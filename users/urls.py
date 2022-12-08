from django.urls import path
from .views import user,getUsers

urlpatterns = [
    path('/getUsers', getUsers),
    path('',user)
]




