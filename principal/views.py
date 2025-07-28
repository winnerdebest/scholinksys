from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse, HttpResponse
from django.contrib.auth import get_user_model
from stu_main.models import *
from academic_main.decorators import role_required
from django.contrib import messages
from .forms import *
from .utils import generate_username, generate_readable_password
from django.core.paginator import Paginator
from django.contrib.auth.decorators import login_required
from django.db.models import Q, Prefetch, Sum, Count
from .models import *
from django.utils import timezone
from datetime import datetime, timedelta
from django.core.paginator import Paginator
from django.db import models
from io import BytesIO
import xlsxwriter
from reportlab.pdfgen import canvas
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle
from reportlab.lib.units import inch
import uuid
from academic_main.models import ActiveTerm
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.conf import settings
from django.db.models.functions import TruncMonth
import json
from .models import FeePayment, AdditionalFee, Term
from django.views.decorators.http import require_http_methods
from django.core.exceptions import PermissionDenied
from django.core.exceptions import ValidationError
from teacher_logic.models import GradingPolicy


User = get_user_model()


@login_required
@role_required('principal')
def principal_dashboard(request):
    user = request.user
    school = getattr(user, 'school', None)

    if not school:
        return render(request, 'principal/dashboard.html', {
            "error": "No school is associated with this account."
        })

    total_students = Student.objects.filter(student_class__school=school).count()
    total_teachers = Teacher.objects.filter(school=school).distinct().count()
    total_classes = Class.objects.filter(school=school).count()
    total_subjects = Subject.objects.filter(school=school).count()

    # Get active announcements
    announcements = Announcement.objects.filter(
        school=school,
        is_active=True
    ).exclude(
        expiry_date__lt=timezone.now()
    ).order_by('-created_at')[:5]  # Get 5 most recent announcements

    # Calculate expense analytics
    try:
        # Total expenses calculation
        total_expenses = Expense.objects.filter(school=school).aggregate(
            total=models.Sum('amount'))['total']
        total_expenses = float(total_expenses) if total_expenses is not None else 0.0

        # Current month expenses
        current_month = timezone.now().month
        current_year = timezone.now().year
        current_month_expenses = Expense.objects.filter(
            school=school,
            date__month=current_month,
            date__year=current_year
        ).aggregate(total=models.Sum('amount'))['total']
        current_month_expenses = float(current_month_expenses) if current_month_expenses is not None else 0.0

        # Previous month expenses
        previous_month = (timezone.now().replace(day=1) - timezone.timedelta(days=1)).month
        previous_month_year = current_year if current_month > 1 else current_year - 1
        previous_month_expenses = Expense.objects.filter(
            school=school,
            date__month=previous_month,
            date__year=previous_month_year
        ).aggregate(total=models.Sum('amount'))['total']
        previous_month_expenses = float(previous_month_expenses) if previous_month_expenses is not None else 0.0

        # Calculate percentage change
        if previous_month_expenses > 0:
            expense_change_percentage = ((current_month_expenses - previous_month_expenses) / previous_month_expenses) * 100
        else:
            expense_change_percentage = 100 if current_month_expenses > 0 else 0

    except Exception as e:
        print(f"Error calculating expenses: {e}")
        total_expenses = 0.0
        current_month_expenses = 0.0
        expense_change_percentage = 0.0

    # Add revenue calculations
    

    context = {
        "total_students": total_students,
        "total_teachers": total_teachers,
        "total_classes": total_classes,
        "total_subjects": total_subjects,
        "total_expenses": total_expenses,
        "current_month_expenses": current_month_expenses,
        "expense_change_percentage": expense_change_percentage,
        "announcements": announcements,
    }

    return render(request, 'principal/dashboard.html', context)



@login_required
@role_required('principal')
def create_or_update_student(request, student_id=None):
    student = None
    if student_id:
        student = get_object_or_404(Student, id=student_id, student_class__school=request.user.school)
        user = student.user

    if request.method == "POST":
        first_name = request.POST.get('first_name')
        last_name = request.POST.get('last_name')
        email = request.POST.get('email')
        phone_number = request.POST.get('phone_number')
        class_id = request.POST.get('class_id')
        photo = request.FILES.get('photo')

        if not all([first_name, last_name, email, class_id]):
            messages.error(request, "Please fill in all required fields.")
            return render(request, "students/create_student.html", {
                "student": student,
                "classes": Class.objects.filter(school=request.user.school),
                "terms": Term.objects.filter(school=request.user.school),
                "discount_types": StudentDiscount.DISCOUNT_TYPE_CHOICES,
            })

        student_class = get_object_or_404(Class, id=class_id, school=request.user.school)

        try:
            if student:  # Update existing student
                # Update user fields
                user.first_name = first_name
                user.last_name = last_name
                user.email = email
                user.save()

                # Update student profile
                student.phone_number = phone_number
                student.student_class = student_class
                if photo:
                    student.photo = photo
                student.save()

                messages.success(request, "Student updated successfully!")
                return redirect("principal:student_list")

            else:  # Create new student
                username = generate_username(first_name, last_name)
                password = generate_readable_password()

                user = User.objects.create_user(
                    username=username,
                    email=email,
                    first_name=first_name,
                    last_name=last_name,
                    password=password,
                    user_type="student"
                )

                student = Student.objects.create(
                    user=user,
                    phone_number=phone_number,
                    student_class=student_class,
                    photo=photo if photo else None,
                )

                # Handle discount
                discount_type = request.POST.get('discount_type')
                discount_value = request.POST.get('discount_value')
                academic_year = request.POST.get('academic_year')
                discount_reason = request.POST.get('discount_reason')

                if discount_type and discount_value and academic_year:
                    StudentDiscount.objects.create(
                        student=student,
                        term=ActiveTerm.get_active_term(),
                        academic_year=academic_year,
                        school_class=student_class,
                        discount_type=discount_type,
                        discount_value=discount_value,
                        reason=discount_reason,
                        is_active=True
                    )



                context = {
                    "student": student,
                    "username": username,
                    "password": password,
                }

                messages.success(request, 'Student created successfully!')
                return render(request, "students/student_success.html", context)

        except Exception as e:
            messages.error(request, f'Error creating/updating student: {str(e)}')
            return render(request, "students/create_student.html", {
                "student": student,
                "classes": Class.objects.filter(school=request.user.school),
                "terms": Term.objects.filter(school=request.user.school),
                "discount_types": StudentDiscount.DISCOUNT_TYPE_CHOICES,
            })

    # GET request
    classes = Class.objects.filter(school=request.user.school)
    terms = Term.objects.filter(school=request.user.school)
    
    return render(request, "students/create_student.html", {
        "student": student,
        "classes": classes,
        "terms": terms,
        "discount_types": StudentDiscount.DISCOUNT_TYPE_CHOICES
    })


@login_required
@role_required('principal')
def delete_student(request, student_id):
    student = get_object_or_404(Student, id=student_id, student_class__school=request.user.school)
    
    if request.method == "POST":
        try:
            # Get the user before deleting the student
            user = student.user
            
            # Delete the student record
            student.delete()
            
            # Delete the associated user account
            user.delete()
            
            messages.success(request, "Student deleted successfully!")
            return redirect("principal:student_list")
            
        except Exception as e:
            messages.error(request, f"Error deleting student: {str(e)}")
            return redirect("principal:student_detail", student_id=student_id)
    
    # If GET request, show confirmation page
    return render(request, "students/delete_student_confirm.html", {
        "student": student
    })


@login_required
@role_required('principal')
def student_list(request):
    school = request.user.school  # Ensure your User model is linked to a school

    query = request.GET.get('q', '')

    # Filter students by school via their student_class
    students = Student.objects.select_related('user', 'student_class').filter(
        student_class__school=school
    )

    if query:
        students = students.filter(
            Q(user__first_name__icontains=query) |
            Q(user__last_name__icontains=query) |
            Q(student_class__name__icontains=query)
        )

    paginator = Paginator(students, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        "students": page_obj.object_list,
        "page_obj": page_obj,
        "paginator": paginator,
        "is_paginated": page_obj.has_other_pages(),
        "query": query,
    }
    return render(request, "students/student_list.html", context)






