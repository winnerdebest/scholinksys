from django.contrib import admin
from .models import *


@admin.register(SubjectGradeSummary)
class SubjectGradeSummaryAdmin(admin.ModelAdmin):
    list_display = (
        'student',
        'class_subject',
        'term',
        'internal_exam_avg',
        'external_exam_score',
        'internal_assignment_avg',
        'external_assignment_score',
        'external_test_score',
        'calculated_total_score',
    )

    list_filter = ('class_subject', 'term')
    search_fields = ('student__username', 'student__first_name', 'student__last_name')

    def internal_exam_avg(self, obj):
        return round(obj.get_internal_exam_average(), 2)
    internal_exam_avg.short_description = "Internal Exam Avg"

    def internal_assignment_avg(self, obj):
        return round(obj.get_internal_assignment_average(), 2)
    internal_assignment_avg.short_description = "Internal Assignment Avg"

    def calculated_total_score(self, obj):
        return obj.total_score
    calculated_total_score.short_description = "Total Score"
    calculated_total_score.admin_order_field = None  # Not sortable


@admin.register(ClassGradeSummary)
class ClassGradeSummaryAdmin(admin.ModelAdmin):
    list_display = ('student', 'term', 'student_class', 'average_score', 'rank',)
    list_filter = ('term', 'student_class')
    search_fields = ('student__first_name', 'student__last_name', 'student__username')
    ordering = ('rank',)