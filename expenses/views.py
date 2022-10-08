from django.shortcuts import render
from django.http import JsonResponse
from django.core.serializers import serialize

from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from categories.models import Category

from .models import Expense

import json

# Create your views here.
@api_view(['GET', 'POST', 'DELETE', 'PATCH'])
def expense(request):
    request_body = request.META['body']

    try:
        if request.method == 'GET':
            user_expenses = Expense.objects.filter(user=request.META['user'])

            expenses_as_dict = []
            
            for expense in user_expenses:
                expenses_as_dict.append(expense.as_dict)

            return JsonResponse(expenses_as_dict, safe=False)

        elif request.method == 'POST':
            category = Category.objects.get(id=request_body['category_id'])

            Expense.objects.create(
                user=request.META['user'],
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
            expense.category=Category.objects.get(id=request_body['category_id'])

            expense.save()

            return Response(None, status=status.HTTP_200_OK)
    except KeyError as key_error_exception:
        return Response({"message": f"{key_error_exception} was not provided"}, status=status.HTTP_400_BAD_REQUEST)
