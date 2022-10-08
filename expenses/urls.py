from django.urls import path
from .views import expense

urlpatterns = [
    path('', expense)
]
