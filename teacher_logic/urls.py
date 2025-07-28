from django.urls import path
from .views import *

app_name = 'teacher'

urlpatterns = [
    path('', teacher_dashboard, name='teacher_dashboard'),
    path('teacher/class/<int:class_id>/', teacher_class_detail, name='teacher_class_detail'),
    path("subject/<int:class_subject_id>/", subject_detail_view, name="class_subject_detail"),
    # Activation toggle
    path("assignment/<int:assignment_id>/toggle/", toggle_assignment_active, name="toggle_assignment_active"),
    path("exam/<int:exam_id>/toggle/", toggle_exam_active, name="toggle_exam_active"),

    path('subjects/<int:class_subject_id>/term/<int:term_id>/create-exam/', create_exam, name='create_exam'),
    path('subjects/<int:class_subject_id>/term/<int:term_id>/create-assignment/', create_assignment, name='create_assignment'),

    # Edit
    path('exam/<int:exam_id>/edit/', edit_exam, name='edit_exam'),
    path('assignment/<int:assignment_id>/edit/', edit_assignment, name='edit_assignment'),

    # Delete
    path('exam/<int:exam_id>/delete/', delete_exam, name='delete_exam'),
    path('assignment/<int:assignment_id>/delete/', delete_assignment, name='delete_assignment'),

    # Student Grade
    path('class-subject/<int:class_subject_id>/students/', subject_student_list_view, name='subject_student_list'),
    path("grade/<int:class_subject_id>/<int:student_id>/<int:term_id>/", grade_student, name="grade_student"),
    path("edit_grade/<int:class_subject_id>/<int:student_id>/<int:term_id>/", edit_student_grade, name="edit_student_grade"),

    # Form Master 
    path('class-posts/', class_posts_view, name='class_posts'),
    path('delete-post/<int:post_id>/', delete_post, name='delete_post'),
    path('no-class-assigned/', no_class_assigned, name='no_class_assigned'),
    
    path('coming_soon/', upcoming_feature, name='upcoming_feature')


]
