from django.urls import path
from .views import *


urlpatterns = [
    path('', index, name='index'),
    path('register/', register_principal, name='register_principal'),
    path('login/', user_login_view, name='user_login'),
    path('logout/', user_logout_view, name='user_logout'),
    path('test-email/', test_email),
]
