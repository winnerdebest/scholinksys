from django.contrib.auth.models import AbstractUser
from django.db import models
from academic_main.models import School
import uuid
from datetime import date


from django.conf import settings
from cloudinary.models import CloudinaryField


class CustomUser(AbstractUser):
    USER_TYPES = (
        ('admin', 'Admin'),
        ('principal', 'Principal'),
        ('teacher', 'Teacher'),
        ('student', 'Student'),
        ('parent', 'Parent'),
    )
    user_type = models.CharField(max_length=10, choices=USER_TYPES, default='principal')



class Teacher(models.Model):
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE)
    school = models.ForeignKey(School, on_delete=models.CASCADE)
    salary = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)

    def __str__(self):
        return self.user.get_full_name()


class Class(models.Model):
    name = models.CharField(max_length=100)
    school = models.ForeignKey(School, on_delete=models.CASCADE, related_name="classes")
    form_master = models.ForeignKey(
        CustomUser,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        limit_choices_to={'user_type': 'teacher'},
        related_name='form_master_classes'
    )

    class Meta:
        unique_together = ('name', 'school')

    def __str__(self):
        return f"{self.name} ({self.school.name})"


class Subject(models.Model):
    name = models.CharField(max_length=100)
    school = models.ForeignKey(School, on_delete=models.CASCADE, related_name="subjects")
    code = models.CharField(max_length=20, null=True, blank=True)
    description = models.TextField(blank=True)

    def __str__(self):
        return f"{self.name} ({self.school.name})"


class ClassSubject(models.Model):
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE, null=True, blank=True)
    school_class = models.ForeignKey(Class, on_delete=models.CASCADE, related_name="class_subjects")
    teacher = models.ForeignKey(Teacher, on_delete=models.CASCADE, related_name="class_subjects")

    class Meta:
        unique_together = ('subject', 'school_class')

    def __str__(self):
        return f"{self.subject.name} - {self.school_class.name}"
    


class Parent(models.Model):
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE, related_name='parent_profile')
    phone_number = models.CharField(max_length=15)
    address = models.TextField(blank=True, null=True)
    occupation = models.CharField(max_length=100, blank=True, null=True)

    def __str__(self):
        return f"{self.user.get_full_name()}"



class Student(models.Model):
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE, related_name="student_profile")
    registration_number = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    if settings.USE_CLOUDINARY:
        photo = CloudinaryField('product_images', transformation=[
                {'width': 800, 'height': 800, 'crop': 'limit', 'quality': 'auto', 'fetch_format': 'webp'}
            ], default='static/student-example3.jpg')
    else:
        photo = models.ImageField(upload_to='student_photos/', blank=True, null=True)
    phone_number = models.CharField(max_length=15, blank=True, null=True)
    date_of_birth = models.DateField(null=True, blank=True)
    parents = models.ManyToManyField(Parent, related_name="children", blank=True)
    student_class = models.ForeignKey(
        Class,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="students"
    )

    def __str__(self):
        return f"{self.user.get_full_name()} - {self.student_class}"
    
    @property
    def school(self):
        return self.student_class.school if self.student_class else None
    
    @property
    def age(self):
        if self.date_of_birth:
            today = date.today()
            return today.year - self.date_of_birth.year - ((today.month, today.day) < (self.date_of_birth.month, self.date_of_birth.day))
        return None
    

class StudentPost(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name="posts", null=True, blank=True)
    created_by = models.ForeignKey(CustomUser, on_delete=models.SET_NULL, related_name="created_posts", null=True, blank=True)
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    likes = models.ManyToManyField(Student, related_name="liked_posts", blank=True)
    dislikes = models.ManyToManyField(Student, related_name="disliked_posts", blank=True)
    school = models.ForeignKey(School, on_delete=models.CASCADE, null=True, blank=True, related_name='posts')

    def __str__(self):
        if self.student:
            return f"Post by {self.student.user.get_full_name()}"
        elif self.created_by:
            return f"Post by {self.created_by.get_full_name()}"
        return "Post"

    def total_likes(self):
        return self.likes.count()

    def total_dislikes(self):
        return self.dislikes.count()
    
    def is_form_master_post(self):
        return self.created_by is not None and self.created_by.user_type == "teacher" and not self.student

