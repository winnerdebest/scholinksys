import random
from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import School
from stu_main.models import CustomUser

class PrincipalRegistrationForm(UserCreationForm):
    full_name = forms.CharField()
    school_name = forms.CharField()
    school_email = forms.EmailField()
    school_address = forms.CharField(widget=forms.Textarea)
    school_logo = forms.ImageField()

    class Meta:
        model = CustomUser
        fields = ['email', 'password1', 'password2'] 

    def save(self, commit=True):
        user = super().save(commit=False)
        full_name = self.cleaned_data['full_name']
        first_name, last_name = (full_name.strip().split(' ', 1) + [''])[:2]
        user.first_name = first_name
        user.last_name = last_name
        user.user_type = 'principal'
        user.username = self.generate_unique_username(first_name, last_name)

        if commit:
            user.save()
            School.objects.create(
                principal=user,
                name=self.cleaned_data['school_name'],
                email=self.cleaned_data['school_email'],
                address=self.cleaned_data['school_address'],
                logo=self.cleaned_data['school_logo']
            )
        return user

    def generate_unique_username(self, first_name, last_name):
        base = f"{first_name}{last_name}".lower().replace(" ", "")
        while True:
            username = f"{base}{random.randint(100, 999)}"
            if not CustomUser.objects.filter(username=username).exists():
                return username
            



