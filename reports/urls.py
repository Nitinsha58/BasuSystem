from django.urls import path
from .views import (
    student_report,
    batchwise_students,
    mentor_students,
    student_personal_report,
    regular_absent_students,
    student_attendance_report,
    student_homework_report,

    # Teachers Reports
    teachers_list,
    teacher_report,
    mentor_remarks,
    suggested_actions
)

urlpatterns = [
    path('student/<uuid:stu_id>/', student_report, name='student_report'),
    path('student_attendance/<uuid:stu_id>/', student_attendance_report, name='student_attendance_report'),
    path('student_homework/<uuid:stu_id>/', student_homework_report, name='student_homework_report'),

    path('personal_report/<uuid:stu_id>/', student_personal_report , name='student_personal_report'),
    path('batchwise_students/', batchwise_students, name='batchwise_students'),
    path('mentor_students/', mentor_students, name='mentor_students'),
    path('regular_absent_students/', regular_absent_students, name='regular_absent_students'),

    # Teachers Reports
    path('teachers_list/', teachers_list, name='teachers_list'),
    path('teacher_report/<int:teacher_id>/', teacher_report, name='teacher_report'),

    path('mentor_remarks/<int:mentor_id>/<uuid:student_id>/', mentor_remarks, name='mentor_remarks'),
    path('suggested_actions/', suggested_actions, name='suggested_actions')
]