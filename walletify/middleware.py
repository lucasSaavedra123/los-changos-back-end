from django.http import HttpResponseForbidden
import firebase_admin

from users.models import User


class CustomFirebaseAuthentication:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        return response

    def process_view(self, request, view_func, view_args, view_kwargs):
        try:
            authorization_header = request.META.get('HTTP_AUTHORIZATION')
            token = authorization_header.replace("Bearer ", "")
            decoded_token = firebase_admin.auth.verify_id_token(token)
            request.META['uid'] = decoded_token['user_id']
        except:
            return HttpResponseForbidden()

        return None


class CustomUserCreation:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        return response

    def process_view(self, request, view_func, view_args, view_kwargs):
        request.META['uid'] = 'a' * 28

        if not User.objects.filter(firebase_uid=request.META['uid']):
            User.objects.create(firebase_uid=request.META['uid'])

        request.META['user'] = User.objects.get(firebase_uid=request.META['uid'])

        return None