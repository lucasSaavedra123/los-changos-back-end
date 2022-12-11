from django.urls import path
from .views import sharedExpense,editSharedExpense,getPendingSharedExpensesCreatedToMe

urlpatterns = [
    path('', sharedExpense),
    path('/edit',editSharedExpense),
    path('/pending',getPendingSharedExpensesCreatedToMe)
    
]