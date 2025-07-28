from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse, HttpResponseBadRequest
from django.views.decorators.csrf import csrf_exempt
from django.contrib import messages
import json
from .models import *
from academic_main.models import *
from exams.models import *

from stu_main.decorators import student_required



@login_required
@student_required
def assignments(request):
    user = request.user
    student = getattr(user, 'student_profile', None)

    if student and hasattr(student, 'student_class'):
        try:
            active_term = ActiveTerm.get_active_term()

            class_subjects = ClassSubject.objects.filter(school_class=student.student_class)

            # Filter active assignments by term
            all_active_assignments = Assignment.objects.filter(
                class_subject__in=class_subjects,
                is_active=True,
                term=active_term  # 👈 Only assignments for the active term
            ).order_by('-created_at')

            # Submitted assignments by the student, filtered by term
            submitted_records = StudentAssignmentRecord.objects.filter(
                student=user,
                is_submitted=True,
                term=active_term  # 👈 Only records for the active term
            ).select_related(
                'assignment',
                'assignment__class_subject',
                'assignment__class_subject__subject',
                'assignment__class_subject__school_class'
            ).order_by('-submitted_at')

            # IDs of assignments already submitted
            submitted_assignment_ids = submitted_records.values_list('assignment_id', flat=True)

            # Assignments that are active and not submitted
            unsubmitted_assignments = all_active_assignments.exclude(id__in=submitted_assignment_ids)

        except Exception as e:
            unsubmitted_assignments = []
            submitted_records = []
            messages.error(request, f"Error loading assignments: {str(e)}")
    else:
        unsubmitted_assignments = []
        submitted_records = []
        if not student:
            messages.warning(request, "No student profile found for this user.")
        elif not hasattr(student, 'student_class'):
            messages.warning(request, "You are not assigned to any class.")

    context = {
        'student': student,
        'assignments': unsubmitted_assignments,
        'submitted_records': submitted_records,
    }

    return render(request, 'assignments/assignments.html', context)


@login_required
@student_required
def take_assignment(request, assignment_id):
    """
    Load the assignment and its questions.
    """
    assignment = get_object_or_404(Assignment, id=assignment_id)
    questions = assignment.questions.all()  # Uses the reverse relationship

    return render(request, "assignments/take_assignment.html", {
        "assignment": assignment,
        "questions": questions
    })


@login_required
@student_required
def get_assignment_question(request, assignment_id, question_index):
    """
    Return one question for HTMX/AJAX.
    """
    assignment = get_object_or_404(Assignment, id=assignment_id)
    questions = list(assignment.questions.all())

    if 0 <= question_index < len(questions):
        question = questions[question_index]
        return render(request, "assignments/question_component.html", {
            "question": question
        })

    return JsonResponse({"error": "Invalid question index"}, status=400)


@csrf_exempt
@login_required
@student_required
def save_assignment_answer(request):
    """
    Save student answers and submit assignment.
    """
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            answers = data.get("answers", {})

            if not answers:
                return JsonResponse({"error": "No answers submitted"}, status=400)

            student = request.user

            first_question_id = list(answers.keys())[0]
            first_question = get_object_or_404(Question, id=first_question_id)
            assignment = first_question.assignment

            # Get active term
            active_term = ActiveTerm.get_active_term()

            record, created = StudentAssignmentRecord.objects.get_or_create(
                student=student,
                assignment=assignment,
                defaults={
                    "responses": {},
                    "score": 0,
                    "is_submitted": False,
                    "term": active_term  # 👈 Save the active term
                }
            )

            if not created and not record.term:
                record.term = active_term

            record.responses = answers 
            record.save()

            return JsonResponse({"message": "Assignment submitted successfully"})

        except json.JSONDecodeError:
            return JsonResponse({"error": "Invalid data"}, status=400)
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=500)

    return JsonResponse({"error": "Invalid request method"}, status=400)



@login_required
@student_required
def assignment_result(request, assignment_id):
    """
    Show student result after grading.
    """
    assignment = get_object_or_404(Assignment, id=assignment_id)
    student = request.user
    record = get_object_or_404(StudentAssignmentRecord, student=student, assignment=assignment)

    questions = assignment.questions.all()
    total_questions = questions.count()
    responses = record.responses or {}

    correct_count = 0
    result_details = []

    for question in questions:
        qid = str(question.id)
        student_answer = responses.get(qid)
        correct_answer = question.correct_answer
        is_correct = student_answer == correct_answer

        if is_correct:
            correct_count += 1

        result_details.append({
            "question": question,
            "student_answer": student_answer,
            "correct_answer": correct_answer,
            "is_correct": is_correct
        })

    score_percent = (correct_count / total_questions) * 100 if total_questions > 0 else 0

    if not record.is_submitted:
        record.score = score_percent
        record.is_submitted = True
        record.save()

    return render(request, "assignments/assignment_result.html", {
        "assignment": assignment,
        "result_details": result_details,
        "correct_count": correct_count,
        "total_questions": total_questions,
        "score_percent": score_percent,
        "record": record
    })
