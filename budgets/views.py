from urllib import response
from django.shortcuts import render
from django.http import JsonResponse

from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status, serializers

from datetime import datetime

from expenses.models import Expense
from budgets.models import Budget, Detail, FutureExpenseDetail, LimitDetail
from categories.models import Category
from django.core.exceptions import ValidationError

from drf_yasg.utils import swagger_auto_schema


def create_details(details, budget):
    limit_dictionary = {}
    value_dictionary = {}

    if len(details) == 0:
        raise Exception("Empty budgets cannot be created")

    limit_details = [detail for detail in details if 'limit' in detail and detail != 0 ]

    if len(limit_details) == 0:
        raise Exception("A limit detail should be included")

    for detail in details:
        if 'limit' not in detail and 'value' not in detail:
            raise Exception("Missing limit or value in detail")

    for detail in details:
        if 'limit' in detail:
            if detail['limit'] > 0:
                if detail['category_id'] in limit_dictionary:
                    raise Exception(f"Category {detail['category_id']} cannot have more than one limit")
                else:
                    limit_dictionary[detail['category_id']] = detail['limit']

                budget.add_limit(Category.objects.get(id=detail['category_id']), detail['limit'])
            elif detail['limit'] == 0:
                pass
            else:
                raise Exception(f"Limit cannot be less than 0")

    for detail in details:
        if 'value' in detail:
            if detail['value'] > 0:
                if detail['category_id'] in value_dictionary:
                    value_dictionary[detail['category_id']] += detail['value']
                else:
                    value_dictionary[detail['category_id']] = detail['value']

                budget.add_future_expense(Category.objects.get(id=detail['category_id']), detail['value'], detail['name'], detail['expiration_date'])
            else:
                raise Exception(f"Value cannot be less than 0")

    for value_id in value_dictionary:
        if value_dictionary[value_id] > limit_dictionary[value_id]:
            raise Exception(f"Category {value_id} has future expenses greater than its limit")

# Create your views here.
def exist_budget_validation(budget_id):
    try:
        Budget.objects.get(id=budget_id)
    except Budget.DoesNotExist:
        raise serializers.ValidationError(f"Budget {budget_id} doesn't exist")

class PostBudgetSerializer(serializers.ModelSerializer):
    class Meta:
        model = Budget
        fields = ['initial_date', 'final_date']

    initial_date = serializers.DateField(required=True)
    final_date = serializers.DateField(required=True)

class PatchBudgetSerializer(serializers.ModelSerializer):
    class Meta:
        model = Budget
        fields = ['id', 'initial_date', 'final_date']

    initial_date = serializers.DateField(required=True)
    final_date = serializers.DateField(required=True)
    id = serializers.IntegerField(required=True, validators=[exist_budget_validation])

class DeleteBudgetSerializer(serializers.ModelSerializer):
    class Meta:
        model = Budget
        fields = ['id']

    id = serializers.IntegerField(required=True, validators=[exist_budget_validation])

class GetBudgetSerializer(serializers.ModelSerializer):
    class Meta:
        model = Budget
        fields = []