@login_required
@role_required('principal')
def create_teacher(request):
    if request.method == "POST":
        first_name = request.POST.get('first_name')
        last_name = request.POST.get('last_name')
        email = request.POST.get('email')
        salary = request.POST.get('salary')

        if not first_name or not last_name or not email:
            messages.error(request, "Please fill in all required fields.")
            return render(request, "teachers/create_teacher.html")

        username = generate_username(first_name, last_name)
        password = generate_readable_password()

        # Create user
        user = User.objects.create_user(
            username=username,
            email=email,
            first_name=first_name,
            last_name=last_name,
            password=password,
            user_type="teacher"
        )

        # Link teacher to user's school (via principal)
        Teacher.objects.create(
            user=user,
            school=request.user.school,
            salary=salary if salary else None
        )

        context = {
            "teacher": user,
            "username": username,
            "password": password,
        }

        return render(request, "teachers/teacher_success.html", context)

    return render(request, "teachers/create_teacher.html")


@login_required
@role_required('principal')
def edit_teacher(request, pk):
    teacher = get_object_or_404(Teacher, pk=pk)
    user = teacher.user 

    if request.method == "POST":
        first_name = request.POST.get('first_name')
        last_name = request.POST.get('last_name')
        email = request.POST.get('email')
        salary = request.POST.get('salary')

        if not first_name or not last_name or not email:
            messages.error(request, "Please fill in all required fields.")
        else:
            user.first_name = first_name
            user.last_name = last_name
            user.email = email
            user.save()

            teacher.salary = salary if salary else None
            teacher.save()
            
            messages.success(request, "Teacher updated successfully.")
            return redirect("principal:teacher_list")

    return render(request, "teachers/edit_teacher.html", {"teacher": teacher})


@login_required
@role_required('principal')
def delete_teacher(request, pk):
    teacher = get_object_or_404(User, pk=pk, user_type="teacher")

    if request.method == "POST":
        teacher.delete()
        messages.success(request, "Teacher deleted successfully.")
        return redirect("principal:teacher_list")

    return render(request, "teachers/delete_teacher_confirm.html", {"teacher": teacher})


@login_required
@role_required('principal')
def teacher_list(request):
    query = request.GET.get('q', '')
    school = request.user.school

    teachers = Teacher.objects.select_related('user', 'school').prefetch_related(
        'class_subjects__subject'
    ).filter(school=school)

    if query:
        teachers = teachers.filter(
            Q(user__first_name__icontains=query) |
            Q(user__last_name__icontains=query) |
            Q(user__email__icontains=query)
        )

    # Calculate total salaries
    total_salaries = teachers.filter(salary__isnull=False).aggregate(
        total=models.Sum('salary')
    )['total'] or 0

    paginator = Paginator(teachers, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        "teachers": page_obj.object_list,
        "page_obj": page_obj,
        "paginator": paginator,
        "is_paginated": page_obj.has_other_pages(),
        "query": query,
        "total_salaries": total_salaries,
    }
    return render(request, "teachers/teacher_list.html", context)




@login_required
@role_required('principal')
def class_list(request):
    school = request.user.school
    classes = Class.objects.filter(school=school).prefetch_related('class_fees')
    return render(request, "classes/class_list.html", {"classes": classes})



@login_required
@role_required('principal')
def create_or_update_class(request, class_id=None):
    is_update = class_id is not None
    school = request.user.school

    school_class = get_object_or_404(Class, id=class_id, school=school) if is_update else None

    if request.method == 'POST':
        name = request.POST.get('name')
        form_master_id = request.POST.get('form_master')

        fee_amounts = request.POST.getlist('fee_amount[]')

        if not name:
            messages.error(request, "Class name is required.")
            return render(request, "classes/create_class.html")

        try:
            # Prevent duplicate class names (on create only)
            if not is_update and Class.objects.filter(name=name, school=school).exists():
                messages.error(request, "A class with this name already exists in your school.")
                return render(request, "classes/create_class.html")

            # Create or update the class
            if is_update:
                school_class.name = name
                school_class.form_master_id = form_master_id if form_master_id else None
                school_class.save()
                # Clear existing fees
                school_class.class_fees.all().delete()
            else:
                school_class = Class.objects.create(
                    name=name,
                    school=school,
                    form_master_id=form_master_id if form_master_id else None
                )

            # Add new class fees
            for amount in fee_amounts:
                if amount:
                    ClassFee.objects.create(
                        school_class=school_class,
                        amount=amount
                    )

            messages.success(request, f"Class {'updated' if is_update else 'created'} successfully!")
            return redirect('principal:class_list')

        except Exception as e:
            messages.error(request, f"Error {'updating' if is_update else 'creating'} class: {str(e)}")
            return render(request, "classes/create_class.html")

    # GET request
    teachers = CustomUser.objects.filter(
        user_type='teacher',
        teacher__school=school
    ).select_related('teacher')

    # Get existing fee amounts for edit
    existing_fees = school_class.class_fees.all() if is_update else []

    return render(request, 'classes/create_class.html', {
        'teachers': teachers,
        'school_class': school_class,
        'existing_fees': existing_fees,
        'is_update': is_update,
    })



@login_required
@role_required('principal')
def delete_class(request, class_id):
    class_instance = get_object_or_404(Class, id=class_id)
    
    if request.method == "POST":
        class_instance.delete()
        messages.success(request, "Class deleted successfully.")
        return redirect("class_list")

    return render(request, "classes/delete_class.html", {"class_instance": class_instance})


@login_required
@role_required('principal')
def class_detail(request, class_id):
    school_class = get_object_or_404(Class, id=class_id)
    class_subjects = ClassSubject.objects.select_related("subject", "teacher").filter(school_class=school_class)

    return render(request, "classes/class_detail.html", {
        "class": school_class,
        "class_subjects": class_subjects
    })


@login_required
@role_required('principal')
def assign_subject_to_class(request, class_id):
    school = request.user.school
    school_class = get_object_or_404(Class, id=class_id, school=school)

    teachers = Teacher.objects.select_related("user").filter(school=school)
    subjects = Subject.objects.filter(school=school)

    if request.method == "POST":
        subject_id = request.POST.get("subject")
        teacher_id = request.POST.get("teacher_id")  

        if not subject_id or not teacher_id:
            messages.error(request, "Please select both a subject and a teacher.")
            return redirect("principal:assign_subject", class_id=class_id)

        subject = get_object_or_404(Subject, id=subject_id, school=school)
        teacher_instance = get_object_or_404(Teacher, id=teacher_id, school=school)
        #teacher_user = teacher_instance.user  # Get CustomUser from Teacher

        if ClassSubject.objects.filter(subject=subject, school_class=school_class).exists():
            messages.warning(request, f"{subject.name} is already assigned to this class.")
        else:
            ClassSubject.objects.create(subject=subject, school_class=school_class, teacher=teacher_instance)
            messages.success(request, f"{subject.name} assigned to {school_class.name}.")

        return redirect("principal:class_detail", class_id=class_id)

    return render(request, "classes/assign_subject.html", {
        "school_class": school_class,
        "subjects": subjects,
        "teachers": teachers
    })




@login_required
@role_required('principal')
def edit_class_subject(request, classsubject_id):
    class_subject = get_object_or_404(ClassSubject, id=classsubject_id)
    teachers = Teacher.objects.select_related("user").filter(school=request.user.school)

    if request.method == "POST":
        teacher_id = request.POST.get("teacher")
        if not teacher_id:
            messages.error(request, "Please select a teacher.")
        else:
            teacher = get_object_or_404(Teacher, user__id=teacher_id, school=request.user.school)
            class_subject.teacher = teacher  
            class_subject.save()
            messages.success(request, f"{class_subject.subject.name} teacher updated.")
            return redirect("principal:class_detail", class_id=class_subject.school_class.id)

    return render(request, "classes/edit_class_subject.html", {
        "class_subject": class_subject,
        "teachers": teachers
    })



@login_required
@role_required('principal')
def delete_class_subject(request, classsubject_id):
    class_subject = get_object_or_404(ClassSubject, id=classsubject_id)
    class_id = class_subject.school_class.id

    if request.method == "POST":
        class_subject.delete()
        messages.success(request, "Subject assignment deleted.")
        return redirect("principal:class_detail", class_id=class_id)

    return render(request, "classes/delete_class_subject.html", {
        "class_subject": class_subject
    })


