from django.urls import path
from .views import (
    lesson,
    lesson_plan,
    lecture_plan,

    add_lecture,
    delete_lecture,
    add_bulk_lecture_dates
)

urlpatterns = [
    path('lesson/<int:sequence_id>/<int:class_id>/<int:batch_id>/', lesson, name='lesson'),
    path('lesson-plan/', lesson_plan, name='lesson_plan'),
    path('lesson-plan/<int:class_id>/', lesson_plan, name='lesson_plan_class'),
    path('lesson-plan/<int:class_id>/<int:batch_id>/', lesson_plan, name='lesson_plan_batch'),
    
    path('lecture-plan/', lecture_plan, name='lecture_plan'),
    path('lecture-plan/<int:class_id>/', lecture_plan, name='lecture_plan_class'),
    path('lecture-plan/<int:class_id>/<int:batch_id>/', lecture_plan, name='lecture_plan_batch'),

    path('add-lecture/<int:class_id>/<int:batch_id>/<int:lesson_id>/', add_lecture, name="add_lecture"),
    path('delete-lecture/<int:class_id>/<int:batch_id>/<int:lecture_id>/', delete_lecture, name="delete_lecture"),

    path('add-bulk-lecture-dates/', add_bulk_lecture_dates, name="add_bulk_lecture_dates"),
    path('add-bulk-lecture-dates/<int:class_id>/', add_bulk_lecture_dates, name="add_bulk_lecture_dates_class"),
    path('add-bulk-lecture-dates/<int:class_id>/<int:batch_id>/', add_bulk_lecture_dates, name="add_bulk_lecture_dates_batch"),


]