@swagger_auto_schema(method='post', request_body=PostBudgetSerializer)
@swagger_auto_schema(method='patch', request_body=PatchBudgetSerializer)
@swagger_auto_schema(method='delete', request_body=DeleteBudgetSerializer)
@api_view(['GET', 'POST', 'PATCH', 'DELETE'])
def budget(request):
    request_body = request.META['body']

    serializers = {
        'POST': PostBudgetSerializer(data=request_body),
        'PATCH': PatchBudgetSerializer(data=request_body),
        'GET': GetBudgetSerializer(data=request_body),
        'DELETE': DeleteBudgetSerializer(data=request_body),
    }

    serializer = serializers[request.method]

    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    #The following validations cannot be included in Django's serializers
    if request.method == 'POST' or request.method == 'PATCH':
        if datetime.strptime(request_body['initial_date'], '%Y-%m-%d') > datetime.strptime(request_body['final_date'], '%Y-%m-%d'):
            return Response({"message": f"Initial date cannot be greater than final date"}, status=status.HTTP_400_BAD_REQUEST)

    if request.method == 'GET':
        user_budgets = Budget.all_from_user(request.META['user'])
        budgets_as_dict = [budget.as_dict for budget in user_budgets]
        all_categories_from_user = Category.categories_from_user(request.META['user'])

        # Front-End requires all limits with each category, even if it's 0
        for budget_index in range(len(budgets_as_dict)):
            if len(budgets_as_dict[budget_index]['details']) == 0:
                user_budgets[budget_index].delete()
                budgets_as_dict[budget_index] = {}
            else:
                categories_that_have_limit_budgets = [ detail['category']['id'] for detail in budgets_as_dict[budget_index]['details'] if detail.get('limit', None) is not None ]
                budgets_as_dict[budget_index]['details'] += [{ 'category': user_category.as_dict, 'limit': 0, 'spent': 0 } for user_category in all_categories_from_user if user_category.id not in categories_that_have_limit_budgets]

        budgets_as_dict = [budget for budget in budgets_as_dict if budget != {}]

        return JsonResponse(budgets_as_dict, safe=False)

    elif request.method == 'POST':
        new_budget = Budget.objects.create(
            user=request.META['user'],
            initial_date=request_body['initial_date'],
            final_date=request_body['final_date']
        )

        try:
            create_details(request_body['details'], new_budget)
        except Exception as e:
            new_budget.delete()
            return Response({"message": f"{e}"}, status=status.HTTP_400_BAD_REQUEST)

        return Response(None, status=status.HTTP_201_CREATED)

    budget = Budget.objects.get(id=request_body['id'])

    if request.method == 'DELETE':
        budget = Budget.objects.get(id=request_body['id'])

        if budget.user != request.META['user']:
            return Response(None, status=status.HTTP_403_FORBIDDEN)

        if not budget.active:
            budget.delete()
        else:
            return Response({"message": f"Current budgets are neither editable and removable"}, status=status.HTTP_400_BAD_REQUEST)

        return Response(None, status=status.HTTP_200_OK)

    if request.method == 'PATCH':
        budget = Budget.objects.get(id=request_body['id'])

        if budget.user != request.META['user']:
            return Response(None, status=status.HTTP_403_FORBIDDEN)

        if budget.active:
            return Response({"message": f"Current budgets are neither editable and removable"}, status=status.HTTP_400_BAD_REQUEST)
        else:
            budget.initial_date = datetime.strptime(request_body['initial_date'], '%Y-%m-%d').date()
            budget.final_date = datetime.strptime(request_body['final_date'], '%Y-%m-%d').date()
            current_details = LimitDetail.from_budget(budget)

            for detail in current_details:
                detail.delete()
            try:
                create_details(request_body['details'], budget)
            except Exception as e:
                #If something failed, we recover the previous state
                for detail in Detail.from_budget(budget):
                    detail.delete()

                for detail in current_details:
                    detail.save()
                return Response({"message": f"{e}"}, status=status.HTTP_400_BAD_REQUEST)

            budget.save(update=True)

        return Response(None, status=status.HTTP_200_OK)


@api_view(['GET'])
def current_budget(request):
    if request.method == 'GET':
        current_user_budget = Budget.current_budget_of(request.META['user'])

        if current_user_budget is None:
            return JsonResponse({}, safe=False)
        else:
            if len(current_user_budget.as_dict['details']) == 0:
                current_user_budget.delete()
                return JsonResponse({}, safe=False)
            else:
                return JsonResponse(current_user_budget.as_dict, safe=False)

class MakeFutureExpenseSerializer(serializers.ModelSerializer):
    class Meta:
        model = Budget
        fields = ['future_expense_id', 'expense_done_date']

    future_expense_id = serializers.IntegerField(required=True)
    expense_done_date = serializers.DateField(required=True)

@swagger_auto_schema(method='patch', request_body=MakeFutureExpenseSerializer)
@api_view(['PATCH'])
def make_future_expense(request):
    
    serializer = MakeFutureExpenseSerializer(data=request.META['body'])

    if request.method == 'PATCH':
        current_user_budget = Budget.current_budget_of(request.META['user'])

        if current_user_budget is None:
            return JsonResponse({"message": f"User has no current budget"}, safe=False, status=status.HTTP_400_BAD_REQUEST)
        else:
            for detail in Detail.from_budget(current_user_budget):
                if detail.id == request.META['body']['future_expense_id'] and detail.__class__ == FutureExpenseDetail:
                    detail.expended = True
                    detail.save()

                    Expense.create_expense_for_user(
                        request.META['user'],
                        value=detail.value,
                        category=detail.category,
                        date=request.META['body']['expense_done_date'],
                        name=detail.name,
                        future_expense=True
                    )

                    return JsonResponse({"message": f"Future Expense created"}, safe=False)

            return JsonResponse({"message": f"Future Expense with ID {request.META['body']['future_expense_id']} does not exist"}, safe=False, status=status.HTTP_400_BAD_REQUEST)
