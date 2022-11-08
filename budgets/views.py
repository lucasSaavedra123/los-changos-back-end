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

            return JsonResponse(budgets_as_dict, safe=False)

        elif request.method == 'POST':
            new_budget = Budget.objects.create(
                user=request.META['user'],
                initial_date=request_body['initial_date'],
                final_date=request_body['final_date']
            )

            for detail in request_body['details']:
                new_budget.add_detail(Category.objects.get(id=detail['category_id']), detail['limit'])

            return Response(None, status=status.HTTP_201_CREATED)

        elif request.method == 'DELETE':
            budget_instance = Budget.objects.get(id=request_body['id'])

            if budget_instance.user != request.META['user']:
                return Response(None, status=status.HTTP_403_FORBIDDEN)

            budget_instance.delete()
            return Response(None, status=status.HTTP_200_OK)

        elif request.method == 'PATCH':
            budget = Budget.objects.get(id=request_body['id'])

            if budget.user != request.META['user']:
                return Response(None, status=status.HTTP_403_FORBIDDEN)

            budget.initial_date = request_body['initial_date']
            budget.final_date = request_body['final_date']

            for detail in Detail.objects.filter(assigned_budget=budget):
                detail.delete()

            for detail in request_body['details']:
                budget.add_detail(Category.objects.get(id=detail['category_id']), detail['limit'])

            budget.save(update=True)

            return Response(None, status=status.HTTP_200_OK)


    except KeyError as key_error_exception:
        return Response({"message": f"{key_error_exception} was not provided"}, status=status.HTTP_400_BAD_REQUEST)
    except Exception as e:
        print(e)

    """
    try:

        if request.method == 'GET':
            user_categories = Category.categories_from_user(request.META['user'])

            categories_as_dict = []

            for category in user_categories:
                categories_as_dict.append(category.as_dict)

            return JsonResponse(categories_as_dict, safe=False)

        elif request.method == 'POST':
            Category.create_category_for_user(
                request.META['user'],
                material_ui_icon_name=request_body['material_ui_icon_name'],
                name=request_body['name']
            )

            return Response(None, status=status.HTTP_201_CREATED)

        category_instance = Category.objects.get(id=request_body['id'])

        if category_instance.static or category_instance.user != request.META['user']:
            return Response(None, status=status.HTTP_403_FORBIDDEN)

        if request.method == 'PATCH':
            category = Category.objects.get(id=request_body['id'])
            category.name = request_body['name']
            category.material_ui_icon_name = request_body['material_ui_icon_name']
            category.save(update=True)

            return Response(None, status=status.HTTP_200_OK)

        elif request.method == 'DELETE':
            category_instance = Category.objects.get(id=request_body['id'])
            category_instance.delete()
            return Response(None, status=status.HTTP_200_OK)

    except KeyError as key_error_exception:
        return Response({"message": f"{key_error_exception} was not provided"}, status=status.HTTP_400_BAD_REQUEST)
    """