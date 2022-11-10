from django.urls import path
from .views import budget

urlpatterns = [
    path('', budget)
]
