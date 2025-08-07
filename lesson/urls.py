from django.urls import path
from .views import (
    lesson,
    lesson_plan,
    lecture_plan
)

urlpatterns = [
    path('lesson/<int:sequence_id>/<int:class_id>/<int:batch_id>/', lesson, name='lesson'),
    path('lesson-plan/', lesson_plan, name='lesson_plan'),
    path('lesson-plan/<int:class_id>/', lesson_plan, name='lesson_plan_class'),
    path('lesson-plan/<int:class_id>/<int:batch_id>/', lesson_plan, name='lesson_plan_batch'),
    
    path('lecture-plan/', lecture_plan, name='lecture_plan'),
    path('lecture-plan/<int:class_id>/', lecture_plan, name='lecture_plan_class'),
    path('lecture-plan/<int:class_id>/<int:batch_id>/', lecture_plan, name='lecture_plan_batch'),
]