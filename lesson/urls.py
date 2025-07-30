from django.urls import path
from .views import (
    lesson,
    lesson_plan,
)

urlpatterns = [
    path('lesson/<int:sequence_id>/<int:class_id>/<int:batch_id>/', lesson, name='lesson'),
    path('lesson-plan/', lesson_plan, name='lesson_plan'),
    path('lesson-plan/<int:class_id>/', lesson_plan, name='lesson_plan_class'),
    path('lesson-plan/<int:class_id>/<int:batch_id>/', lesson_plan, name='lesson_plan_batch'),
]