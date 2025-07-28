from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static


urlpatterns = [
    path('', include('academic_main.urls')),
    path('students/', include('stu_main.urls')),
    path('admin/', admin.site.urls),
    path('exam/', include('exams.urls')),
    path('teacher/', include('teacher_logic.urls')),
    path('assignments/', include('assignments.urls')),
    path('principal/', include('principal.urls')),
    path('parents/', include('parents.urls')),

]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

handler404 = "a_scholink.views.universal_error_view"
handler403 = "a_scholink.views.universal_error_view"
handler500 = "a_scholink.views.internal_server_error_view"
