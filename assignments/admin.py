from django.contrib import admin
from .models import *
from django.utils.html import format_html
from exams.models import Question


class QuestionInline(admin.TabularInline):
    model = Question
    extra = 1
    fields = (
        'text', 'image', 'display_image',
        'option_a_text', 'option_a_image',
        'option_b_text', 'option_b_image',
        'option_c_text', 'option_c_image',
        'option_d_text', 'option_d_image',
        'correct_answer',
        'created_by',
    )
    readonly_fields = ('display_image',)

    def display_image(self, obj):
        if obj.image:
            return format_html('<img src="{}" width="100" height="100"/>', obj.image.url)
        return "No Image"
    display_image.short_description = "Question Image"



@admin.register(Assignment)
class AssignmentAdmin(admin.ModelAdmin):
    list_display = ('class_subject', 'is_active', 'created_at')
    list_filter = ('class_subject', 'is_active')
    search_fields = ('title', 'class_subject__subject__name')

@admin.register(StudentAssignmentRecord)
class StudentAssignmentRecordAdmin(admin.ModelAdmin):
    list_display = ('student', 'assignment', 'score', 'submitted_at', 'is_submitted')
    list_filter = ('assignment', 'is_submitted')
    search_fields = ('student__username', 'assignment__title')
    readonly_fields = ('responses', 'score', 'submitted_at')