from django.urls import path
from .views import expense, expense_filter

urlpatterns = [
    path('', expense),
    path('/filter', expense_filter)
]
