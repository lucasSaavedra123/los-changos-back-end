from urllib import response
from django.shortcuts import render
from django.http import JsonResponse

from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status, serializers

from categories.models import Category

from drf_yasg.utils import swagger_auto_schema

def exist_category_validation(category_id):
    try:
        Category.objects.get(id=category_id)
    except Category.DoesNotExist:
        raise serializers.ValidationError(f"Category {category_id} doesn't exist")

class PostOrPatchCategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ['name', 'material_ui_icon_name']

    material_ui_icon_name = serializers.CharField(required=True)
    name = serializers.CharField(required=True)

class PatchOrDeleteCategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ['id', 'name', 'material_ui_icon_name']

    material_ui_icon_name = serializers.CharField(required=False)
    name = serializers.CharField(required=False)
    id = serializers.IntegerField(required=True, validators=[exist_category_validation])

class GetCategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = []

# Create your views here.
@swagger_auto_schema(method='post', request_body=PostOrPatchCategorySerializer)
@swagger_auto_schema(method='patch', request_body=PostOrPatchCategorySerializer)
@swagger_auto_schema(method='delete', request_body=PatchOrDeleteCategorySerializer)
@api_view(['GET', 'POST', 'PATCH', 'DELETE'])
def category(request):
    request_body = request.META['body']

    serializers = {
        'POST': [PostOrPatchCategorySerializer(data=request_body)],
        'PATCH': [PatchOrDeleteCategorySerializer(data=request_body), PostOrPatchCategorySerializer(data=request_body)],
        'GET': [GetCategorySerializer(data=request_body)],
        'DELETE': [PatchOrDeleteCategorySerializer(data=request_body)],
    }

    for serializer in serializers[request.method]:
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    if request.method == 'GET':
        user_categories = Category.categories_from_user(request.META['user'])
        categories_as_dict = [category.as_dict for category in user_categories]
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
