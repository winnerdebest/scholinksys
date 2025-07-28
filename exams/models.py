from django.db import models
from stu_main.models import *
from assignments.models import *
from academic_main.models import *

from django.conf import settings
from cloudinary.models import CloudinaryField


class Exam(models.Model):
    class_subject = models.ForeignKey(ClassSubject, on_delete=models.CASCADE, related_name='exams', null=True, blank=True)
    term = models.ForeignKey(Term, on_delete=models.CASCADE, related_name='exams')
    duration_minutes = models.PositiveIntegerField()
    is_active = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True, null=True)

    def __str__(self):
        return f"{self.class_subject} ({self.class_subject})"



class Question(models.Model):
    exam = models.ForeignKey(Exam, on_delete=models.CASCADE, related_name='questions', blank=True, null=True)
    assignment = models.ForeignKey(Assignment, on_delete=models.CASCADE, related_name='questions', blank=True, null=True)

    text = models.TextField(blank=True, null=True)
    if settings.USE_CLOUDINARY:
        image = CloudinaryField('question_images/', transformation=[
                {'width': 800, 'height': 800, 'crop': 'limit', 'quality': 'auto', 'fetch_format': 'webp'}
            ], default='static/student-example3.jpg')
    else:
        image = models.ImageField(upload_to='question_images/', blank=True, null=True)

    option_a_text = models.CharField(max_length=255, blank=True, null=True)
    if settings.USE_CLOUDINARY:
        option_a_image = CloudinaryField('answer_images/', transformation=[
                {'width': 800, 'height': 800, 'crop': 'limit', 'quality': 'auto', 'fetch_format': 'webp'}
            ], default='static/student-example3.jpg')
    else:
        option_a_image = models.ImageField(upload_to='answer_images/', blank=True, null=True)

    option_b_text = models.CharField(max_length=255, blank=True, null=True)
    if settings.USE_CLOUDINARY:
        option_b_image = CloudinaryField('answer_images/', transformation=[
                {'width': 800, 'height': 800, 'crop': 'limit', 'quality': 'auto', 'fetch_format': 'webp'}
            ], default='static/student-example3.jpg')
    else:
        option_b_image = models.ImageField(upload_to='answer_images/', blank=True, null=True)

    option_c_text = models.CharField(max_length=255, blank=True, null=True)
    if settings.USE_CLOUDINARY:
        option_c_image = CloudinaryField('answer_images/', transformation=[
                {'width': 800, 'height': 800, 'crop': 'limit', 'quality': 'auto', 'fetch_format': 'webp'}
            ], default='static/student-example3.jpg')
    else:
        option_c_image = models.ImageField(upload_to='answer_images/', blank=True, null=True)

    option_d_text = models.CharField(max_length=255, blank=True, null=True)
    if settings.USE_CLOUDINARY:
        option_d_image = CloudinaryField('answer_images/', transformation=[
                {'width': 800, 'height': 800, 'crop': 'limit', 'quality': 'auto', 'fetch_format': 'webp'}
            ], default='static/student-example3.jpg')
    else:
        option_d_image = models.ImageField(upload_to='answer_images/', blank=True, null=True)

    correct_answer = models.CharField(
        max_length=1,
        choices=[('A', 'A'), ('B', 'B'), ('C', 'C'), ('D', 'D')]
    )

    created_by = models.ForeignKey(CustomUser, on_delete=models.CASCADE, limit_choices_to={'user_type': 'teacher'})

    def __str__(self):
        if self.text:
            return self.text[:50]
        return f"Image Question by {self.created_by.username}"


class StudentExamRecord(models.Model):
    student = models.ForeignKey(CustomUser, on_delete=models.CASCADE, limit_choices_to={'user_type': 'student'}, related_name='exam_records')
    term = models.ForeignKey(Term, on_delete=models.SET_NULL, null=True, blank=True, related_name='exam_records')
    exam = models.ForeignKey(Exam, on_delete=models.CASCADE, related_name='student_records')
    responses = models.JSONField()  # Format: {"question_id": "A"}
    score = models.FloatField()
    submitted_at = models.DateTimeField(auto_now_add=True)
    is_submitted = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.student.username} - {self.exam.class_subject}"



