from django.shortcuts import render
from django.http import JsonResponse
from django.core.serializers import serialize

from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from categories.models import Category

from .models import Transaction

import json

# Create your views here.
@api_view(['GET', 'POST', 'DELETE', 'PATCH'])
def transaction(request):
    request_body = json.loads(request.body.decode('utf-8'))

    if request.method == 'GET':
        user_transactions = Transaction.objects.filter(user=request.META['user'])
        response_object = json.loads(serialize("json", user_transactions))
        return JsonResponse(response_object, safe=False)

    elif request.method == 'POST':
        category = Category.objects.get(id=request_body['category_id'])

        Transaction.objects.create(
            user=request.META['user'],
            value=request_body['value'],
            category=category,
            date=request_body['date'],
            name=request_body['name']
        )

        return Response(None, status=status.HTTP_201_CREATED)

    elif request.method == 'DELETE':
        transaction_instace = Transaction.objects.get(id=request_body['id'])
        transaction_instace.delete()
        return Response(None, status=status.HTTP_200_OK)

    elif request.method == 'PATCH':
        transaction = Transaction.objects.get(id=request_body['id'])
        transaction.name = request_body['name']
        transaction.value = request_body['value']
        transaction.date = request_body['date']
        transaction.category=Category.objects.get(id=request_body['category_id'])

        transaction.save()

        return Response(None, status=status.HTTP_200_OK)
