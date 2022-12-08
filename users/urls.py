from django.urls import path
from .views import user, getUser

urlpatterns = [
    path('', user),
    path('/currentUser', getUser),
]




