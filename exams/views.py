from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.utils.timezone import now
import json

from .models import *
from academic_main.models import *
from stu_main.models import CustomUser
from .utils import exam_session_required


# EXAM LOGIN VIEW
def exam_login_view(request):
    if request.method == 'POST':
        email = request.POST.get('email')
        password = request.POST.get('password')

        try:
            user = CustomUser.objects.get(email=email)
            user = authenticate(request, username=user.username, password=password)

            if user and user.user_type == 'student':
                login(request, user)

                # Set session flag for exam login
                request.session['exam_logged_in'] = True

                return redirect('available_exams')
            else:
                messages.error(request, "Only students can log in for exams.")
        except CustomUser.DoesNotExist:
            messages.error(request, "Invalid credentials.")

    return render(request, 'exams/login.html')


# EXAM LOGOUT VIEW
def exam_logout_view(request):
    # Clear the session flag
    request.session.pop('exam_logged_in', None)

    # Optionally log out the user entirely (or keep them logged in if it's shared)
    logout(request)

    return redirect('exam_login')


@exam_session_required
def available_exams_view(request):
    student = request.user
    student_class = student.student_profile.student_class

    try:
        active_term = ActiveTerm.get_active_term()
    except AttributeError:
        return render(request, 'exams/available_exams.html', {
            'available_exams': [],
            'completed_exams': [],
            'error': "No active term has been set. Please contact the administrator."
        })

    # Exams the student hasn't done yet (in the active term)
    available_exams = Exam.objects.filter(
        class_subject__school_class=student_class,
        is_active=True,
        term=active_term
    ).exclude(
        student_records__student=student,
        student_records__is_submitted=True
    )

    # Exams the student has completed (in the active term)
    completed_exams = Exam.objects.filter(
        student_records__student=student,
        student_records__is_submitted=True,
        term=active_term
    ).distinct()

    return render(request, 'exams/available_exams.html', {
        'available_exams': available_exams,
        'completed_exams': completed_exams,
        'active_term': active_term
    })


@exam_session_required
def take_exam(request, exam_id):
    exam = get_object_or_404(Exam, id=exam_id)
    questions = Question.objects.filter(exam=exam)
    return render(request, "exams/take_exam.html", {"exam": exam, "questions": questions})


@exam_session_required
def get_question(request, exam_id, question_index):
    exam = get_object_or_404(Exam, id=exam_id)
    questions = list(Question.objects.filter(exam=exam))

    if 0 <= question_index < len(questions):
        return render(request, "exams/question_component.html", {"question": questions[question_index]})
    
    return JsonResponse({"error": "Invalid question index"}, status=400)


@exam_session_required
def save_answer(request):
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            answers = data.get("answers", {})

            if not answers:
                return JsonResponse({"error": "No answers provided"}, status=400)

            student = request.user
            first_question_id = list(answers.keys())[0]
            first_question = get_object_or_404(Question, id=first_question_id)
            exam = first_question.exam

            # Get active term
            
            active_term = ActiveTerm.get_active_term()

            exam_record, created = StudentExamRecord.objects.get_or_create(
                student=student,
                exam=exam,
                defaults={
                    "responses": {},
                    "score": 0,
                    "is_submitted": False,
                    "term": active_term  # 👈 Save active term
                }
            )

            # If it already exists and term isn't set, update it
            if not created and not exam_record.term:
                exam_record.term = active_term

            responses = exam_record.responses or {}
            responses.update(answers)
            exam_record.responses = responses
            exam_record.save()

            return JsonResponse({"message": "Exam submitted successfully!"})

        except json.JSONDecodeError:
            return JsonResponse({"error": "Invalid JSON data"}, status=400)

    return JsonResponse({"error": "Invalid request"}, status=400)


@exam_session_required
def exam_result(request, exam_id):
    exam = get_object_or_404(Exam, id=exam_id)
    student = request.user

    exam_record = get_object_or_404(StudentExamRecord, student=student, exam=exam)
    questions = Question.objects.filter(exam=exam)

    total_questions = questions.count()
    student_responses = exam_record.responses or {}

    result_details = []
    correct_count = 0

    for question in questions:
        question_id = str(question.id)
        student_answer = student_responses.get(question_id)
        is_correct = student_answer == question.correct_answer

        if is_correct:
            correct_count += 1

        result_details.append({
            'question': question,
            'student_answer': student_answer,
            'is_correct': is_correct,
            'correct_answer': question.correct_answer,
        })

    score_percent = (correct_count / total_questions * 100) if total_questions > 0 else 0

    if exam_record.score == 0:
        exam_record.score = score_percent
        exam_record.is_submitted = True
        exam_record.save()

    # Optionally clear the session so the user must re-auth next time
    request.session.pop('exam_logged_in', None)

    context = {
        'exam': exam,
        'result_details': result_details,
        'correct_count': correct_count,
        'total_questions': total_questions,
        'score_percent': score_percent,
        'exam_record': exam_record,
    }

    return render(request, 'exams/exam_result.html', context)
