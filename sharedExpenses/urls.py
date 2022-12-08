from django.urls import path
from .views import sharedExpense

urlpatterns = [
    path('', sharedExpense),
    
]