@login_required
@role_required('principal')
def subject_list(request):
    school = request.user.school
    subjects = Subject.objects.filter(school=school)
    return render(request, "principal/subject_list.html", {"subjects": subjects})


@login_required
@role_required('principal')
def create_subject(request):
    school = request.user.school

    if request.method == "POST":
        name = request.POST.get("name")
        code = request.POST.get("code")
        description = request.POST.get("description")

        if not name:
            messages.error(request, "Subject name is required.")
            return render(request, "principal/create_or_edit_subject.html", {
                "name": name,
                "code": code,
                "description": description
            })

        Subject.objects.create(
            name=name,
            code=code,
            description=description,
            school=school  
        )
        messages.success(request, "Subject created successfully.")
        return redirect("principal:subject_list")

    return render(request, "principal/create_or_edit_subject.html")

@login_required
@role_required('principal')
def edit_subject(request, subject_id):
    subject = get_object_or_404(Subject, id=subject_id)

    if request.method == "POST":
        subject.name = request.POST.get("name")
        subject.code = request.POST.get("code")
        subject.description = request.POST.get("description")
        subject.save()
        messages.success(request, "Subject updated successfully.")
        return redirect("principal:subject_list")

    return render(request, "principal/create_or_edit_subject.html", {"subject": subject})


@login_required
@role_required('principal')
def delete_subject(request, subject_id):
    subject = get_object_or_404(Subject, id=subject_id)
    subject.delete()
    messages.success(request, "Subject deleted successfully.")
    return redirect("principal:subject_list")





@login_required
@role_required('principal')
def customize_grade_weights(request):
    try:
        policy = GradingPolicy.objects.get(school=request.user.school)
    except GradingPolicy.DoesNotExist:
        policy = None

    if request.method == 'POST':
        # Get values from form
        internal_exam = float(request.POST.get('internalExam', 0))
        external_exam = float(request.POST.get('externalExam', 0))
        internal_assignment = float(request.POST.get('internalAssignment', 0))
        external_assignment = float(request.POST.get('externalAssignment', 0))
        test_weight = float(request.POST.get('testWeight', 0))

        # Calculate total weights
        exam_weight = internal_exam + external_exam
        assignment_weight = internal_assignment + external_assignment

        # Calculate internal ratios
        exam_internal_ratio = (internal_exam / exam_weight * 100) if exam_weight > 0 else 50
        assignment_internal_ratio = (internal_assignment / assignment_weight * 100) if assignment_weight > 0 else 50

        try:
            if policy is None:
                policy = GradingPolicy(school=request.user.principal.school)

            policy.exam_weight = exam_weight
            policy.assignment_weight = assignment_weight
            policy.test_weight = test_weight
            policy.exam_internal_ratio = exam_internal_ratio
            policy.assignment_internal_ratio = assignment_internal_ratio
            policy.save()

            messages.success(request, 'Grading policy updated successfully.')
            return redirect('principal:customize_grade')

        except ValidationError as e:
            messages.error(request, str(e))
            return redirect('principal:customize_grade')

    # For GET request, prepare initial data
    context = {}
    if policy:
        exam_internal = (policy.exam_weight * policy.exam_internal_ratio) / 100
        exam_external = (policy.exam_weight * (100 - policy.exam_internal_ratio)) / 100
        assignment_internal = (policy.assignment_weight * policy.assignment_internal_ratio) / 100
        assignment_external = (policy.assignment_weight * (100 - policy.assignment_internal_ratio)) / 100

        context = {
            'internal_exam': exam_internal,
            'external_exam': exam_external,
            'internal_assignment': assignment_internal,
            'external_assignment': assignment_external,
            'test_weight': policy.test_weight
        }

    return render(request, 'principal/customize_grade.html', context)




@login_required
@role_required("principal")
def settings_view(request):
    user = request.user
    try:
        school = user.school
    except School.DoesNotExist:
        messages.error(request, "School settings not found.")
        return redirect("dashboard")

    if request.method == "POST":
        user_form = UserSettingsForm(request.POST, instance=user)
        school_form = SchoolSettingsForm(request.POST, request.FILES, instance=school)

        if user_form.is_valid() and school_form.is_valid():
            user_form.save()
            school_form.save()
            messages.success(request, "Settings updated successfully.")
            return redirect("principal:settings")
    else:
        user_form = UserSettingsForm(instance=user)
        school_form = SchoolSettingsForm(instance=school)

    return render(request, "settings/settings.html", {
        "user_form": user_form,
        "school_form": school_form
    })




# Imports for this view I didnt add it at the top because its like on thousand lines at the top
import requests
from django.views import View
from django.urls import reverse
from academic_main.utils import create_flutterwave_subaccount, get_flutterwave_banks

#Class based view for creating, updating and deleting Payment Info Creation
class PaymentInfoCreateUpdateView(View):
    def get(self, request):
        school = request.user.school
        banks = get_flutterwave_banks()
        payment_info = SchoolPaymentInfo.objects.filter(school=school).first()

        return render(request, "settings/payment_info.html", {
            "banks": banks,
            "payment_info": payment_info
        })

    def post(self, request):
        school = request.user.school
        data = request.POST

        payment_info = SchoolPaymentInfo.objects.filter(school=school).first()

        if payment_info:
            # Update existing record
            payment_info.account_name = data["account_name"]
            payment_info.account_number = data["account_number"]
            payment_info.bank_name = data["bank_name"]
            payment_info.bank_code = data["bank_code"]
            payment_info.split_percentage = int(data.get("split_percentage", 98))
            payment_info.save()

            messages.success(request, "Payment info updated successfully.")
            return redirect("principal:paymentinfo-create", pk=payment_info.pk)

        else:
            # Create new record + Flutterwave subaccount
            try:
                subaccount = create_flutterwave_subaccount(
                    account_name=data["account_name"],
                    account_number=data["account_number"],
                    bank_code=data["bank_code"],
                    split_percentage=int(data.get("split_percentage", 98)),
                    school=school,
                )
            except requests.exceptions.HTTPError as e:
                try:
                    error_response = e.response.json()
                    flutterwave_message = error_response.get("message", str(e))
                except Exception:
                    flutterwave_message = str(e)

                messages.error(request, f"Flutterwave Error: {flutterwave_message}")
                return redirect("principal:paymentinfo-create")


            payment_info = SchoolPaymentInfo.objects.create(
                school=school,
                provider="flutterwave",
                account_name=data["account_name"],
                account_number=data["account_number"],
                bank_name=data["bank_name"],
                bank_code=data["bank_code"],
                flutterwave_subaccount_id=subaccount["id"],
                split_percentage=98,
                is_active=True,
            )
            messages.success(request, "Payment info added successfully.")
            return redirect("paymentinfo-detail", pk=payment_info.pk)




class PaymentInfoDeleteView(View):
    def post(self, request, pk):
        payment_info = get_object_or_404(SchoolPaymentInfo, pk=pk)
        payment_info.delete()
        messages.success(request, "Payment info deleted.")
        return redirect("school-dashboard")




@login_required
@role_required('principal')
def expense_list(request):
    school = request.user.school
    category_filter = request.GET.get('category')
    month_filter = request.GET.get('month')

    # Base queryset for all expenses
    expenses = Expense.objects.filter(school=school).select_related('category')
    all_expenses = expenses  # Keep an unfiltered copy for totals

    # Apply filters for display only
    if category_filter and category_filter != 'all':
        expenses = expenses.filter(category__id=category_filter)
    
    if month_filter:
        try:
            year, month = map(int, month_filter.split('-'))
            expenses = expenses.filter(date__year=year, date__month=month)
        except (ValueError, TypeError):
            pass

    # Calculate totals from unfiltered queryset
    total_expenses = all_expenses.aggregate(total=models.Sum('amount'))['total'] or 0
    teacher_salaries = all_expenses.filter(category__name='Teacher Salary').aggregate(
        total=models.Sum('amount'))['total'] or 0
    other_expenses = total_expenses - teacher_salaries

    # Calculate pending salaries
    pending_payments = TeacherSalaryPayment.objects.filter(
        teacher__school=school,
        expense__payment_status='pending'
    )
    pending_salaries = sum(payment.net_salary for payment in pending_payments)

    # Get all expense categories for the filter dropdown
    categories = ExpenseCategory.objects.filter(school=school)

    # Paginate the filtered expenses
    paginator = Paginator(expenses, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'expenses': page_obj,
        'categories': categories,
        'total_expenses': total_expenses,
        'teacher_salaries': teacher_salaries,
        'other_expenses': other_expenses,
        'pending_salaries': pending_salaries,
        'selected_category': category_filter,
        'selected_month': month_filter,
        'is_paginated': page_obj.has_other_pages(),
        'page_obj': page_obj,
        'paginator': paginator,
    }

    return render(request, "principal/expenses.html", context)

