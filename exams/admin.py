from django.contrib import admin
from django.utils.html import format_html
from .models import Exam, Assignment, Question, StudentExamRecord, StudentAssignmentRecord


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


@admin.register(Exam)
class ExamAdmin(admin.ModelAdmin):
    list_display = ( 'class_subject', 'term', 'is_active', 'created_at')
    list_filter = ('class_subject', 'is_active')
    search_fields = ('title', 'class_subject__subject__name')
    inlines = [QuestionInline]





@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    list_display = ('short_text', 'exam', 'assignment', 'created_by', 'correct_answer')
    list_filter = ('exam', 'assignment', 'created_by')
    search_fields = ('text', 'created_by__username')

    def short_text(self, obj):
        return obj.text[:60] if obj.text else "Image Question"
    short_text.short_description = "Question"


@admin.register(StudentExamRecord)
class StudentExamRecordAdmin(admin.ModelAdmin):
    list_display = ('student', 'exam', 'score', 'submitted_at', 'is_submitted')
    list_filter = ('exam', 'is_submitted')
    search_fields = ('student__username', 'exam__title')
    readonly_fields = ('responses', 'score', 'submitted_at')



