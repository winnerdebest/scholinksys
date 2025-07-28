from django.contrib import admin
from .models import *

@admin.register(ExpenseCategory)
class ExpenseCategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'school')
    search_fields = ('name',)
    list_filter = ('school',)


@admin.register(Expense)
class ExpenseAdmin(admin.ModelAdmin):
    list_display = ('category', 'amount', 'date', 'payment_status', 'school')
    search_fields = ('description',)
    list_filter = ('payment_status', 'category', 'school')


@admin.register(TeacherSalaryPayment)
class TeacherSalaryPaymentAdmin(admin.ModelAdmin):
    list_display = ('teacher', 'month', 'net_salary', 'basic_salary', 'allowances', 'deductions')
    list_filter = ('month', 'teacher__school')
    search_fields = ('teacher__user__first_name', 'teacher__user__last_name')


@admin.register(Announcement)
class AnnouncementAdmin(admin.ModelAdmin):
    list_display = ('title', 'school', 'priority', 'is_active', 'created_at')
    list_filter = ('priority', 'is_active', 'school')
    search_fields = ('title', 'content')


@admin.register(ClassFee)
class ClassFeeAdmin(admin.ModelAdmin):
    list_display = ('school_class', 'amount')
    list_filter = ('school_class',)
    search_fields = ('school_class__name',)


@admin.register(AdditionalFee)
class AdditionalFeeAdmin(admin.ModelAdmin):
    list_display = ('name', 'amount', 'is_general')
    list_filter = ( 'is_general',)
    search_fields = ('name',)
    filter_horizontal = ('applicable_classes',)


@admin.register(StudentDiscount)
class StudentDiscountAdmin(admin.ModelAdmin):
    list_display = ('student', 'term', 'discount_type', 'discount_value', 'is_active')
    list_filter = ('term', 'discount_type', 'is_active')
    search_fields = ('student__user__first_name', 'student__user__last_name')


@admin.register(FeePayment)
class FeePaymentAdmin(admin.ModelAdmin):
    list_display = (
        'student', 'term', 'payment_type', 'amount', 'amount_paid',
        'payment_status', 'payment_method', 'payment_date', 'receipt_number'
    )
    list_filter = (
        'payment_status', 'payment_method', 'term', 'payment_type'
    )
    search_fields = (
        'student__user__first_name', 'student__user__last_name', 'receipt_number'
    )
    readonly_fields = ('receipt_number',)