@login_required
@role_required('principal')
def create_expense(request):
    school = request.user.school

    if request.method == "POST":
        category_choice = request.POST.get('category_choice')
        amount = request.POST.get('amount')
        description = request.POST.get('description')
        date = request.POST.get('date')
        payment_status = request.POST.get('payment_status')
        payment_date = request.POST.get('payment_date') or None
        receipt = request.FILES.get('receipt')

        try:
            # Handle category (existing or new)
            if category_choice == 'new':
                new_category_name = request.POST.get('new_category_name')
                new_category_description = request.POST.get('new_category_description')
                
                if not new_category_name:
                    raise ValueError("Category name is required when creating a new category")
                
                # Create new category
                category = ExpenseCategory.objects.create(
                    name=new_category_name,
                    description=new_category_description,
                    school=school
                )
            else:
                category_id = request.POST.get('category')
                category = ExpenseCategory.objects.get(id=category_id, school=school)

            # Create the expense
            expense = Expense.objects.create(
                school=school,
                category=category,
                amount=amount,
                description=description,
                date=date,
                payment_status=payment_status,
                payment_date=payment_date,
                receipt=receipt
            )
            messages.success(request, "Expense created successfully.")
            return redirect('principal:expense_list')
        except ExpenseCategory.DoesNotExist:
            messages.error(request, "Selected category does not exist.")
        except ValueError as e:
            messages.error(request, str(e))
        except Exception as e:
            messages.error(request, f"Error creating expense: {str(e)}")

    categories = ExpenseCategory.objects.filter(school=school)
    return render(request, "principal/create_edit_expense.html", {
        'categories': categories,
        'payment_status_choices': Expense.PAYMENT_STATUS,
    })

@login_required
@role_required('principal')
def edit_expense(request, expense_id):
    school = request.user.school
    expense = get_object_or_404(Expense, id=expense_id, school=school)

    if request.method == "POST":
        category_id = request.POST.get('category')
        amount = request.POST.get('amount')
        description = request.POST.get('description')
        date = request.POST.get('date')
        payment_status = request.POST.get('payment_status')
        payment_date = request.POST.get('payment_date') or None
        receipt = request.FILES.get('receipt')

        try:
            category = ExpenseCategory.objects.get(id=category_id, school=school)
            expense.category = category
            expense.amount = amount
            expense.description = description
            expense.date = date
            expense.payment_status = payment_status
            expense.payment_date = payment_date
            if receipt:
                expense.receipt = receipt
            expense.save()
            messages.success(request, "Expense updated successfully.")
            return redirect('principal:expense_list')
        except (ExpenseCategory.DoesNotExist, ValueError) as e:
            messages.error(request, f"Error updating expense: {str(e)}")

    categories = ExpenseCategory.objects.filter(school=school)
    return render(request, "principal/create_edit_expense.html", {
        'expense': expense,
        'categories': categories,
        'payment_status_choices': Expense.PAYMENT_STATUS,
    })

@login_required
@role_required('principal')
def delete_expense(request, expense_id):
    expense = get_object_or_404(Expense, id=expense_id, school=request.user.school)
    
    if request.method == "POST":
        expense.delete()
        messages.success(request, "Expense deleted successfully.")
        return redirect('principal:expense_list')

    return render(request, "principal/delete_expense_confirm.html", {
        'expense': expense
    })

@login_required
@role_required('principal')
def teacher_salaries(request):
    school = request.user.school
    month_filter = request.GET.get('month')
    status_filter = request.GET.get('status')

    # Get all teachers with their latest salary payments
    teachers = Teacher.objects.filter(school=school).select_related('user')

    if month_filter:
        year, month = map(int, month_filter.split('-'))
        for teacher in teachers:
            teacher.current_month_payment = TeacherSalaryPayment.objects.filter(
                teacher=teacher,
                month__year=year,
                month__month=month
            ).first()
    else:
        # Default to current month
        current_date = timezone.now()
        for teacher in teachers:
            teacher.current_month_payment = TeacherSalaryPayment.objects.filter(
                teacher=teacher,
                month__year=current_date.year,
                month__month=current_date.month
            ).first()

    if status_filter:
        teachers = [t for t in teachers if (
            t.current_month_payment and 
            t.current_month_payment.expense.payment_status == status_filter
        )]

    paginator = Paginator(teachers, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'teachers': page_obj,
        'selected_month': month_filter,
        'status': status_filter,
        'is_paginated': page_obj.has_other_pages(),
        'page_obj': page_obj,
        'paginator': paginator,
    }

    return render(request, 'principal/teacher_salary_payment.html', context)


@login_required
@role_required('principal')
def update_salary_payment(request, teacher_id):
    school = request.user.school
    teacher = get_object_or_404(Teacher, id=teacher_id, school=school)
    
    # Get or initialize salary payment
    month = request.GET.get('month', timezone.now().strftime('%Y-%m'))
    year, month = map(int, month.split('-'))
    
    try:
        salary_payment = TeacherSalaryPayment.objects.get(
            teacher=teacher,
            month__year=year,
            month__month=month
        )
    except TeacherSalaryPayment.DoesNotExist:
        salary_payment = None

    if request.method == "POST":
        try:
            basic_salary = float(request.POST.get('basic_salary'))
            allowances = float(request.POST.get('allowances', 0))
            deductions = float(request.POST.get('deductions', 0))
            payment_status = request.POST.get('payment_status')
            payment_date = request.POST.get('payment_date')
            comments = request.POST.get('comments')
            month = request.POST.get('month')

            if not salary_payment:
                salary_payment = TeacherSalaryPayment(teacher=teacher)

            salary_payment.basic_salary = basic_salary
            salary_payment.allowances = allowances
            salary_payment.deductions = deductions
            salary_payment.comments = comments
            salary_payment.month = datetime.strptime(month, '%Y-%m').date()
            
            # Save salary payment first to create/update associated expense
            salary_payment.save()
            
            # Update expense payment status and date
            salary_payment.expense.payment_status = payment_status
            if payment_date:
                salary_payment.expense.payment_date = payment_date
            salary_payment.expense.save()

            messages.success(request, "Salary payment updated successfully.")
            return redirect('principal:teacher_salaries')

        except (ValueError, TypeError) as e:
            messages.error(request, f"Error updating salary payment: {str(e)}")

    context = {
        'teacher': teacher,
        'salary_payment': salary_payment,
        'payment_status_choices': Expense.PAYMENT_STATUS,
    }
    return render(request, 'principal/update_salary_payment.html', context)


@login_required
@role_required('principal')
def process_bulk_payment(request):
    if request.method != "POST":
        return redirect('principal:teacher_salaries')

    school = request.user.school
    selected_teachers = request.POST.get('selected_teachers', '').split(',')
    payment_date = request.POST.get('payment_date')
    comments = request.POST.get('comments')

    try:
        teachers = Teacher.objects.filter(id__in=selected_teachers, school=school)
        current_date = timezone.now()
        
        for teacher in teachers:
            try:
                salary_payment = TeacherSalaryPayment.objects.get(
                    teacher=teacher,
                    month__year=current_date.year,
                    month__month=current_date.month
                )
                
                # Update payment status and date
                salary_payment.expense.payment_status = 'paid'
                salary_payment.expense.payment_date = payment_date
                salary_payment.comments = comments
                salary_payment.expense.save()
                salary_payment.save()
                
            except TeacherSalaryPayment.DoesNotExist:
                # Create new salary payment if it doesn't exist
                salary_payment = TeacherSalaryPayment.objects.create(
                    teacher=teacher,
                    basic_salary=teacher.salary,
                    month=current_date,
                    comments=comments
                )
                salary_payment.expense.payment_status = 'paid'
                salary_payment.expense.payment_date = payment_date
                salary_payment.expense.save()

        messages.success(request, f"Successfully processed payments for {len(teachers)} teachers.")
    except Exception as e:
        messages.error(request, f"Error processing bulk payments: {str(e)}")

    return redirect('principal:teacher_salaries')

