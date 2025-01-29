from django.urls import path
from .views import ( 
    staff_dashboard,
    staff_student_registration,
    staff_student_delete,
    staff_student_update,

    staff_teacher_registration,
    staff_teacher_update,
    staff_teacher_delete,


    create_test_template,
    create_test_response,
    create_response,
    create_template,
    delete_template,
    create_question,
    update_question,
    update_response,
    delete_response,
    create_all_pending_response,
    
    batchwise_report,
    chapterwise_report,
    
    chapterwise_personal_report,
    chapterwise_student_report,

    compare_progres,
    calculate_total_marks,
    create_marks_obtained,
    
    getQuery
)

urlpatterns = [
    path('getQuery/', getQuery),
    path('', staff_dashboard, name="staff_dashboard"),
    path('student-registration/', staff_student_registration, name="staff_student_registration"),
    path('student-registration/<int:is_batch>', staff_student_registration, name="staff_student_registration_batch"),
    path('student-delete/<int:user_id>', staff_student_delete, name="staff_student_delete"),
    path('student-update/<int:student_id>/', staff_student_update, name="staff_student_update"),
    
    path('teacher-registration/', staff_teacher_registration, name="staff_teacher_registration"),
    path('teacher-registration/<int:is_batch>', staff_teacher_registration, name="staff_teacher_registration_batch"),
    path('teacher-delete/<int:user_id>', staff_teacher_delete, name="staff_teacher_delete"),
    path('teacher-update/<int:teacher_id>/', staff_teacher_update, name="staff_teacher_update"),

    path('create-test-template/', create_test_template, name="create_test_template"),
    path('create-test-response/', create_test_response, name="create_test_response"),

    path('create-test-response/<int:batch_id>/<int:test_id>/', create_response, name="create_response"),
    path('create-test-response/<int:batch_id>/<int:test_id>/<int:student_id>/', create_response, name="create_student_response"),
    path('create-test-response/<int:batch_id>/<int:test_id>/<int:student_id>/<int:question_id>', create_response, name="add_response"),
    path('update-test-response/<int:batch_id>/<int:test_id>/<int:student_id>/<int:response_id>', update_response, name="update_response"),
    path('delete-test-response/<int:batch_id>/<int:test_id>/<int:student_id>/<int:response_id>', delete_response, name="delete_response"),
    path('create-all-test-response/<int:batch_id>/<int:test_id>/<int:student_id>', create_all_pending_response, name="create_all_pending_response"),
    
    path('create-marks-obtained/<int:batch_id>/<int:test_id>/<int:student_id>/', create_marks_obtained, name="create_marks_obtained"),

    path('create-test-template/<int:batch_id>/', create_test_template, name="create_test_template"),
    path('create-template/<int:batch_id>/<int:test_id>/', create_template, name="create_template"),
    path('delete-template/<int:batch_id>/<int:test_id>/', delete_template, name="delete_template"),
    path('create-question/<int:batch_id>/<int:test_id>/', create_question, name="create_question"),
    path('update-question/<int:batch_id>/<int:test_id>/<int:question_id>', update_question, name="update_question"),

    path('calculate_total_marks/<int:batch_id>/<int:test_id>/', calculate_total_marks, name="calculate_total_marks"),

    path('batchwise_report/', batchwise_report, name="batchwise_report"),
    path('batchwise_report/<int:batch_id>/', batchwise_report, name="batch_report"),

    path('chapterwise_report/', chapterwise_report, name="chapterwise_report"),
    path('chapterwise_report/<int:batch_id>', chapterwise_report, name="chapter_batch_report"),

    #student personal
    path('chapterwise_personal_report/', chapterwise_personal_report, name="chapterwise_personal_report"),
    path('chapterwise_personal-report/<int:batch_id>', chapterwise_personal_report, name="chapter_personal_batch_report"),

    path('personal_student_report/<int:student_id>', chapterwise_personal_report, name="personal_student_report"),
    path('personal_student_report/<int:batch_id>/<int:student_id>', chapterwise_personal_report, name="personal_student_batch_report"),
 
    #student
    path('chapterwise_student_report/', chapterwise_student_report, name="chapterwise_student_report"),
    path('chapterwise_student_report/<int:batch_id>/', chapterwise_student_report, name="chapter_student_batch_report"),
    path('chapterwise_student_report/<int:batch_id>/<int:student_id>', chapterwise_student_report, name="chapter_student_batch_report_progress"),
    
    path('compare_progress/', compare_progres, name="compare_progress"),
    path('compare_progress/<int:batch_id>', compare_progres, name="compare_batch_progress"),
]