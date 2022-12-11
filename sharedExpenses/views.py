from collections.abc import Sequence

from datetime import date
from django.shortcuts import render
from django.http import JsonResponse
from django.core.serializers import serialize

from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from categories.models import Category
from users.models import User

from .models import SharedExpense


# Create your views here.

def validateAlias(alias):
    try:
        user = User.objects.get(alias=alias)
        return True
    except:
        return False


@api_view(['GET', 'POST', 'DELETE', 'PATCH'])
def sharedExpense(request):
    request_body = request.META['body']

    try:
        if request.method == 'GET':
            user_expenses = SharedExpense.expenses_from_user(request.META['user'])
            expenses_as_dict = []

            for expense in user_expenses:
                expenses_as_dict.append(expense.as_dict)

            return JsonResponse(expenses_as_dict, safe=False)

        elif request.method == 'POST':
            category = Category.objects.get(id=request_body['category_id'])

            

            if not validateAlias(request_body['userToShare']):

                return Response({"message": "Alias not found"}, status=status.HTTP_400_BAD_REQUEST)

            
            SharedExpense.create_expense_for_user(
                request.META['user'],
                value=request_body['value'],
                category=category,
                date=request_body['date'],
                name=request_body['name'],
                userToShare= User.objects.get(alias=request_body['userToShare']),
                
            )

            return Response(None, status=status.HTTP_201_CREATED)

        elif request.method == 'DELETE':
            expense_instace = SharedExpense.objects.get(id=request_body['id'])

            if expense_instace.userToShare != request.META['user']:
                return Response(None, status=status.HTTP_403_FORBIDDEN)

            expense_instace.delete()
            return Response(None, status=status.HTTP_200_OK)

        elif request.method == 'PATCH':
            expense = SharedExpense.objects.get(id=request_body['id'])

            if expense.userToShare != request.META['user']:
                return Response(None, status=status.HTTP_403_FORBIDDEN)

            expense.name = request_body['name']
            expense.value = request_body['value']
            expense.date = request_body['date']
            expense.category = Category.objects.get(
                id=request_body['category_id'])
            expense.userToShare = User.objects.get(alias=request_body['userToShare'])
            expense.aceptedTransaction = request_body['aceptedTransaction']
            expense.save()

            return Response(None, status=status.HTTP_200_OK)
    except KeyError as key_error_exception:
        return Response({"message": f"{key_error_exception} was not provided"}, status=status.HTTP_400_BAD_REQUEST)

@api_view(['PATCH'])
def editSharedExpense(request):
    request_body = request.META['body']

    try:
        if request.method == 'PATCH':
            print(request_body)
            expense = SharedExpense.objects.get(id=request_body['id'])
            print(expense)
            print(request.META['user'])

            if expense.userToShare != request.META['user']:
                return Response(None, status=status.HTTP_403_FORBIDDEN)

            expense.aceptedTransaction = request_body['aceptedTransaction']
            expense.save()

            return Response(None, status=status.HTTP_200_OK)
    except KeyError as key_error_exception:
        return Response({"message": f"{key_error_exception} was not provided"}, status=status.HTTP_400_BAD_REQUEST)

@api_view(['GET'])
def getPendingSharedExpensesCreatedToMe(request):
    try:
        if request.method == 'GET':
            user_expenses = SharedExpense.get_expenses_pending_to_accept(request.META['user'])
            expenses_as_dict = []

            for expense in user_expenses:
                expenses_as_dict.append(expense.as_dict)

            return JsonResponse(expenses_as_dict, safe=False)

    except KeyError as key_error_exception:
        return Response({"message": f"{key_error_exception} was not provided"}, status=status.HTTP_400_BAD_REQUEST)

# @api_view(['GET'])
# def getPendingSharedExpensesCreatedByMe(request):
#     try:
#         if request.method == 'GET':
#             user_expenses = SharedExpense.get_expenses_created_by_user_pending_to_accept(request.META['user'])
#             expenses_as_dict = []

#             for expense in user_expenses:
#                 expenses_as_dict.append(expense.as_dict)

#             return JsonResponse(expenses_as_dict, safe=False)
#     except KeyError as key_error_exception:
#         return Response({"message": f"{key_error_exception} was not provided"}, status=status.HTTP_400_BAD_REQUEST)
