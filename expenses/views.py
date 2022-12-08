from collections.abc import Sequence

from datetime import date
from django.shortcuts import render
from django.http import JsonResponse
from django.core.serializers import serialize

from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from categories.models import Category

from .models import Expense
from users.models import User

# Create your views here.


@api_view(['GET', 'POST', 'DELETE', 'PATCH'])
def expense(request):
    request_body = request.META['body']

    try:
        if request.method == 'GET':
            user_expenses = Expense.expenses_from_user(request.META['user'])
            expenses_as_dict = []

            for expense in user_expenses:
                expenses_as_dict.append(expense.as_dict)

            return JsonResponse(expenses_as_dict, safe=False)

        elif request.method == 'POST':
            user_expenses = Expense.expenses_from_user(request.META['user'])
            suma = 0
            for userExpense in user_expenses:
                if userExpense.type == 'income':
                    suma += userExpense.value
                elif userExpense.type == 'expense':
                    suma -= userExpense.value
                elif userExpense.type == 'transfer_send':
                    suma -= userExpense.value
                elif userExpense.type == 'transfer_receive':
                    suma += userExpense.value
            print(suma - int(request_body['value']))
            if (suma - int(request_body['value'])>=0 or request_body['type'] == 'income'):
                
                category = Category.objects.get(id=request_body['category_id'])

                if request_body['type'] == 'transfer_send':
                    userToReceive = User.objects.get(alias=request_body['alias'])
                    income_category = Category.objects.get(id=6)
                    print("HOLAAAAAAAAAA")
                    print(userToReceive)
                    Expense.create_expense_for_user(
                    userToReceive,
                    value=request_body['value'],
                    category=income_category,
                    date=request_body['date'],
                    name="Transferencia recibida",
                    type="transfer_receive"
                    )

                    Expense.create_expense_for_user(
                    request.META['user'],
                    value=request_body['value'],
                    category=category,
                    date=request_body['date'],
                    name="Transferencia enviada",
                    type=request_body['type']
                    )

                else:   
                    Expense.create_expense_for_user(
                        request.META['user'],
                        value=request_body['value'],
                        category=category,
                        date=request_body['date'],
                        name=request_body['name'],
                        type=request_body['type'],
                    )

            return Response(None, status=status.HTTP_201_CREATED)

        elif request.method == 'DELETE':
            expense_instace = Expense.objects.get(id=request_body['id'])

            if expense_instace.user != request.META['user']:
                return Response(None, status=status.HTTP_403_FORBIDDEN)

            expense_instace.delete()
            return Response(None, status=status.HTTP_200_OK)

        elif request.method == 'PATCH':
            all_user_expenses = Expense.expenses_from_user(request.META['user'])
            expense = Expense.objects.get(id=request_body['id'])

            if expense.user != request.META['user']:
                return Response(None, status=status.HTTP_403_FORBIDDEN)
            
            income = 0
            for e in all_user_expenses:
                if e.type == 'income':
                    income += e.value
                elif e.type == 'expense':
                    income -= e.value
                elif e.type == 'transfer_send':
                    income -= e.value
                elif e.type == 'transfer_receive':
                    income += e.value

            if((expense.type == 'income' and (income - int(expense.value) + int(request_body['value']) >= 0)) or (expense.type == 'expense' and (income + int(expense.value) - int(request_body['value']) >= 0))):
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
