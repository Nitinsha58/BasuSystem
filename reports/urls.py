from django.urls import path
from .views import (
    student_report,
    batchwise_students,
    mentor_students,
)

urlpatterns = [
    path('student/<uuid:stu_id>/', student_report, name='student_report'),
    path('batchwise_students/', batchwise_students, name='batchwise_students'),
    path('mentor_students/', mentor_students, name='mentor_students'),
]