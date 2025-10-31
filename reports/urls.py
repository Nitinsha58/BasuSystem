from django.urls import path
from .views import (
    student_report,
    batchwise_students,
    mentor_students,
    teacher_students,
    student_personal_report,
    regular_absent_students,
    student_attendance_report,
    student_homework_report,
    student_test_summary_report,

    # Teachers Reports
    teachers_list,
    teacher_report,
    mentor_remarks,
    suggested_actions,
    compare_student_performance,
    update_recommendation,
    update_remark,
    add_student_remarks,
    delete_student_remark,
)

urlpatterns = [
    path('student/<uuid:stu_id>/', student_report, name='student_report'),
    path('student_attendance/<uuid:stu_id>/', student_attendance_report, name='student_attendance_report'),
    path('student_homework/<uuid:stu_id>/', student_homework_report, name='student_homework_report'),
    path('student_test_summary/<uuid:stu_id>/', student_test_summary_report, name='student_test_summary_report'),

    path('compare_performance/', compare_student_performance, name='compare_performance'),
    path('compare_performance/<int:class_id>/', compare_student_performance, name='compare_class'),
    path('compare_performance/<int:class_id>/<int:batch_id>/', compare_student_performance, name='compare_batch'),

    path('personal_report/<uuid:stu_id>/', student_personal_report , name='student_personal_report'),
    path('batchwise_students/', batchwise_students, name='batchwise_students'),
    path('mentor_students/', mentor_students, name='mentor_students'),
    path('regular_absent_students/', regular_absent_students, name='regular_absent_students'),

    # Teachers Reports
    path('teacher_students/', teacher_students, name='teacher_students'),

    path('teachers_list/', teachers_list, name='teachers_list'),
    path('teacher_report/<int:teacher_id>/', teacher_report, name='teacher_report'),

    path('mentor_remarks/<int:mentor_id>/<uuid:student_id>/', mentor_remarks, name='mentor_remarks'),
    path('suggested_actions/', suggested_actions, name='suggested_actions'),

    path("update-recommendation/", update_recommendation, name="update-recommendation"),
    path("update-remark/<int:test_id>/<uuid:student_id>/", update_remark, name="update-remark"),

    path("add-student-remarks/<int:mentor_id>/<uuid:stu_id>/", add_student_remarks, name="add-student-remarks"),
    path("delete-student-remark/<int:remark_id>/<int:mentor_id>/<uuid:stu_id>/",delete_student_remark, name="delete-student-remark"),
]