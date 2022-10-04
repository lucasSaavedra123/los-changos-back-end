from urllib import response
from django.shortcuts import render
from django.http import JsonResponse
from django.core.serializers import serialize
from django.forms.models import model_to_dict

from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status

import json

from categories.models import Category


# Create your views here.
@api_view(['GET', 'POST', 'PATCH'])
def category(request):
    request_body = request.META['body']

    if request.method == 'GET':
        static_categories = Category.objects.filter(user=None)
        user_categories = Category.objects.filter(user=request.META['user'])
        all_categories = static_categories.union(user_categories)
        
        categories_as_dict = []
        
        for category in all_categories:
            categories_as_dict.append(category.as_dict)

        return JsonResponse(categories_as_dict, safe=False)

    elif request.method == 'POST':
        Category.objects.create(
            user=request.META['user'],
            material_ui_icon_name=request_body['material_ui_icon_name'],
            name=request_body['name']
        )

        return Response(None, status=status.HTTP_201_CREATED)

    elif request.method == 'PATCH':
        category = Category.objects.get(id=request_body['id'])
        
        if category.static:
            return Response(None, status=status.HTTP_403_FORBIDDEN)
        
        category.name = request_body['name']
        category.material_ui_icon_name = request_body['material_ui_icon_name']
        category.save()

        return Response(None, status=status.HTTP_200_OK)

    elif request.method == 'DELETE':
        category_instance = Category.objects.get(id=request_body['id'])
  
        if category_instance.static:
            return Response(None, status=status.HTTP_403_FORBIDDEN)
    
        category_instance.delete()
        return Response(None, status=status.HTTP_200_OK)