@login_required
@role_required('principal')
def export_expenses_excel(request):
    school = request.user.school
    category_filter = request.GET.get('category')
    month_filter = request.GET.get('month')
    
    expenses = Expense.objects.filter(school=school).select_related('category')
    
    if category_filter and category_filter != 'all':
        expenses = expenses.filter(category__id=category_filter)
    
    if month_filter:
        try:
            year, month = map(int, month_filter.split('-'))
            expenses = expenses.filter(date__year=year, date__month=month)
        except (ValueError, TypeError):
            pass

    # Create Excel file
    output = BytesIO()
    workbook = xlsxwriter.Workbook(output)
    worksheet = workbook.add_worksheet()

    # Add headers
    headers = ['Date', 'Category', 'Description', 'Amount (₦)', 'Status']
    header_format = workbook.add_format({'bold': True, 'bg_color': '#f0f0f0'})
    
    for col, header in enumerate(headers):
        worksheet.write(0, col, header, header_format)

    # Add expense data
    for row, expense in enumerate(expenses, start=1):
        worksheet.write(row, 0, expense.date.strftime('%Y-%m-%d'))
        worksheet.write(row, 1, expense.category.name if expense.category else 'Uncategorized')
        worksheet.write(row, 2, expense.description)
        worksheet.write(row, 3, float(expense.amount))
        worksheet.write(row, 4, expense.get_payment_status_display())

    # Add totals
    total_row = len(expenses) + 2
    worksheet.write(total_row, 2, 'Total:', header_format)
    worksheet.write(total_row, 3, f'=SUM(D2:D{total_row})', workbook.add_format({'bold': True}))

    # Set column widths
    worksheet.set_column('A:A', 12)  # Date
    worksheet.set_column('B:B', 20)  # Category
    worksheet.set_column('C:C', 40)  # Description
    worksheet.set_column('D:D', 15)  # Amount
    worksheet.set_column('E:E', 12)  # Status

    workbook.close()
    output.seek(0)

    # Generate filename with timestamp
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    filename = f'expenses_{timestamp}.xlsx'

    response = HttpResponse(
        output.read(),
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    return response

@login_required
@role_required('principal')
def export_expenses_pdf(request):
    school = request.user.school
    category_filter = request.GET.get('category')
    month_filter = request.GET.get('month')
    
    expenses = Expense.objects.filter(school=school).select_related('category')
    
    if category_filter and category_filter != 'all':
        expenses = expenses.filter(category__id=category_filter)
    
    if month_filter:
        try:
            year, month = map(int, month_filter.split('-'))
            expenses = expenses.filter(date__year=year, date__month=month)
        except (ValueError, TypeError):
            pass

    # Create PDF
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter)
    elements = []

    # Create the expense table data
    data = [['Date', 'Category', 'Description', 'Amount (₦)', 'Status']]
    
    for expense in expenses:
        data.append([
            expense.date.strftime('%Y-%m-%d'),
            expense.category.name if expense.category else 'Uncategorized',
            expense.description,
            f"₦{expense.amount:,.2f}",
            expense.get_payment_status_display()
        ])

    # Calculate totals
    total_amount = sum(expense.amount for expense in expenses)
    data.append(['', '', 'Total:', f"₦{total_amount:,.2f}", ''])

    # Create the table
    table = Table(data)
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 14),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, -1), (-1, -1), colors.grey),
        ('TEXTCOLOR', (0, -1), (-1, -1), colors.whitesmoke),
        ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, -1), (-1, -1), 12),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('ALIGN', (3, 1), (3, -1), 'RIGHT'),
    ]))

    elements.append(table)
    doc.build(elements)

    buffer.seek(0)
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    filename = f'expenses_{timestamp}.pdf'

    response = HttpResponse(buffer.read(), content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    return response

@login_required
@role_required('principal')
def create_announcement(request):
    if request.method == "POST":
        title = request.POST.get('title')
        content = request.POST.get('content')
        priority = request.POST.get('priority')
        expiry_date = request.POST.get('expiry_date')

        try:
            announcement = Announcement.objects.create(
                school=request.user.school,
                title=title,
                content=content,
                created_by=request.user,
                priority=priority,
                expiry_date=expiry_date if expiry_date else None
            )
            messages.success(request, "Announcement created successfully.")
            return redirect('principal:principal_dashboard')
        except Exception as e:
            messages.error(request, f"Error creating announcement: {str(e)}")

    return render(request, 'principal/create_announcement.html', {
        'priority_choices': Announcement.PRIORITY_CHOICES
    })

@login_required
@role_required('principal')
def edit_announcement(request, pk):
    announcement = get_object_or_404(Announcement, pk=pk, school=request.user.school)
    
    if request.method == "POST":
        announcement.title = request.POST.get('title')
        announcement.content = request.POST.get('content')
        announcement.priority = request.POST.get('priority')
        announcement.expiry_date = request.POST.get('expiry_date') or None
        announcement.is_active = request.POST.get('is_active') == 'on'
        
        try:
            announcement.save()
            messages.success(request, "Announcement updated successfully.")
            return redirect('principal:principal_dashboard')
        except Exception as e:
            messages.error(request, f"Error updating announcement: {str(e)}")

    return render(request, 'principal/edit_announcement.html', {
        'announcement': announcement,
        'priority_choices': Announcement.PRIORITY_CHOICES
    })

@login_required
@role_required('principal')
def delete_announcement(request, pk):
    announcement = get_object_or_404(Announcement, pk=pk, school=request.user.school)
    
    if request.method == "POST":
        announcement.delete()
        messages.success(request, "Announcement deleted successfully.")
        return redirect('principal:principal_dashboard')

    return render(request, 'principal/delete_announcement_confirm.html', {
        'announcement': announcement
    })







@login_required
@role_required('principal')
def fee_categories(request):
    school = request.user.school
    categories = FeeCategory.objects.filter(school=school)
    
    if request.method == "POST":
        name = request.POST.get('name')
        amount = request.POST.get('amount')
        description = request.POST.get('description')
        is_recurring = request.POST.get('is_recurring') == 'on'
        due_date = request.POST.get('due_date')

        try:
            FeeCategory.objects.create(
                school=school,
                name=name,
                amount=amount,
                description=description,
                is_recurring=is_recurring,
                due_date=due_date if due_date else None
            )
            messages.success(request, "Fee category created successfully.")
            return redirect('principal:fee_categories')
        except Exception as e:
            messages.error(request, f"Error creating fee category: {str(e)}")

    return render(request, 'principal/fee_categories.html', {'categories': categories})




@login_required
@role_required('principal')
def class_fees(request):
    school = request.user.school
    selected_class = request.GET.get('class')
    selected_category = request.GET.get('category')
    selected_term = request.GET.get('term')
    selected_year = request.GET.get('academic_year')

    # Base queryset
    class_fees = ClassFee.objects.filter(school_class__school=school).select_related(
        'school_class', 'fee_category', 'term'
    )

    # Apply filters
    if selected_class:
        class_fees = class_fees.filter(school_class_id=selected_class)
    if selected_category:
        class_fees = class_fees.filter(fee_category_id=selected_category)
    if selected_term:
        class_fees = class_fees.filter(term_id=selected_term)
    if selected_year:
        class_fees = class_fees.filter(academic_year=selected_year)

    if request.method == "POST":
        school_class_id = request.POST.get('school_class')
        fee_category_id = request.POST.get('fee_category')
        amount = request.POST.get('amount')
        due_date = request.POST.get('due_date')
        term_id = request.POST.get('term')
        academic_year = request.POST.get('academic_year')

        try:
            class_fee = ClassFee.objects.create(
                school_class_id=school_class_id,
                fee_category_id=fee_category_id,
                amount=amount,
                due_date=due_date,
                term_id=term_id,
                academic_year=academic_year
            )
            messages.success(request, "Class fee created successfully.")
            return redirect('principal:class_fees')
        except Exception as e:
            messages.error(request, f"Error creating class fee: {str(e)}")

    # Get data for dropdowns
    classes = Class.objects.filter(school=school)
    fee_categories = FeeCategory.objects.filter(school=school)
    terms = Term.objects.filter(school=school)
    academic_years = class_fees.values_list('academic_year', flat=True).distinct()

    context = {
        'class_fees': class_fees,
        'classes': classes,
        'fee_categories': fee_categories,
        'terms': terms,
        'academic_years': academic_years,
        'selected_class': selected_class,
        'selected_category': selected_category,
        'selected_term': selected_term,
        'selected_year': selected_year,
    }

    return render(request, 'principal/class_fees.html', context)

@login_required
@role_required('principal')
def edit_class_fee(request, fee_id):
    school = request.user.school
    class_fee = get_object_or_404(ClassFee, id=fee_id, school_class__school=school)

    if request.method == "POST":
        try:
            class_fee.school_class_id = request.POST.get('school_class')
            class_fee.fee_category_id = request.POST.get('fee_category')
            class_fee.amount = request.POST.get('amount')
            class_fee.due_date = request.POST.get('due_date')
            class_fee.term_id = request.POST.get('term')
            class_fee.academic_year = request.POST.get('academic_year')
            class_fee.save()
            messages.success(request, "Class fee updated successfully.")
            return redirect('principal:class_fees')
        except Exception as e:
            messages.error(request, f"Error updating class fee: {str(e)}")

    return JsonResponse({'id': class_fee.id, 'data': {
        'school_class': class_fee.school_class_id,
        'fee_category': class_fee.fee_category_id,
        'amount': float(class_fee.amount),
        'due_date': class_fee.due_date.isoformat(),
        'term': class_fee.term_id,
        'academic_year': class_fee.academic_year,
    }})

@login_required
@role_required('principal')
def delete_class_fee(request, fee_id):
    class_fee = get_object_or_404(ClassFee, id=fee_id, school_class__school=request.user.school)
    
    if request.method == "POST":
        class_fee.delete()
        messages.success(request, "Class fee deleted successfully.")
    
    return redirect('principal:class_fees')

"""@login_required
@role_required('principal')
def student_discounts(request):
    school = request.user.school
    selected_student = request.GET.get('student')
    selected_category = request.GET.get('category')
    selected_term = request.GET.get('term')
    status = request.GET.get('status')

    # Base queryset
    discounts = StudentDiscount.objects.filter(
        student__student_class__school=school
    ).select_related('student', 'student__user', 'student__student_class', 'fee_category', 'term')

    # Apply filters
    if selected_student:
        discounts = discounts.filter(student_id=selected_student)
    if selected_category:
        discounts = discounts.filter(fee_category_id=selected_category)
    if selected_term:
        discounts = discounts.filter(term_id=selected_term)
    if status:
        discounts = discounts.filter(is_active=status == 'active')

    if request.method == "POST":
        student_id = request.POST.get('student')
        fee_category_id = request.POST.get('fee_category')
        discount_type = request.POST.get('discount_type')
        discount_value = request.POST.get('discount_value')
        term_id = request.POST.get('term')
        academic_year = request.POST.get('academic_year')
        reason = request.POST.get('reason')
        is_active = request.POST.get('is_active') == 'on'

        try:
            discount = StudentDiscount.objects.create(
                student_id=student_id,
                fee_category_id=fee_category_id,
                discount_type=discount_type,
                discount_value=discount_value,
                term_id=term_id,
                academic_year=academic_year,
                reason=reason,
                is_active=is_active
            )
            messages.success(request, "Student discount created successfully.")
            return redirect('principal:student_discounts')
        except Exception as e:
            messages.error(request, f"Error creating student discount: {str(e)}")

    # Get data for dropdowns
    students = Student.objects.filter(student_class__school=school).select_related('user', 'student_class')
    #fee_categories = FeeCategory.objects.filter(school=school)
    terms = Term.objects.filter(school=school)

    context = {
        'discounts': discounts,
        'students': students,
        'fee_categories': fee_categories,
        'terms': terms,
        'selected_student': selected_student,
        'selected_category': selected_category,
        'selected_term': selected_term,
        'status': status,
    }

    return render(request, 'principal/student_discounts.html', context)"""

@login_required
@role_required('principal')
def edit_student_discount(request, discount_id):
    school = request.user.school
    discount = get_object_or_404(StudentDiscount, id=discount_id, student__student_class__school=school)

    if request.method == "POST":
        try:
            discount.student_id = request.POST.get('student')
            discount.fee_category_id = request.POST.get('fee_category')
            discount.discount_type = request.POST.get('discount_type')
            discount.discount_value = request.POST.get('discount_value')
            discount.term_id = request.POST.get('term')
            discount.academic_year = request.POST.get('academic_year')
            discount.reason = request.POST.get('reason')
            discount.is_active = request.POST.get('is_active') == 'on'
            discount.save()
            messages.success(request, "Student discount updated successfully.")
            return redirect('principal:student_discounts')
        except Exception as e:
            messages.error(request, f"Error updating student discount: {str(e)}")

    return JsonResponse({'id': discount.id, 'data': {
        'student': discount.student_id,
        'fee_category': discount.fee_category_id,
        'discount_type': discount.discount_type,
        'discount_value': float(discount.discount_value),
        'term': discount.term_id,
        'academic_year': discount.academic_year,
        'reason': discount.reason,
        'is_active': discount.is_active,
    }})

@login_required
@role_required('principal')
def delete_student_discount(request, discount_id):
    discount = get_object_or_404(StudentDiscount, id=discount_id, student__student_class__school=request.user.school)
    
    if request.method == "POST":
        discount.delete()
        messages.success(request, "Student discount deleted successfully.")
    
    return redirect('principal:student_discounts')

@login_required
def manage_class_fees(request):
    # Get the active term
    active_term = ActiveTerm.get_active_term()
    
    # Get all fee categories for the school
    fee_categories = FeeCategory.objects.filter(school=request.user.school)
    
    # Get all classes for the school
    classes = Class.objects.filter(school=request.user.school)
    
    if request.method == 'POST':
        fee_category_id = request.POST.get('fee_category')
        class_id = request.POST.get('class')
        amount = request.POST.get('amount')
        due_date = request.POST.get('due_date')
        
        try:
            fee_category = FeeCategory.objects.get(id=fee_category_id)
            school_class = Class.objects.get(id=class_id)
            
            # Create or update class fee
            ClassFee.objects.update_or_create(
                school_class=school_class,
                fee_category=fee_category,
                term=active_term,
                academic_year=active_term.school.academic_year,
                defaults={
                    'amount': amount,
                    'due_date': due_date
                }
            )
            
            messages.success(request, 'Fee assigned successfully!')
        except Exception as e:
            messages.error(request, f'Error assigning fee: {str(e)}')
            
        return redirect('manage_class_fees')
    
    # Get existing class fees for the active term
    class_fees = ClassFee.objects.filter(
        term=active_term,
        school_class__school=request.user.school
    ).select_related('school_class', 'fee_category')
    
    context = {
        'fee_categories': fee_categories,
        'classes': classes,
        'class_fees': class_fees,
        'active_term': active_term
    }
    
    return render(request, 'principal/manage_class_fees.html', context)

@login_required
def view_class_fees(request, class_id):
    active_term = ActiveTerm.get_active_term()
    school_class = get_object_or_404(Class, id=class_id, school=request.user.school)
    
    class_fees = ClassFee.objects.filter(
        school_class=school_class,
        term=active_term
    ).select_related('fee_category')
    
    # Get total fees for the class
    total_fees = class_fees.aggregate(total=Sum('amount'))['total'] or 0
    
    context = {
        'school_class': school_class,
        'class_fees': class_fees,
        'total_fees': total_fees,
        'active_term': active_term
    }
    
    return render(request, 'principal/view_class_fees.html', context)

@login_required
@role_required('principal')
def revenue_dashboard(request):
    # Get the principal’s school
    school = request.user.school

    # Try to get current active term safely
    active_term_obj = ActiveTerm.objects.filter(school=school).first()
    current_term = active_term_obj.term if active_term_obj else None

    # Get filters from request
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')
    term_filter = request.GET.get('term')

    # Base queryset
    payments = FeePayment.objects.filter(school=school)

    # Apply filters
    if start_date:
        payments = payments.filter(payment_date__gte=start_date)
    if end_date:
        payments = payments.filter(payment_date__lte=end_date)
    if term_filter:
        payments = payments.filter(term_id=term_filter)
    elif current_term:
        payments = payments.filter(term=current_term)

    # Totals
    total_revenue = payments.filter(payment_status='paid').aggregate(
        total=Sum('amount_paid')
    )['total'] or 0

    class_fee_revenue = payments.filter(
        payment_type='class_fee',
        payment_status='paid'
    ).aggregate(total=Sum('amount_paid'))['total'] or 0

    additional_fee_revenue = payments.filter(
        payment_type='additional_fee',
        payment_status='paid'
    ).aggregate(total=Sum('amount_paid'))['total'] or 0

    # Payment status stats
    payment_stats = {
        'total_payments': payments.count(),
        'paid_payments': payments.filter(payment_status='paid').count(),
        'partial_payments': payments.filter(payment_status='partial').count(),
        'unpaid_payments': payments.filter(payment_status='unpaid').count(),
    }

    # Recent payments (only valid select_related fields)
    recent_payments = payments.select_related(
        'student', 'student__user', 'class_fee', 'additional_fee', 'term'
    ).order_by('-payment_date')[:10]

    # Terms dropdown
    terms = Term.objects.filter(school=school)

    context = {
        'total_revenue': total_revenue,
        'class_fee_revenue': class_fee_revenue,
        'additional_fee_revenue': additional_fee_revenue,
        'payment_stats': payment_stats,
        'recent_payments': recent_payments,
        'terms': terms,
        'current_term': current_term,
        'start_date': start_date,
        'end_date': end_date,
        'term_filter': term_filter,
    }

    return render(request, 'principal/revenue_dashboard.html', context)

@login_required
@role_required('principal')
def record_fee_payment(request):
    school = request.user.school
    
    if request.method == 'POST':
        student_id = request.POST.get('student')
        payment_type = request.POST.get('payment_type')
        fee_category_id = request.POST.get('fee_category')
        additional_fee_id = request.POST.get('additional_fee')
        amount = request.POST.get('amount')
        amount_paid = request.POST.get('amount_paid')
        payment_method = request.POST.get('payment_method')
        payment_date = request.POST.get('payment_date')
        term_id = request.POST.get('term')
        academic_year = request.POST.get('academic_year')
        notes = request.POST.get('notes')
        
        try:
            student = Student.objects.get(id=student_id, student_class__school=school)
            
            # Create payment record
            payment = FeePayment.objects.create(
                student=student,
                school=school,
                payment_type=payment_type,
                fee_category_id=fee_category_id if payment_type == 'class_fee' else None,
                additional_fee_id=additional_fee_id if payment_type == 'additional_fee' else None,
                amount=amount,
                amount_paid=amount_paid,
                payment_method=payment_method,
                payment_date=payment_date,
                term_id=term_id,
                academic_year=academic_year,
                notes=notes
            )
            
            messages.success(request, f"Payment of ₦{amount_paid} recorded successfully. Receipt #: {payment.receipt_number}")
            return redirect('principal:revenue_dashboard')
            
        except Exception as e:
            messages.error(request, f"Error recording payment: {str(e)}")
    
    # GET request - show the form
    students = Student.objects.filter(student_class__school=school).select_related('user', 'student_class')
    #fee_categories = FeeCategory.objects.filter(school=school)
    additional_fees = AdditionalFee.objects.filter(applicable_classes__school=school).distinct()
    terms = Term.objects.filter(school=school)
    
    context = {
        'students': students,
        #'fee_categories': fee_categories,
        'additional_fees': additional_fees,
        'terms': terms,
        'payment_methods': FeePayment.PAYMENT_METHOD,
    }
    
    return render(request, 'principal/record_fee_payment.html', context)

@login_required
@role_required('principal')
def manage_additional_fees(request):
    school = request.user.school
    
    if request.method == 'POST':
        name = request.POST.get('name')
        amount = request.POST.get('amount')
        description = request.POST.get('description')
        is_general = request.POST.get('is_general') == 'on'
        applicable_classes = request.POST.getlist('applicable_classes')
        
        try:
            fee = AdditionalFee.objects.create(
                name=name,
                amount=amount,
                description=description,
                is_general=is_general
            )
            
            if not is_general and applicable_classes:
                fee.applicable_classes.set(applicable_classes)
            
            messages.success(request, "Additional fee created successfully.")
            return redirect('principal:manage_additional_fees')
            
        except Exception as e:
            messages.error(request, f"Error creating additional fee: {str(e)}")
    
    # GET request - show the form and list
    additional_fees = AdditionalFee.objects.filter(
        applicable_classes__school=school
    ).distinct().prefetch_related('applicable_classes')
    
    classes = Class.objects.filter(school=school)
    
    context = {
        'additional_fees': additional_fees,
        'classes': classes,
    }
    
    return render(request, 'principal/manage_additional_fees.html', context)

@login_required
@role_required('principal')
def edit_additional_fee(request, fee_id):
    school = request.user.school
    fee = get_object_or_404(AdditionalFee, id=fee_id, applicable_classes__school=school)
    
    if request.method == 'POST':
        fee.name = request.POST.get('name')
        fee.amount = request.POST.get('amount')
        fee.description = request.POST.get('description')
        fee.is_general = request.POST.get('is_general') == 'on'
        
        try:
            fee.save()
            
            if not fee.is_general:
                fee.applicable_classes.set(request.POST.getlist('applicable_classes'))
            else:
                fee.applicable_classes.clear()
            
            messages.success(request, "Additional fee updated successfully.")
            return redirect('principal:manage_additional_fees')
            
        except Exception as e:
            messages.error(request, f"Error updating additional fee: {str(e)}")
    
    return JsonResponse({
        'id': fee.id,
        'name': fee.name,
        'amount': float(fee.amount),
        'description': fee.description,
        'is_general': fee.is_general,
        'applicable_classes': list(fee.applicable_classes.values_list('id', flat=True))
    })

@login_required
@role_required('principal')
def delete_additional_fee(request, fee_id):
    fee = get_object_or_404(AdditionalFee, id=fee_id, applicable_classes__school=request.user.school)
    
    if request.method == 'POST':
        fee.delete()
        messages.success(request, "Additional fee deleted successfully.")
    
    return redirect('principal:manage_additional_fees')

@login_required
@role_required('principal')
def payment_details(request, payment_id):
    payment = get_object_or_404(FeePayment, id=payment_id, school=request.user.school)
    return render(request, 'principal/payment_details.html', {'payment': payment})

@login_required
@role_required('principal')
def export_revenue_report(request):
    school = request.user.school
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')
    term_filter = request.GET.get('term')
    
    # Base queryset
    payments = FeePayment.objects.filter(school=school)
    
    # Apply filters
    if start_date:
        payments = payments.filter(payment_date__gte=start_date)
    if end_date:
        payments = payments.filter(payment_date__lte=end_date)
    if term_filter:
        payments = payments.filter(term_id=term_filter)
    
    # Create Excel file
    output = BytesIO()
    workbook = xlsxwriter.Workbook(output)
    worksheet = workbook.add_worksheet()
    
    # Add headers
    headers = ['Date', 'Student', 'Fee Type', 'Category', 'Amount', 'Amount Paid', 'Status', 'Method', 'Receipt #']
    header_format = workbook.add_format({'bold': True, 'bg_color': '#f0f0f0'})
    
    for col, header in enumerate(headers):
        worksheet.write(0, col, header, header_format)
    
    # Add payment data
    for row, payment in enumerate(payments.select_related('student__user', 'fee_category', 'additional_fee'), start=1):
        worksheet.write(row, 0, payment.payment_date.strftime('%Y-%m-%d'))
        worksheet.write(row, 1, payment.student.user.get_full_name())
        worksheet.write(row, 2, payment.get_payment_type_display())
        worksheet.write(row, 3, payment.fee_category.name if payment.fee_category else payment.additional_fee.name)
        worksheet.write(row, 4, float(payment.amount))
        worksheet.write(row, 5, float(payment.amount_paid))
        worksheet.write(row, 6, payment.get_payment_status_display())
        worksheet.write(row, 7, payment.get_payment_method_display())
        worksheet.write(row, 8, payment.receipt_number)
    
    # Add totals
    total_row = len(payments) + 2
    worksheet.write(total_row, 3, 'Total:', header_format)
    worksheet.write(total_row, 4, f'=SUM(E2:E{total_row})', workbook.add_format({'bold': True}))
    worksheet.write(total_row, 5, f'=SUM(F2:F{total_row})', workbook.add_format({'bold': True}))
    
    # Set column widths
    worksheet.set_column('A:A', 12)  # Date
    worksheet.set_column('B:B', 30)  # Student
    worksheet.set_column('C:C', 15)  # Fee Type
    worksheet.set_column('D:D', 20)  # Category
    worksheet.set_column('E:F', 15)  # Amount columns
    worksheet.set_column('G:G', 12)  # Status
    worksheet.set_column('H:H', 15)  # Method
    worksheet.set_column('I:I', 15)  # Receipt #
    
    workbook.close()
    output.seek(0)
    
    # Generate filename
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    filename = f'revenue_report_{timestamp}.xlsx'
    
    response = HttpResponse(
        output.read(),
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    return response

@login_required
@role_required('principal')
def edit_fee_category(request, category_id):
    fee_category = get_object_or_404(FeeCategory, id=category_id, school=request.user.school)
    
    if request.method == 'POST':
        name = request.POST.get('name')
        amount = request.POST.get('amount')
        description = request.POST.get('description')
        is_recurring = request.POST.get('is_recurring') == 'on'
        due_date = request.POST.get('due_date')
        
        try:
            # Check if name is unique within the school
            if FeeCategory.objects.filter(school=request.user.school, name=name).exclude(id=category_id).exists():
                messages.error(request, "A fee category with this name already exists.")
                return redirect('principal:edit_fee_category', category_id=category_id)
            
            fee_category.name = name
            fee_category.amount = amount
            fee_category.description = description
            fee_category.is_recurring = is_recurring
            fee_category.due_date = due_date if due_date else None
            fee_category.save()
            
            messages.success(request, 'Fee category updated successfully!')
            return redirect('principal:fee_categories')
            
        except Exception as e:
            messages.error(request, f'Error updating fee category: {str(e)}')
            return redirect('principal:edit_fee_category', category_id=category_id)
    
    return render(request, 'principal/edit_fee_category.html', {
        'fee_category': fee_category
    })

@login_required
@role_required('principal')
def delete_fee_category(request, category_id):
    fee_category = get_object_or_404(FeeCategory, id=category_id, school=request.user.school)
    
    if request.method == 'POST':
        try:
            # Check if fee category is in use
            if ClassFee.objects.filter(fee_category=fee_category).exists():
                messages.error(request, 'Cannot delete fee category that is in use by classes.')
                return redirect('principal:fee_categories')
            
            if FeePayment.objects.filter(fee_category=fee_category).exists():
                messages.error(request, 'Cannot delete fee category that has associated payments.')
                return redirect('principal:fee_categories')
            
            fee_category.delete()
            messages.success(request, 'Fee category deleted successfully!')
            
        except Exception as e:
            messages.error(request, f'Error deleting fee category: {str(e)}')
    
    return redirect('principal:fee_categories')

@login_required
@role_required('principal')
@require_http_methods(['GET'])
def additional_fee_detail(request, fee_id):
    """API endpoint to get additional fee details"""
    try:
        fee = AdditionalFee.objects.get(id=fee_id, school=request.user.school)
        data = {
            'id': fee.id,
            'name': fee.name,
            'amount': str(fee.amount),
            'description': fee.description,
            'is_active': fee.is_active,
            'is_general': fee.is_general,
            'applicable_classes': [{'id': c.id, 'name': c.name} for c in fee.applicable_classes.all()]
        }
        return JsonResponse(data)
    except AdditionalFee.DoesNotExist:
        return JsonResponse({'error': 'Fee not found'}, status=404)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

@login_required
@role_required('principal')
@require_http_methods(['GET'])
def revenue_stats_api(request):
    """API endpoint to get revenue statistics"""
    try:
        # Get date range from request
        start_date = request.GET.get('start_date')
        end_date = request.GET.get('end_date')
        
        # Convert to datetime objects
        if start_date:
            start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
        else:
            start_date = timezone.now().date() - timedelta(days=30)
            
        if end_date:
            end_date = datetime.strptime(end_date, '%Y-%m-%d').date()
        else:
            end_date = timezone.now().date()
        
        # Get payment statistics
        payments = FeePayment.objects.filter(
            school=request.user.school,
            payment_date__range=[start_date, end_date]
        )
        
        stats = {
            'total_revenue': str(payments.aggregate(total=Sum('amount_paid'))['total'] or 0),
            'class_fee_revenue': str(payments.filter(payment_type='class_fee').aggregate(total=Sum('amount_paid'))['total'] or 0),
            'additional_fee_revenue': str(payments.filter(payment_type='additional_fee').aggregate(total=Sum('amount_paid'))['total'] or 0),
            'payment_status': {
                'paid': payments.filter(payment_status='paid').count(),
                'partial': payments.filter(payment_status='partial').count(),
                'unpaid': payments.filter(payment_status='unpaid').count()
            },
            'daily_revenue': list(payments.values('payment_date')
                                .annotate(total=Sum('amount_paid'))
                                .order_by('payment_date')
                                .values('payment_date', 'total'))
        }
        
        return JsonResponse(stats)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

@login_required
@role_required('principal')
@require_http_methods(['GET'])
def revenue_chart_data_api(request):
    """API endpoint to get revenue chart data"""
    try:
        # Get date range and interval from request
        start_date = request.GET.get('start_date')
        end_date = request.GET.get('end_date')
        interval = request.GET.get('interval', 'daily')  # daily, weekly, monthly
        
        # Convert to datetime objects
        if start_date:
            start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
        else:
            start_date = timezone.now().date() - timedelta(days=30)
            
        if end_date:
            end_date = datetime.strptime(end_date, '%Y-%m-%d').date()
        else:
            end_date = timezone.now().date()
        
        # Get base queryset
        payments = FeePayment.objects.filter(
            school=request.user.school,
            payment_date__range=[start_date, end_date]
        )
        
        # Prepare data based on interval
        if interval == 'daily':
            data = list(payments.values('payment_date')
                       .annotate(
                           total=Sum('amount_paid'),
                           class_fees=Sum('amount_paid', filter=Q(payment_type='class_fee')),
                           additional_fees=Sum('amount_paid', filter=Q(payment_type='additional_fee'))
                       )
                       .order_by('payment_date'))
            
        elif interval == 'weekly':
            data = list(payments.extra(
                select={'week': "date_trunc('week', payment_date)"}
            ).values('week')
            .annotate(
                total=Sum('amount_paid'),
                class_fees=Sum('amount_paid', filter=Q(payment_type='class_fee')),
                additional_fees=Sum('amount_paid', filter=Q(payment_type='additional_fee'))
            )
            .order_by('week'))
            
        else:  # monthly
            data = list(payments.extra(
                select={'month': "date_trunc('month', payment_date)"}
            ).values('month')
            .annotate(
                total=Sum('amount_paid'),
                class_fees=Sum('amount_paid', filter=Q(payment_type='class_fee')),
                additional_fees=Sum('amount_paid', filter=Q(payment_type='additional_fee'))
            )
            .order_by('month'))
        
        # Format the data
        formatted_data = []
        for item in data:
            formatted_item = {
                'date': item.get('payment_date', item.get('week', item.get('month'))).strftime('%Y-%m-%d'),
                'total': str(item['total'] or 0),
                'class_fees': str(item['class_fees'] or 0),
                'additional_fees': str(item['additional_fees'] or 0)
            }
            formatted_data.append(formatted_item)
        
        return JsonResponse({'data': formatted_data})
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)