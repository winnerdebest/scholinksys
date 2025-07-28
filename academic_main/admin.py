from django.contrib import admin
from .models import *


admin.site.register(Term)
admin.site.register(ActiveTerm)


@admin.register(SchoolPaymentInfo)
class SchoolPaymentInfoAdmin(admin.ModelAdmin):
    list_display = ('school', 'bank_name', 'account_number', 'account_name')




@admin.register(School)
class SchoolAdmin(admin.ModelAdmin):
    list_display = ('name', 'principal', 'email')