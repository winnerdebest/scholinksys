from django.urls import path
from .views import *

app_name = 'principal'


urlpatterns = [
    path("", principal_dashboard, name="principal_dashboard"),

    #path('register-student/', StudentCreateUpdateView.as_view(), name='create_student'),
    #path('<int:student_id>/edit/', StudentCreateUpdateView.as_view(), name='update_student'),
    path("register-student/", create_or_update_student, name="create_student"),
    path('<int:student_id>/edit/', create_or_update_student, name='update_student'),
    path('delete/<int:student_id>/', delete_student, name='delete_student'),
    path('student-list/', student_list, name='student_list'),

    path("register-teacher/", create_teacher, name="create_teacher"),
    path("edit-teacher/<int:pk>/", edit_teacher, name="edit_teacher"),
    path("delete-teacher/<int:pk>/", delete_teacher, name="delete_teacher"),
    path('teacher-list/', teacher_list, name='teacher_list'),
    path('class-list/', class_list, name='class_list'),
    path('subject-list/',subject_list, name='subject_list'),


    path("subjects/", subject_list, name="subject_list"),
    path("subjects/create/", create_subject, name="create_subject"),
    path("subjects/<int:subject_id>/edit/", edit_subject, name="edit_subject"),
    path("subjects/<int:subject_id>/delete/", delete_subject, name="delete_subject"),

    path('create-class/', create_or_update_class, name="create_class"),
    path('edit-class/<int:class_id>/edit/', create_or_update_class, name="edit_class"),
    path("classes/<int:class_id>/delete/", delete_class, name="delete_class"),
    path('class-list/', class_list, name="class_list"),
    path("classes/<int:class_id>/", class_detail, name="class_detail"),

    path("classes/<int:class_id>/assign-subject/", assign_subject_to_class, name="assign_subject"),
    path("class-subjects/<int:classsubject_id>/edit/", edit_class_subject, name="edit_class_subject"),
    path("class-subjects/<int:classsubject_id>/delete/", delete_class_subject, name="delete_class_subject"),


    path("grade_customize/", customize_grade_weights, name="grade_customize"),
    path("settings/", settings_view, name="settings"), 
    # URL for payment info creation, update, and deletion
    path("payment/create/", PaymentInfoCreateUpdateView.as_view(), name="paymentinfo-create"),
    path("payment/<int:pk>/delete/", PaymentInfoDeleteView.as_view(), name="paymentinfo-delete"),


    path("expenses/", expense_list, name="expense_list"),
    path("expenses/create/", create_expense, name="create_expense"),
    path("expenses/<int:expense_id>/edit/", edit_expense, name="edit_expense"),
    path("expenses/<int:expense_id>/delete/", delete_expense, name="delete_expense"),
    path("expenses/export/excel/", export_expenses_excel, name="export_expenses_excel"),
    path("expenses/export/pdf/", export_expenses_pdf, name="export_expenses_pdf"),

    # Teacher Salary URLs
    path("teacher-salaries/", teacher_salaries, name="teacher_salaries"),
    path("teacher-salaries/<int:teacher_id>/update/", update_salary_payment, name="update_salary_payment"),
    path("teacher-salaries/process-bulk/", process_bulk_payment, name="process_bulk_payment"),

    # Announcement URLs
    path('announcements/create/', create_announcement, name='create_announcement'),
    path('announcements/<int:pk>/edit/', edit_announcement, name='edit_announcement'),
    path('announcements/<int:pk>/delete/', delete_announcement, name='delete_announcement'),

    # Revenue Management URLs
    path('revenue/', revenue_dashboard, name='revenue_dashboard'),
    path('revenue/export/', export_revenue_report, name='export_revenue_report'),
    
    # Fee Payment URLs
    path('revenue/record-payment/', record_fee_payment, name='record_fee_payment'),
    path('revenue/payments/<int:payment_id>/', payment_details, name='payment_details'),
    
    
    # Additional Fees URLs
    path('revenue/additional-fees/', manage_additional_fees, name='manage_additional_fees'),
    path('revenue/additional-fees/<int:fee_id>/edit/', edit_additional_fee, name='edit_additional_fee'),
    path('revenue/additional-fees/<int:fee_id>/delete/', delete_additional_fee, name='delete_additional_fee'),
    
    # Fee Categories URLs
    path('revenue/fee-categories/', fee_categories, name='fee_categories'),
    path('revenue/fee-categories/<int:category_id>/edit/', edit_fee_category, name='edit_fee_category'),
    path('revenue/fee-categories/<int:category_id>/delete/', delete_fee_category, name='delete_fee_category'),
    
    # Class Fees URLs
    path('revenue/class-fees/', class_fees, name='class_fees'),
    path('revenue/class-fees/<int:fee_id>/edit/', edit_class_fee, name='edit_class_fee'),
    path('revenue/class-fees/<int:fee_id>/delete/', delete_class_fee, name='delete_class_fee'),
    
    # Student Discounts URLs
    #path('revenue/discounts/', student_discounts, name='student_discounts'),
    path('revenue/discounts/<int:discount_id>/edit/', edit_student_discount, name='edit_student_discount'),
    path('revenue/discounts/<int:discount_id>/delete/', delete_student_discount, name='delete_student_discount'),
    
    
    
    # API Endpoints for Revenue Management
    path('api/additional-fees/<int:fee_id>/', additional_fee_detail, name='additional_fee_detail'),
    path('api/revenue/stats/', revenue_stats_api, name='revenue_stats_api'),
    path('api/revenue/chart-data/', revenue_chart_data_api, name='revenue_chart_data_api'),
]
