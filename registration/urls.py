from django.urls import path
from .views import (
    student_registration, 
    student_fees_details, 
    student_parent_details, 
    student_transport_details,
    student_update,
    students_list,
    student_reg_doc,
    delete_installment,
    search_students,
    print_receipt,
    mark_attendance,
    mark_present,
    mark_absent,

    get_attendance,
    add_teacher,
    update_teacher,
    mark_homework,
    update_homework,
    get_homework,
    delete_attendance,
    delete_homework,

    # Test Paper
    test_templates,
    create_testpaper,
    delete_testpaper,
    create_test_question,
    update_test_question,

    # Test Response
    result_templates,
    calculate_marks,
    add_result,
    update_result,
    delete_result,
    all_pending_response,
    add_total_marks_obtained,
    add_test_result_type,

    # Transport
    transport_list,
    transport_driver_list,
    grouped_transports,
    add_driver,
    drivers_list,
    transport_attendance,

    # Mentorship Assignment
    assign_mentor,
    unassign_mentor,
    students_pick_drop,
    mark_transport_attendance,
    delete_transport_attendance,
    )


urlpatterns = [
    path('', students_list, name='students_list'),
    path('search-students/', search_students, name='search_students'),
    path('registration', student_registration, name='student_registration'),
    path('<uuid:stu_id>', student_update, name='student_update'),
    path('<uuid:stu_id>/parent', student_parent_details, name='student_parent_details'),
    path('<uuid:stu_id>/fees', student_fees_details, name='student_fees_details'),
    path('<uuid:stu_id>/transport', student_transport_details, name='student_transport_details'),
    path('<uuid:stu_id>/registration_document', student_reg_doc, name='student_reg_doc'),
    path('<uuid:stu_id>/receipt', print_receipt, name='receipt'),
    path('delete_installment/<uuid:stu_id>/<int:ins_id>', delete_installment, name='delete_installment'),

    path('mark_attendance/', mark_attendance, name='attendance'),
    path('mark_attendance/<int:class_id>/', mark_attendance, name='attendance_class'),
    path('mark_attendance/<int:class_id>/<int:batch_id>/', mark_attendance, name='attendance_batch'),

    path('mark_homework', mark_homework, name='homework'),
    path('mark_homework/<int:class_id>/', mark_homework, name='homework_class'),
    path('mark_homework/<int:class_id>/<int:batch_id>/', mark_homework, name='homework_batch'),
    path('update_homework/<int:class_id>/<int:batch_id>/', update_homework, name='homework_batch_update'),


    path('mark_present/<int:class_id>/<int:batch_id>/<int:attendance_id>', mark_present, name='mark_present'),
    path('mark_absent/<int:class_id>/<int:batch_id>/<int:attendance_id>', mark_absent, name='mark_absent'),
    path('delete_attendance/<int:class_id>/<int:batch_id>/<int:attendance_id>', delete_attendance, name='delete_attendance'),
    path('delete_homework/<int:class_id>/<int:batch_id>/<int:homework_id>', delete_homework, name='delete_homework'),

    # path('mark_attendance/<int:batch_id>', mark_attendance, name='mark_attendance'),
    path('get_attendance/<int:batch_id>', get_attendance, name='get_attendance'),
    # path('mark_homework/<int:batch_id>', mark_homework, name='mark_homework'),
    path('get_homework/<int:batch_id>', get_homework, name='get_homework'),

    path('add_teacher/', add_teacher, name='add_teacher'),
    path('update_teacher/<int:teacher_id>', update_teacher, name='update_teacher'),

    path('transport_list/', transport_list, name='transport_list'),
    path('transport_driver_list/', transport_driver_list, name='transport_driver_list'),
    path('grouped_transports/', grouped_transports, name='grouped_transports'),
    path('add_driver/', add_driver, name='add_driver'),


    # Mentorship Assignment
    path('assign_mentor/', assign_mentor, name='assign_mentor'),
    path('unassign_mentor/<uuid:stu_id>/', unassign_mentor, name='unassign_mentor'),

    # Test Paper
    path('test-templates/',test_templates, name='test_templates'),
    path('test-templates/<int:batch_id>/',test_templates, name='test_templates'),
    path('create-testpaper/<int:batch_id>/<int:test_id>/', create_testpaper, name="create_testpaper"),
    path('delete-testpaper/<int:test_id>/', delete_testpaper, name="delete_testpaper"),
    path('create-test-question/<int:batch_id>/<int:test_id>/', create_test_question, name="create_test_question"),
    path('update-test-question/<int:batch_id>/<int:test_id>/<int:question_id>', update_test_question, name="update_test_question"),

    path('calculate_marks/<int:batch_id>/<int:test_id>/', calculate_marks, name="calculate_marks"),


    # Test Response
    path('result-templates/', result_templates, name='result_templates'),
    path('add-result/<int:batch_id>/<int:test_id>/', add_result, name="add_result"),
    path('add-result/<int:batch_id>/<int:test_id>/<int:student_id>/', add_result, name="add_student_result"),
    path('add_total_marks_obtained/<int:batch_id>/<int:test_id>/<int:student_id>/', add_total_marks_obtained, name="add_total_marks_obtained"),
    path('add_test_result_type/<int:test_result_id>/', add_test_result_type, name="add_test_result_type"),

    path('add-result/<int:batch_id>/<int:test_id>/<int:student_id>/<int:question_id>', add_result, name="add_student_question_response"),
    path('update-result/<int:batch_id>/<int:test_id>/<int:student_id>/<int:response_id>', update_result, name="update_student_question_response"),
    path('delete-result/<int:batch_id>/<int:test_id>/<int:student_id>/<int:response_id>', delete_result, name="delete_student_question_response"),
    path('all-pending-response/<int:batch_id>/<int:test_id>/<int:student_id>', all_pending_response, name="all_pending_response"),

    #Transport Person
    path('students-pick-drop/', students_pick_drop, name="students_pick_drop"),
    path('mark-transport-attendance/', mark_transport_attendance, name="mark_transport_attendance"),
    path('delete_transport_attendance/', delete_transport_attendance, name="delete_transport_attendance"),
    path('drivers_list/', drivers_list, name='drivers_list'),
    path('transport_attendance/<int:driver_id>/', transport_attendance, name='transport_attendance'),
]