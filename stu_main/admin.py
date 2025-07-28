from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import *



# CustomUser admin (extends default UserAdmin)
@admin.register(CustomUser)
class CustomUserAdmin(UserAdmin):
    list_display = ('username', 'email', 'first_name', 'last_name', 'user_type', 'is_staff')
    list_filter = ('user_type', 'is_staff', 'is_superuser')
    fieldsets = UserAdmin.fieldsets + (
        (None, {'fields': ('user_type',)}),
    )
    add_fieldsets = UserAdmin.add_fieldsets + (
        (None, {'fields': ('user_type',)}),
    )
    search_fields = ('username', 'email', 'first_name', 'last_name')
    ordering = ('username',)


@admin.register(Class)
class ClassAdmin(admin.ModelAdmin):
    list_display = ('name', 'school', 'form_master')
    list_filter = ('school',)
    search_fields = ('name',)
    autocomplete_fields = ['form_master']


@admin.register(Subject)
class SubjectAdmin(admin.ModelAdmin):
    list_display = ('name', 'school', 'code')
    list_filter = ('school',)
    search_fields = ('name', 'code')


@admin.register(ClassSubject)
class ClassSubjectAdmin(admin.ModelAdmin):
    list_display = ('subject', 'school_class', 'teacher')
    list_filter = ('school_class__school',)
    search_fields = ('subject__name', 'school_class__name')
    autocomplete_fields = ['subject', 'school_class', 'teacher']


@admin.register(Parent)
class GuardianAdmin(admin.ModelAdmin):
    list_display = ('user', 'phone_number', )
    search_fields = ('user', 'phone_number',)


class StudentInline(admin.TabularInline):
    model = Student
    extra = 0
    fields = ('user', 'student_class')


@admin.register(Student)
class StudentAdmin(admin.ModelAdmin):
    list_display = ('user', 'student_class', 'phone_number')
    list_filter = ('student_class__school',)
    search_fields = ('user__username', 'user__first_name', 'user__last_name', 'phone_number')
    autocomplete_fields = ['user', 'student_class', ]
    inlines = []


@admin.register(StudentPost)
class StudentPostAdmin(admin.ModelAdmin):
    list_display = ('__str__', 'school', 'created_at', 'updated_at')
    list_filter = ('school', 'created_at')
    

@admin.register(Teacher)
class TeacherAdmin(admin.ModelAdmin):
    list_display = ('user_full_name', 'email', 'school')
    search_fields = ('user__first_name', 'user__last_name', 'user__email', 'school__name')
    list_filter = ('school',)

    def user_full_name(self, obj):
        return obj.user.get_full_name()
    user_full_name.short_description = 'Name'

    def email(self, obj):
        return obj.user.email
