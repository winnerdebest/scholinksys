from django.apps import AppConfig


class TeacherLogicConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'teacher_logic'


    def ready(self):
        import teacher_logic.signals