from django.urls import path
from .views import *


urlpatterns = [
    path('', student_dashboard, name='student_dashboard'),
    path("create-post/", create_post, name="create_post"),
    path('profile/', profile, name='profile'),
    path("post/<int:post_id>/like/", like_post, name="like_post"),
    path("post/<int:post_id>/dislike/", dislike_post, name="dislike_post"),
    path('results/', student_term_results_overview, name='term_overview'),
    path("results/<int:term_id>/", student_result_view, name="student_result_view"),
    path('students/leaderboard/<int:class_id>/', leaderboard, name='leaderboard'),


    path('pay/<int:student_id>/', pay_school_fees, name='pay_school_fees'),

]
