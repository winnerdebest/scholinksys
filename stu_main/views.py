from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, login, logout
from django.http import JsonResponse, HttpResponseBadRequest
from django.views.decorators.csrf import csrf_exempt
from django.contrib import messages
import json
from django.db.models import Q
from .models import *
from exams.models import *

from .decorators import student_required

 


@login_required
@student_required
def student_dashboard(request):
    user = request.user
    student = getattr(user, 'student_profile', None)
    school = student.school if student else None

    if student:
        student_class = student.student_class
        
        # Query for all posts for the student's class, including form master posts
        posts = StudentPost.objects.filter(
            Q(student__student_class=student_class) |
            Q(created_by=student_class.form_master)
        ).order_by('-created_at')
    else:
        posts = StudentPost.objects.none()

    # Get the active term
    active_term = ActiveTerm.get_active_term()

    context = {
        'user': user,
        'student': student,
        'posts': posts,
        'term': active_term,
        'school': school,
    }

    return render(request, 'dashboard.html', context)


@login_required
@student_required
def create_post(request):
    if request.method == "POST":
        content = request.POST.get("content")
        user = request.user

        if not content:
            return JsonResponse({"error": "Content cannot be empty."}, status=400)

        post_data = {
            "content": content,
            "created_by": user,
        }

        # If the user is a student, attach their student profile
        if hasattr(user, "student_profile"):
            post_data["student"] = user.student_profile

        post = StudentPost.objects.create(**post_data)
        return render(request, "partials/post_item.html", {"post": post})

    return JsonResponse({"error": "Method not allowed"}, status=405)


@login_required
@student_required
def like_post(request, post_id):
    if request.method == 'POST':
        post = get_object_or_404(StudentPost, id=post_id)
        student = request.user.student_profile

        if post.likes.filter(id=student.id).exists():
            post.likes.remove(student)
            liked = False
        else:
            post.likes.add(student)
            post.dislikes.remove(student)  # Remove from dislikes if previously disliked
            liked = True

        return JsonResponse({
            "liked": liked,
            "disliked": post.dislikes.filter(id=student.id).exists(),
            "total_likes": post.likes.count(),
            "total_dislikes": post.dislikes.count()
        })

    return HttpResponseBadRequest()


@login_required
@student_required
def dislike_post(request, post_id):
    if request.method == 'POST':
        post = get_object_or_404(StudentPost, id=post_id)
        student = request.user.student_profile

        if post.dislikes.filter(id=student.id).exists():
            post.dislikes.remove(student)
            disliked = False
        else:
            post.dislikes.add(student)
            post.likes.remove(student)  # Remove from likes if previously liked
            disliked = True

        return JsonResponse({
            "liked": post.likes.filter(id=student.id).exists(),
            "disliked": disliked,
            "total_likes": post.likes.count(),
            "total_dislikes": post.dislikes.count()
        })

    return HttpResponseBadRequest()



from .utils import get_all_payments  # Make sure this is imported

@login_required
@student_required
def profile(request):
    user = request.user
    student = getattr(user, 'student_profile', None)
    guardian = None

    if student:
        guardian = student.parents.first()

    #subject_summaries = SubjectGradeSummary.objects.filter(student=student)

    all_payments = get_all_payments()
    student_payments = sorted([
        {
            'date': p.get('paid_at'),
            'amount': p.get('amount_paid'),
            'method': 'Manual',
            'status': p.get('status'),
        }
        for p in all_payments
        if str(p.get('student_id')) == str(student.id)
    ], key=lambda x: datetime.strptime(x['date'], '%Y-%m-%dT%H:%M:%S.%f'), reverse=True)

    rank = "1st"  # Placeholder

    context = {
        'student': student,
        'guardian': guardian,
        'rank': rank,
        #'subject_summaries': subject_summaries,
        'payments': student_payments,
    }

    return render(request, 'profile.html', context)







from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .utils import store_payment
from datetime import datetime

@login_required
def pay_school_fees(request, student_id):
    if request.method == 'POST':
        amount_paid = request.POST.get('amount')

        # Prepare payment data
        payment_data = {
            'student_id': student_id,
            'user_id': request.user.id,
            'amount_paid': amount_paid,
            'paid_at': datetime.now().isoformat(),
            'status': 'pending'
        }

        # Save to JSON file
        store_payment(payment_data)

        messages.success(request, 'Payment successful!')

        return redirect('profile')





#Importing cause this is the only view that used it 
from teacher_logic.models import SubjectGradeSummary, ClassGradeSummary
# This is for the results 

@login_required
@student_required
def student_term_results_overview(request):
    student = get_object_or_404(Student, user=request.user)
    terms_with_results = Term.objects.filter(subject_grade_summaries__student=request.user).distinct()

    return render(request, 'results/term_overview.html', {
        'student': student,
        'terms': terms_with_results
    })



@login_required
@student_required
def student_result_view(request, term_id):
    student = get_object_or_404(Student, user=request.user)
    term = get_object_or_404(Term, id=term_id)
    subject_summaries = SubjectGradeSummary.objects.filter(student=request.user, term=term)

    class_summary = ClassGradeSummary.objects.filter(student=request.user, term=term).first()

    context = {
        'student': student,
        'term': term,
        'subject_summaries': subject_summaries,
        'class_summary': class_summary
    }
    return render(request, 'results/student_result.html', context)


from django.utils.timezone import now

@login_required
def leaderboard(request, class_id):
    # Get the current term (you can customize this logic if you have multiple terms)
    current_term = ActiveTerm.get_active_term()

    
    if not current_term:
        # Handle the case when no current term is found (optional)
        return render(request, 'leaderboard.html', {'error': 'No current term found.'})

    # Get the class
    selected_class = Class.objects.get(id=class_id)

    # Get the grade summaries for students in this class and the current term
    grade_summaries = ClassGradeSummary.objects.filter(
        student_class=selected_class,
        term=current_term
    ).order_by('rank')  # Ordering by rank (highest first)

    return render(request, 'leaderboard.html', {
        'class': selected_class,
        'grade_summaries': grade_summaries,
        'current_term': current_term,
    })