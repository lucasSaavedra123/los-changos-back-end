from django.urls import path
from .views import budget, current_budget

urlpatterns = [
    path('', budget),
    path('/current', current_budget)
]
