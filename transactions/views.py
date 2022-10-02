from django.shortcuts import render
from django.http import JsonResponse
from django.core.serializers import serialize

from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status

from users.models import User
from .models import Transaction

# Create your views here.
@api_view(['GET', 'POST', 'DELETE'])
def transaction(request):

    if request.method == 'GET':
        user_transactions = Transaction.objects.filter(user=request.META['user'])
        response_object = {"transactions":serialize("json", user_transactions)}
        return JsonResponse(response_object)

    elif request.method == 'POST':
        Transaction.objects.create(
            user=request.META['user'],
            value=request.POST['value'],
            date=request.POST['date']
        )

        return Response(None, status=status.HTTP_201_CREATED)

    """
    elif request.method == 'DELETE':
        Transaction.objects.create(
            user=request.META['transaction_id'],
            value=request.POST['value'],
            date=request.POST['date']
        )

        return Response(None, status=status.HTTP_200_OK)
    """