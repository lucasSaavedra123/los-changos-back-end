from collections.abc import Sequence

from datetime import date
from django.shortcuts import render
from django.http import JsonResponse
from django.core.serializers import serialize

from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from categories.models import Category

from .models import User
@api_view(['GET'])
def user(request):


    try:
        if request.method == 'GET':
            users = User.objects.all()
            userWithAlias = []
            
            for user in users:
                userWithAlias.append(user.alias)
                

            return JsonResponse(userWithAlias, safe=False)
    
    except KeyError as key_error_exception:
        return Response({"message": f"{key_error_exception} was not provided"}, status=status.HTTP_400_BAD_REQUEST)

   