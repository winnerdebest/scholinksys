from django.apps import AppConfig


class AcademicMainConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'academic_main'

    def ready(self):
        import academic_main.signals