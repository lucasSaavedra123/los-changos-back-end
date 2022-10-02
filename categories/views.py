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
@api_view(['GET', 'POST', 'DELETE'])
def category(request):

    if request.method == 'GET':
        static_categories = Category.objects.filter(user=None)
        user_categories = Category.objects.filter(user=request.META['user'])
        all_categories = static_categories.union(user_categories)
        response_object = json.loads(serialize("json", all_categories))
        return JsonResponse(response_object, safe=False)
