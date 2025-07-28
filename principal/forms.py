from django import forms
from stu_main.models import *
from .models import *
from academic_main.models import ActiveTerm
from django.core.validators import MinValueValidator, MaxValueValidator



class UserSettingsForm(forms.ModelForm):
    class Meta:
        model = CustomUser
        fields = ["first_name", "last_name", "email"]

class SchoolSettingsForm(forms.ModelForm):
    class Meta:
        model = School
        fields = ["name", "logo", "address", "email"]

class ClassForm(forms.ModelForm):
    class Meta:
        model = Class
        fields = ['name', 'form_master']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500 dark:bg-gray-700 dark:border-gray-600 dark:text-white dark:placeholder-gray-400',
                'placeholder': 'e.g. JS1 Red'
            }),
            'form_master': forms.Select(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500 dark:bg-gray-700 dark:border-gray-600 dark:text-white'
            })
        }

    def __init__(self, *args, **kwargs):
        self.school = kwargs.pop('school', None)
        super().__init__(*args, **kwargs)
        
        # Filter form masters to only show teachers from the current school
        if self.school:
            self.fields['form_master'].queryset = CustomUser.objects.filter(
                user_type='teacher',
                teacher__school=self.school
            ).select_related('teacher')
            self.fields['form_master'].empty_label = '-- Select Teacher --'
        
        # Add required field indicator
        self.fields['name'].label = 'Class Name'
        self.fields['form_master'].label = 'Form Master (optional)'
        self.fields['name'].required = True
        self.fields['form_master'].required = False

    def clean_name(self):
        name = self.cleaned_data.get('name')
        if self.school:
            # Check if a class with this name already exists in the school
            if Class.objects.filter(name=name, school=self.school).exclude(pk=self.instance.pk if self.instance else None).exists():
                raise forms.ValidationError('A class with this name already exists in your school.')
        return name