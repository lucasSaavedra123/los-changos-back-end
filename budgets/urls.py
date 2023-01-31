from django.urls import path
from .views import budget, current_budget, make_future_expense

urlpatterns = [
    path('', budget),
    path('/current', current_budget),
    path('/expended', make_future_expense)
]
