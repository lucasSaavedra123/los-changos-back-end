import json
import os

from django.http import HttpResponse
import firebase_admin

from users.models import User


class CustomFirebaseAuthentication:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        return response

    def process_view(self, request, view_func, view_args, view_kwargs):
        if os.environ.get('ENVIRONMENT') == "PROD":
            try:
                print(request.META.get('HTTP_AUTHORIZATION'))
                authorization_header = request.META.get('HTTP_AUTHORIZATION')
                print(authorization_header)
                token = authorization_header.replace("Bearer ", "")
                print(token)
                decoded_token = firebase_admin.auth.verify_id_token(token)
                request.META['uid'] = decoded_token['user_id']
            except:
                return HttpResponse(None, status=401)
        elif os.environ.get('ENVIRONMENT') == "DEV":
            request.META['uid'] = 'randomrandomrandomrandomrand'

        return None


class CustomUserCreation:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        return response

    def process_view(self, request, view_func, view_args, view_kwargs):

        if not User.objects.filter(firebase_uid=request.META['uid']):
            User.objects.create(firebase_uid=request.META['uid'])

        request.META['user'] = User.objects.get(firebase_uid=request.META['uid'])

        return None

class SanitizeRequest:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        return response

    def process_view(self, request, view_func, view_args, view_kwargs):
        if request.body == b'':
            request.META['body'] = {}
        else:
            request.META['body'] = json.loads(request.body.decode('utf-8'))

        return None
