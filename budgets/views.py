from urllib import response
from django.shortcuts import render
from django.http import JsonResponse

from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status

from budgets.models import Budget, Detail
from categories.models import Category

# Create your views here.
@api_view(['GET', 'POST', 'PATCH', 'DELETE'])
def budget(request):
    request_body = request.META['body']

    try:
        if request.method == 'GET':
            user_budgets = Budget.all_from_user(request.META['user'])

            budgets_as_dict = []

            for budget in user_budgets:
                budgets_as_dict.append(budget.as_dict)

            all_categories_from_user = Category.categories_from_user(request.META['user'])

            #Front-End requires all limits with each category
            #There should be an improvement for this. At the end, improvements will be done
            for budget_index in range(len(budgets_as_dict)):
                categories_that_have_limit_budgets = []

                for detail in budgets_as_dict[budget_index]['details']:
                    if detail.get('limit', None) is not None:
                        categories_that_have_limit_budgets.append(detail['category']['id'])

                for user_category in all_categories_from_user:
                    if user_category.id not in categories_that_have_limit_budgets:
                        budgets_as_dict[budget_index]['details'].append({
                            'category': user_category.as_dict,
                            'limit':0,
                            'spent': 0
                        })

            return JsonResponse(budgets_as_dict, safe=False)

        elif request.method == 'POST':
            Budget.force = True
            new_budget = Budget.objects.create(
                user=request.META['user'],
                initial_date=request_body['initial_date'],
                final_date=request_body['final_date']
            )

            for detail in request_body['details']:
                if 'limit' in detail and detail['limit'] > 0:
                    new_budget.add_limit(Category.objects.get(id=detail['category_id']), detail['limit'])
                elif 'value' in detail and detail['value'] > 0:
                    new_budget.add_future_expense(Category.objects.get(id=detail['category_id']), detail['value'], detail['name'], detail['expiration_date'])
                else:
                    return Response({"message": f"Request should include in details field limit and value for limit or future expense detail respectively"}, status=status.HTTP_400_BAD_REQUEST)

            return Response(None, status=status.HTTP_201_CREATED)

        elif request.method == 'DELETE':
            budget_instance = Budget.objects.get(id=request_body['id'])

            if budget_instance.user != request.META['user']:
                return Response(None, status=status.HTTP_403_FORBIDDEN)

            if not budget_instance.active:
                budget_instance.delete()
            else:
                return Response({"message": f"Current budgets are neither editable and removable"}, status=status.HTTP_400_BAD_REQUEST)

            return Response(None, status=status.HTTP_200_OK)

        elif request.method == 'PATCH':
            budget = Budget.objects.get(id=request_body['id'])

            if budget.user != request.META['user']:
                return Response(None, status=status.HTTP_403_FORBIDDEN)

            if budget.active:
                return Response({"message": f"Current budgets are neither editable and removable"}, status=status.HTTP_400_BAD_REQUEST)
            else:
                budget.initial_date = request_body['initial_date']
                budget.final_date = request_body['final_date']

                #Esto hay que revisarlo. Osea, si falla algo abajo, se borraron todos los detalles sin querer!!!
                for detail in Detail.from_budget(budget):
                    detail.delete()

                for detail in request_body['details']:
                    if 'limit' in detail:
                        if detail['limit'] > 0:
                            budget.add_limit(Category.objects.get(id=detail['category_id']), detail['limit'])
                    elif 'value' in detail:
                        if detail['value'] > 0:
                            budget.add_future_expense(Category.objects.get(id=detail['category_id']), detail['value'], detail['name'], detail['expiration_date'])
                    else:
                        return Response({"message": f"Request should include in details field limit and value for limit or future expense detail respectively"}, status=status.HTTP_400_BAD_REQUEST)

                budget.save(update=True)

            return Response(None, status=status.HTTP_200_OK)
    except KeyError as key_error_exception:
        return Response({"message": f"{key_error_exception} was not provided"}, status=status.HTTP_400_BAD_REQUEST)

# Create your views here.
@api_view(['GET'])
def current_budget(request):
    if request.method == 'GET':
        current_user_budget = Budget.current_budget_of(request.META['user'])

        if current_user_budget is None:
            return JsonResponse({}, safe=False)
        else:
            return JsonResponse(current_user_budget.as_dict, safe=False)
