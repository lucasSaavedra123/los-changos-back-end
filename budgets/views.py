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

# Create your views here.
def exist_budget_validation(budget_id):
    try:
        Budget.objects.get(id=budget_id)
    except Budget.DoesNotExist:
        raise serializers.ValidationError(f"Budget {budget_id} doesn't exist")

class PostOrPatchBudgetSerializer(serializers.ModelSerializer):
    class Meta:
        model = Budget
        fields = ['initial_date', 'final_date']

    initial_date = serializers.DateField(required=True)
    final_date = serializers.DateField(required=True)

class PatchOrDeleteBudgetSerializer(serializers.ModelSerializer):
    class Meta:
        model = Budget
        fields = ['id', 'initial_date', 'final_date']

    initial_date = serializers.DateField(required=False)
    final_date = serializers.DateField(required=False)
    id = serializers.IntegerField(required=True, validators=[exist_budget_validation])

class GetBudgetSerializer(serializers.ModelSerializer):
    class Meta:
        model = Budget
        fields = []

@api_view(['GET', 'POST', 'PATCH', 'DELETE'])
def budget(request):
    request_body = request.META['body']

    serializers = {
        'POST': [PostOrPatchBudgetSerializer(data=request_body)],
        'PATCH': [PatchOrDeleteBudgetSerializer(data=request_body), PostOrPatchBudgetSerializer(data=request_body)],
        'GET': [GetBudgetSerializer(data=request_body)],
        'DELETE': [PatchOrDeleteBudgetSerializer(data=request_body)],
    }

    for serializer in serializers[request.method]:
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    #The following validations cannot be included in Django's serializers
    if request.method == 'POST' or request.method == 'PATCH':
        if datetime.strptime(request_body['initial_date'], '%Y-%d-%m') > datetime.strptime(request_body['final_date'], '%Y-%d-%m'):
            return Response({"message": f"Initial date cannot be greater than final date"}, status=status.HTTP_400_BAD_REQUEST)
        
    try:
        if request.method == 'GET':
            user_budgets = Budget.all_from_user(request.META['user'])
            budgets_as_dict = [budget.as_dict for budget in user_budgets]
            all_categories_from_user = Category.categories_from_user(request.META['user'])

            # Front-End requires all limits with each category, even if it's 0
            for budget_index in range(len(budgets_as_dict)):
                categories_that_have_limit_budgets = [ detail['category']['id'] for detail in budgets_as_dict[budget_index]['details'] if detail.get('limit', None) is not None ]
                budgets_as_dict[budget_index]['details'] += [{ 'category': user_category.as_dict, 'limit': 0, 'spent': 0 } for user_category in all_categories_from_user if user_category.id not in categories_that_have_limit_budgets]

            return JsonResponse(budgets_as_dict, safe=False)

        elif request.method == 'POST':
            new_budget = Budget.objects.create(
                user=request.META['user'],
                initial_date=request_body['initial_date'],
                final_date=request_body['final_date']
            )

            try:
                for detail in request_body['details']:
                    if 'limit' in detail:
                        if detail['limit'] > 0:
                            new_budget.add_limit(Category.objects.get(id=detail['category_id']), detail['limit'])
                    elif 'value' in detail:
                        if detail['value'] > 0:
                            new_budget.add_future_expense(Category.objects.get(id=detail['category_id']), detail['value'], detail['name'], detail['expiration_date'])                        
                    else:
                        new_budget.delete()
                        return Response({"message": f"Request should include in details field limit and value for limit or future expense detail respectively"}, status=status.HTTP_400_BAD_REQUEST)
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
                current_details = LimitDetail.from_budget(budget)

                for detail in current_details:
                    detail.delete()

                try:
                    for detail in request_body['details']:
                        if 'limit' in detail:
                            if detail['limit'] > 0:
                                budget.add_limit(Category.objects.get(
                                    id=detail['category_id']), detail['limit'])
                        elif 'value' in detail:
                            if detail['value'] > 0:
                                budget.add_future_expense(Category.objects.get(id=detail['category_id']), detail['value'], detail['name'], detail['expiration_date'])
                        else:
                            return Response({"message": f"Request should include in details field limit and value for limit or future expense detail respectively"}, status=status.HTTP_400_BAD_REQUEST)
                except Exception as e:
                    #If something failed, we recover the previous state
                    for detail in current_details:
                        detail.save()
                    return Response({"message": f"{e}"}, status=status.HTTP_400_BAD_REQUEST)

                budget.initial_date = request_body['initial_date']
                budget.final_date = request_body['final_date']
                budget.save(update=True)

            return Response(None, status=status.HTTP_200_OK)
    except KeyError as key_error_exception:
        return Response({"message": f"{key_error_exception} was not provided"}, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET'])
def current_budget(request):
    if request.method == 'GET':
        current_user_budget = Budget.current_budget_of(request.META['user'])

        if current_user_budget is None:
            return JsonResponse({}, safe=False)
        else:
            return JsonResponse(current_user_budget.as_dict, safe=False)


@api_view(['PATCH'])
def make_future_expense(request):
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
