from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import SubjectGradeSummary
from .utils import generate_class_rankings 


@receiver(post_save, sender=SubjectGradeSummary)
def update_class_grade_summary(sender, instance, **kwargs):
    student_class = instance.class_subject.school_class
    term = instance.term
    generate_class_rankings(term=term, student_class=student_class)
