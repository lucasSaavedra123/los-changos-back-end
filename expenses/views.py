from collections.abc import Sequence

from datetime import date, datetime
from django.shortcuts import render
from django.http import JsonResponse
from django.core.serializers import serialize

from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from categories.models import Category

from .models import Expense

# Create your views here.


@api_view(['GET', 'POST', 'DELETE', 'PATCH'])
def expense(request):
    request_body = request.META['body']

    try:

        if request.method == 'POST' or request.method == 'PATCH':
            if request_body['name'] is None:
                return Response({'message': "'name' field cannot be null."}, status=status.HTTP_400_BAD_REQUEST)
            if request_body['value'] is None:
                return Response({'message': "'value' field cannot be null."}, status=status.HTTP_400_BAD_REQUEST)
            if request_body['category_id'] is None:
                return Response({'message': "'category_id' field cannot be null."}, status=status.HTTP_400_BAD_REQUEST)
            if request_body['date'] is None:
                return Response({'message': "'date' field cannot be null."}, status=status.HTTP_400_BAD_REQUEST)
            try:
                if datetime.strptime(request_body['date'], '%Y-%m-%d').date() > date.today():
                    return Response({"message": "The date is in the future"}, status=status.HTTP_400_BAD_REQUEST)
            except:
                return Response({"message": "The date should have format YYYY-MM-DD"}, status=status.HTTP_400_BAD_REQUEST)

        if request.method == 'DELETE' or request.method == 'PATCH':
            if request_body['id'] is None:
                return Response({'message': "'id' field cannot be null."}, status=status.HTTP_400_BAD_REQUEST)

        if request.method == 'GET':
            user_expenses = Expense.expenses_from_user(request.META['user'])
            expenses_as_dict = []

            for expense in user_expenses:
                expenses_as_dict.append(expense.as_dict)

            return JsonResponse(expenses_as_dict, safe=False)

        if request.method == 'POST':
            category = Category.objects.get(id=request_body['category_id'])

            Expense.create_expense_for_user(
                request.META['user'],
                value=request_body['value'],
                category=category,
                date=request_body['date'],
                name=request_body['name'],
            )

            return Response(None, status=status.HTTP_201_CREATED)

        try:
            category_instance = Category.objects.get(id=request_body['id'])
        except Category.DoesNotExist:
            return Response({'message': "'id' does not exist"}, status=status.HTTP_400_BAD_REQUEST)

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
            expense.category = Category.objects.get(
                id=request_body['category_id'])

            expense.save()

            return Response(None, status=status.HTTP_200_OK)
    except KeyError as key_error_exception:
        return Response({"message": f"{key_error_exception} was not provided"}, status=status.HTTP_400_BAD_REQUEST)

@api_view(['POST'])
def expense_filter(request):
    request_body = request.META['body']

    try:
        response = []

        if request_body['timeline'] is None:
            return Response({'message': "'timeline' field cannot be null."}, status=status.HTTP_400_BAD_REQUEST)
        try:
            if datetime.strptime(request_body['timeline'][0], '%Y-%m-%d').date() > datetime.strptime(request_body['timeline'][1], '%Y-%m-%d').date():
                return Response({"message": "First date has to be earlier or equal than second one"}, status=status.HTTP_400_BAD_REQUEST)
        except:
            return Response({"message": "Timeline should have the following format [YYYY-MM-DD, YYYY-MM-DD]"}, status=status.HTTP_400_BAD_REQUEST)

        first_date = request_body["timeline"][0].split("-")
        second_date = request_body["timeline"][1].split("-")

        first_date = [int(string_piece) for string_piece in first_date]
        second_date = [int(string_piece) for string_piece in second_date]

        if "category_id" not in request_body or request_body['category_id'] == []:
            expenses = Expense.filter_within_timeline_from_user(
                request.META['user'],
                date(*first_date),
                date(*second_date)
            )

            for expense in expenses:
                response.append(expense.as_dict)
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

                    for expense in expenses:
                        response.append(expense.as_dict)

            else:
                expenses = Expense.filter_by_category_within_timeline_from_user(
                    request.META['user'],
                    date(*first_date),
                    date(*second_date),
                    Category.objects.get(id=request_body['category_id'])
                )

                for expense in expenses:
                    response.append(expense.as_dict)

        return JsonResponse(response, safe=False)

    except KeyError as key_error_exception:
        return Response({"message": f"{key_error_exception} was not provided"}, status=status.HTTP_400_BAD_REQUEST)
