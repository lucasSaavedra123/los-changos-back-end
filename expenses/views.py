from collections.abc import Sequence

from datetime import date
from django.shortcuts import render
from django.http import JsonResponse
from django.core.serializers import serialize

from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from operator import itemgetter

from categories.models import Category

from .models import Expense
from sharedExpenses.models import SharedExpense

# Create your views here.


def inList(expense, lista):
    for element in lista:
        if element.id == expense.id:
            return True
        
    return  False
def orderExpensesByDate(expenses):
    aux=[]
    aux = sorted(expenses, key=itemgetter('date'), reverse=True)
    return aux

@api_view(['GET', 'POST', 'DELETE', 'PATCH'])
def expense(request):
    request_body = request.META['body']

    try:
        if request.method == 'GET':
            
           
            expenses_as_dict = []
            
            y= Expense.expenses_from_user(request.META['user'])

            userSharedExpenses= SharedExpense.expenses_from_user(request.META['user'])

            sharedExpensesFromUser = SharedExpense.expenses_user_made_with_me(request.META['user'])

            
            for expense in sharedExpensesFromUser:
                expenses_as_dict.append(expense.as_dict)

            for expense in userSharedExpenses:
                expenses_as_dict.append(expense.as_dict)

            for expense in y:
                 if not inList(expense, userSharedExpenses):
                     expenses_as_dict.append(expense.as_dict)
            
            expenses_as_dict = orderExpensesByDate(expenses_as_dict)
            
           

            return JsonResponse(expenses_as_dict, safe=False)

        elif request.method == 'POST':
            category = Category.objects.get(id=request_body['category_id'])
            
            Expense.create_expense_for_user(
                request.META['user'],
                value=request_body['value'],
                category=category,
                date=request_body['date'],
                name=request_body['name']
            )

            return Response(None, status=status.HTTP_201_CREATED)

        elif request.method == 'DELETE':
            expense_instace = Expense.objects.get(id=request_body['id'])

            if expense_instace.user != request.META['user']:
                return Response(None, status=status.HTTP_403_FORBIDDEN)

            expense_instace.delete()
            return Response(None, status=status.HTTP_200_OK)

        elif request.method == 'PATCH':
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

        first_date = request_body["timeline"][0].split("-")
        second_date = request_body["timeline"][1].split("-")

        first_date = [int(string_piece) for string_piece in first_date]
        second_date = [int(string_piece) for string_piece in second_date]

        if "category_id" not in request_body or request_body['category_id'] == []:
            aux=[]
            expenses = Expense.filter_within_timeline_from_user(
                request.META['user'],
                date(*first_date),
                date(*second_date)
            )
            sharedExpenses= SharedExpense.filter_within_timeline_from_user(
                request.META['user'],
                date(*first_date),
                date(*second_date)
            )

            userSharedExpenses = SharedExpense.filter_within_timeline_from_otherUser(
                request.META['user'],
                date(*first_date),
                date(*second_date)
            )

            
            for expense in sharedExpenses:
                aux.append(expense.as_dict)
            
            for expense in expenses:
                  if not inList(expense, sharedExpenses):
                     aux.append(expense.as_dict)
            
            for expense in userSharedExpenses:
                aux.append(expense.as_dict)

            response = orderExpensesByDate(aux)
           

        else:
            if isinstance(request_body['category_id'], Sequence):
                expenses = Expense.objects.none()
                sharedExpenses= SharedExpense.objects.none()
                userSharedExpenses = SharedExpense.objects.none()
                aux = []

                for category_id in request_body['category_id']:
                    expenses = Expense.filter_by_category_within_timeline_from_user(
                    request.META['user'],
                    date(*first_date),
                    date(*second_date),
                    Category.objects.get(id=category_id)
                    )
                    sharedExpenses = SharedExpense.filter_by_category_within_timeline_from_user(
                    request.META['user'],
                    date(*first_date),
                    date(*second_date),
                    Category.objects.get(id=category_id)
                    )
                    userSharedExpenses = SharedExpense.filter_by_category_within_timeline_from_otherUser(
                    request.META['user'],
                    date(*first_date),
                    date(*second_date),
                    Category.objects.get(id=category_id)
                    )

                  
                    for expense in sharedExpenses:
                        aux.append(expense.as_dict)

                    for expense in expenses:
                         if not inList(expense, sharedExpenses):
                             aux.append(expense.as_dict)
                    
                    for expense in userSharedExpenses:
                        aux.append(expense.as_dict)
                    
                   
                    response = orderExpensesByDate(aux)
                    
                    
         
           
            else:
                aux = []
                expenses = Expense.filter_by_category_within_timeline_from_user(
                    request.META['user'],
                    date(*first_date),
                    date(*second_date),
                    Category.objects.get(id=request_body['category_id'])
                )
                sharedExpenses= SharedExpense.filter_by_category_within_timeline_from_user(
                    request.META['user'],
                    date(*first_date),
                    date(*second_date),
                    Category.objects.get(id=request_body['category_id'])
                )
                userSharedExpenses = SharedExpense.filter_by_category_within_timeline_from_otherUser(
                    request.META['user'],
                    date(*first_date),
                    date(*second_date),
                    Category.objects.get(id=request_body['category_id'])
                )

                
                for expense in sharedExpenses:
                    aux.append(expense.as_dict)
            
                for expense in expenses:
                     if not inList(expense, sharedExpenses):
                         aux.append(expense.as_dict)

                for expense in userSharedExpenses:
                    aux.append(expense.as_dict)
                

                print("Antes de orderna")
                print(JsonResponse(response, safe=False))
                
                response = orderExpensesByDate(aux)
                    
                print("Depois de orderna")
                print(JsonResponse(response, safe=False))
         
                
              
                

        return JsonResponse(response, safe=False)

    except KeyError as key_error_exception:
        return Response({"message": f"{key_error_exception} was not provided"}, status=status.HTTP_400_BAD_REQUEST)
