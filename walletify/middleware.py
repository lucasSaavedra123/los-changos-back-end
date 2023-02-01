import json
import os

from django.http import JsonResponse
from firebase_admin import auth
from firebase_admin._token_gen import ExpiredIdTokenError
from firebase_admin._auth_utils import InvalidIdTokenError
from users.models import User


class CustomFirebaseAuthentication:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        return response

    def process_view(self, request, view_func, view_args, view_kwargs):
        if not (request.path.startswith('/docs') or request.path.startswith('/redocs')):
            if os.environ.get('ENVIRONMENT') == "DEV":
                request.META['uid'] = 'randomrandomrandomrandomrand'
                request.META['email'] = 'random@random.com'
            else:
                try:
                    authorization_header = request.META.get('HTTP_AUTHORIZATION')
                    token = authorization_header.replace("Bearer ", "")
                    decoded_token = auth.verify_id_token(token)
                    request.META['uid'] = decoded_token['user_id']
                    request.META['email'] = decoded_token['email']
                except KeyError:
                    return JsonResponse({"message": "A valid token was not provided"}, status=401)
                except AttributeError:
                    return JsonResponse({"message": "A valid token was not provided"}, status=401)
                except ExpiredIdTokenError:
                    return JsonResponse({"message": "A valid token was not provided"}, status=401)
                except InvalidIdTokenError:
                    return JsonResponse({"message": "A valid token was not provided"}, status=401)

        return None


class CustomUserCreation:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        return response

    def process_view(self, request, view_func, view_args, view_kwargs):

        if not User.objects.filter(firebase_uid=request.META['uid'], email=request.META['email']).exists():
            User.objects.create(firebase_uid=request.META['uid'], email=request.META['email'])

        request.META['user'] = User.objects.get(firebase_uid=request.META['uid'], email=request.META['email'])

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
