from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from .forms import PrincipalRegistrationForm
from .models import *
from stu_main.models import *



def register_principal(request):
    if request.method == 'POST':
        form = PrincipalRegistrationForm(request.POST, request.FILES)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect('principal:principal_dashboard') 
    else:
        form = PrincipalRegistrationForm()
    return render(request, 'principal_register.html', {'form': form})


def user_login_view(request):
    if request.method == "POST":
        email = request.POST.get("email")
        password = request.POST.get("password")

        try:
            # Find the user by email
            user = CustomUser.objects.get(email=email)
            
            # Authenticate the user
            user = authenticate(request, username=user.username, password=password)

            if user is not None:
                login(request, user)
                
                # Redirect to different dashboards based on user_type
                if user.user_type == 'student':
                    return redirect('student_dashboard')
                elif user.user_type == 'teacher':
                   return redirect('teacher:teacher_dashboard')
                #elif user.user_type == 'admin':
                    #return redirect('admin_dashboard:admin_dashboard')
                elif user.user_type == 'principal':
                    return redirect('principal:principal_dashboard')
                else:
                    messages.error(request, "Invalid user type.")
                    return redirect('user_login')
            else:
                messages.error(request, "Invalid credentials. Please try again.")
        except CustomUser.DoesNotExist:
            messages.error(request, "No user found with this email.")

    return render(request, "login.html")


@login_required
def user_logout_view(request):
    logout(request)
    return redirect('user_login')


from django.core.mail import send_mail, BadHeaderError
from django.http import HttpResponse
import smtplib

def test_email(request):
    try:
        send_mail(
            subject="Test Email from Django",
            message="This is a test email sent from your Django app.",
            from_email=None,  # Uses DEFAULT_FROM_EMAIL
            recipient_list=["winnerbrown9@gmail.com"],
            fail_silently=False,
        )
        return HttpResponse("✅ Email sent successfully!")

    except BadHeaderError:
        return HttpResponse("❌ Invalid header found.")

    except smtplib.SMTPAuthenticationError as e:
        return HttpResponse(f"❌ SMTP Authentication Error: {str(e)}")

    except smtplib.SMTPException as e:
        return HttpResponse(f"❌ SMTP Error: {str(e)}")

    except Exception as e:
        return HttpResponse(f"❌ General Error: {str(e)}")




def index(request):
    return render(request, 'index.html')


