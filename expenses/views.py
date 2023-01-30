from collections.abc import Sequence

from datetime import date, datetime
from django.shortcuts import render
from django.http import JsonResponse
from django.core.serializers import serialize

from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status, serializers
from categories.models import Category

from .models import Expense


def is_on_the_future_validation(new_date):
    try:
        if new_date > date.today():
            raise serializers.ValidationError('Future dates are not accepted')
    except Exception as e:
        raise serializers.ValidationError('Date format should be YYYY-MM-DD')

def exist_expense_validation(expense_id):
    try:
        Expense.objects.get(id=expense_id)
    except Expense.DoesNotExist as e:
        raise serializers.ValidationError(f"Expense {expense_id} doesn't exist")

def exist_category_validation(category_id):
    try:
        Category.objects.get(id=category_id)
    except Category.DoesNotExist:
        raise serializers.ValidationError(f"Category {category_id} doesn't exist")

class PostOrPatchExpenseSerializer(serializers.ModelSerializer):
    class Meta:
        model = Expense
        fields = ['name', 'value', 'category_id', 'date']

    name = serializers.CharField(required=True)
    value = serializers.FloatField(required=True)
    category_id = serializers.IntegerField(required=True, validators=[exist_category_validation])
    date = serializers.DateField(validators=[is_on_the_future_validation], required=True)

class PatchOrDeleteExpenseSerializer(serializers.ModelSerializer):
    class Meta:
        model = Expense
        fields = ['id', 'name', 'value', 'category_id', 'date']

    name = serializers.CharField(required=False)
    value = serializers.FloatField(required=False)
    category_id = serializers.IntegerField(required=False, validators=[exist_category_validation])
    date = serializers.DateField(required=False, validators=[is_on_the_future_validation])
    id = serializers.IntegerField(required=True, validators=[exist_expense_validation])

class GetExpenseSerializer(serializers.ModelSerializer):
    class Meta:
        model = Expense
        fields = []

# Create your views here.
@api_view(['GET', 'POST', 'DELETE', 'PATCH'])
def expense(request):
    request_body = request.META['body']

    serializers = {
        'POST': [PostOrPatchExpenseSerializer(data=request_body)],
        'PATCH': [PatchOrDeleteExpenseSerializer(data=request_body), PostOrPatchExpenseSerializer(data=request_body)],
        'GET': [GetExpenseSerializer(data=request_body)],
        'DELETE': [PatchOrDeleteExpenseSerializer(data=request_body)],
    }

    for serializer in serializers[request.method]:
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    if request.method == 'GET':
        user_expenses = Expense.expenses_from_user(request.META['user'])
        expenses_as_dict = [expense.as_dict for expense in user_expenses]
        return JsonResponse(expenses_as_dict, safe=False)

    if request.method == 'POST':
        Expense.create_expense_for_user(
            request.META['user'],
            value=request_body['value'],
            category=Category.objects.get(id=request_body['category_id']),
            date=request_body['date'],
            name=request_body['name'],
        )

        return Response(None, status=status.HTTP_201_CREATED)

    if request.method == 'DELETE':
        expense_instace = Expense.objects.get(id=request_body['id'])

        if expense_instace.user != request.META['user']:
            return Response(None, status=status.HTTP_403_FORBIDDEN)

        expense_instace.delete()
        return Response(None, status=status.HTTP_200_OK)

    if request.method == 'PATCH':
        expense = Expense.objects.get(id=request_body['id'])

        if expense.user != request.META['user']:
            return Response(None, status=status.HTTP_403_FORBIDDEN)

        expense.name = request_body['name']
        expense.value = request_body['value']
        expense.date = request_body['date']
        expense.category = Category.objects.get(id=request_body['category_id'])

        expense.save()

        return Response(None, status=status.HTTP_200_OK)

def is_on_the_future_validation(date_list):
    try:
        if date_list[0] > date_list[1]:
            raise serializers.ValidationError("First date has to be earlier or equal than second one")
    except:
        raise serializers.ValidationError("Timeline should have the following format [YYYY-MM-DD, YYYY-MM-DD]")

class PostFilterExpenseSerializer(serializers.ModelSerializer):
    class Meta:
        model = Expense
        fields = ['timeline']

    timeline = serializers.ListField(required=True, child=serializers.DateField(), validators=[is_on_the_future_validation])


@api_view(['POST'])
def expense_filter(request):
    request_body = request.META['body']

    serializer = PostFilterExpenseSerializer(data=request_body)

    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    response = []
    first_date = [int(string_piece) for string_piece in request_body["timeline"][0].split("-")]
    second_date = [int(string_piece) for string_piece in request_body["timeline"][1].split("-")]

    if request_body.get('category_id', None) is None or request_body['category_id'] == []:
        expenses = Expense.filter_within_timeline_from_user(
            request.META['user'],
            date(*first_date),
            date(*second_date)
        )

        response = [expense.as_dict for expense in expenses]
    else:
        if isinstance(request_body['category_id'], Sequence):
            expenses = Expense.objects.none()

            for category_id in request_body['category_id']:
                expenses = Expense.filter_by_category_within_timeline_from_user(
                request.META['user'],
                date(*first_date),
                date(*second_date),
                Category.objects.get(id=category_id)
                )

                response += [expense.as_dict for expense in expenses]

        else:
            expenses = Expense.filter_by_category_within_timeline_from_user(
                request.META['user'],
                date(*first_date),
                date(*second_date),
                Category.objects.get(id=request_body['category_id'])
            )

            response = [expense.as_dict for expense in expenses]

    return JsonResponse(response, safe=False)
