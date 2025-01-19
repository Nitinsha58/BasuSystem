from django.urls import path
from .views import index, update_test_progress, delete_test_progress


urlpatterns =  [
    path('', index, name="test_progress"),
    path('update_test_progress/<int:test_id>', update_test_progress, name="update_test_progress"),
    path('delete_test_progress/<int:test_id>', delete_test_progress, name="delete_test_progress"),
]