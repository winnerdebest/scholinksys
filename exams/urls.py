from django.urls import path
from .views import *


urlpatterns = [
    path('exam-login/', exam_login_view, name='exam_login'),
    path('exam-logout/', exam_logout_view, name='exam_logout'),
    path('available_exams/', available_exams_view, name='available_exams'),
    path("<int:exam_id>/", take_exam, name="take_exam"),
    path("<int:exam_id>/question/<int:question_index>/", get_question, name="get_question"),
    path("save-answer/", save_answer, name="save-answer"),
    path('<int:exam_id>/result/', exam_result, name='exam-result'),
]
