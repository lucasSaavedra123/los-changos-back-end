from django.urls import path
from .views import sharedExpense,editSharedExpense

urlpatterns = [
    path('', sharedExpense),
    path('/edit',editSharedExpense)
    
]