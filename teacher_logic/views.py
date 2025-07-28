#imports 
from django.shortcuts import render, get_object_or_404, redirect
from django.db.models import Prefetch
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.views.decorators.http import require_POST
from django.urls import reverse
from django.http import HttpResponseRedirect
from django.forms import modelformset_factory
from django.db.models import Count
from django.contrib import messages

#importing all models from other apps 
from academic_main.models import *
from exams.models import *
from academic_main.decorators import role_required
from assignments.models import *
from stu_main.models import *
from .models import *

#importing forms
from .forms import *


@login_required
@role_required('teacher')
def teacher_dashboard(request):
    teacher = Teacher.objects.get(user=request.user)

    # Fetch all ClassSubjects assigned to this teacher
    assigned_subjects = ClassSubject.objects.filter(teacher=teacher).select_related('subject', 'school_class')

    # Group by class, then collect all subjects the teacher teaches in that class
    class_data = {}
    for cs in assigned_subjects:
        class_name = cs.school_class.name
        if class_name not in class_data:
            class_data[class_name] = {
                'class_obj': cs.school_class,
                'subjects': [cs.subject.name]
            }
        else:
            class_data[class_name]['subjects'].append(cs.subject.name)

    return render(request, 'dashboard/dashboard.html', {
        'class_data': class_data
    })


@login_required
@role_required('teacher')
def teacher_class_detail(request, class_id):
    teacher = Teacher.objects.get(user=request.user)
    school_class = get_object_or_404(Class, id=class_id)

    # Get only the subjects THIS teacher handles for that class
    class_subjects = ClassSubject.objects.filter(
        teacher=teacher,
        school_class=school_class
    ).select_related('subject')

    return render(request, 'dashboard/teacher_class_detail.html', {
        'school_class': school_class,
        'class_subjects': class_subjects
    })


@login_required
@role_required('teacher')
def subject_detail_view(request, class_subject_id):
    class_subject = get_object_or_404(ClassSubject, id=class_subject_id)

    active_term = ActiveTerm.get_active_term()
    
    assignments = Assignment.objects.filter(class_subject=class_subject).annotate(submission_count=Count('student_records')).order_by('-created_at')
    exams = Exam.objects.filter(class_subject=class_subject).annotate(submission_count=Count('student_records')).order_by('-created_at')

    student_assignment_records = StudentAssignmentRecord.objects.filter(assignment__in=assignments)
    student_exam_records = StudentExamRecord.objects.filter(exam__in=exams)

    query = request.GET.get('q')
    if query:
        student_assignment_records = student_assignment_records.filter(
            Q(student__username__icontains=query) |
            Q(student__first_name__icontains=query) |
            Q(student__last_name__icontains=query)
        )
        student_exam_records = student_exam_records.filter(
            Q(student__username__icontains=query) |
            Q(student__first_name__icontains=query) |
            Q(student__last_name__icontains=query)
        )

    context = {
        "class_subject": class_subject,
        "assignments": assignments,
        "exams": exams,
        "assignment_records": student_assignment_records,
        "exam_records": student_exam_records,
        "active_term": active_term,
    }
    return render(request, "dashboard"
    "/class_subject_detail.html", context)



@login_required
@role_required('teacher')
@require_POST
def toggle_assignment_active(request, assignment_id):
    assignment = get_object_or_404(Assignment, id=assignment_id)
    assignment.is_active = not assignment.is_active
    assignment.save()
    return redirect(request.META.get('HTTP_REFERER', '/'))

@require_POST
@login_required
@role_required('teacher')
def toggle_exam_active(request, exam_id):
    exam = get_object_or_404(Exam, id=exam_id)
    exam.is_active = not exam.is_active
    exam.save()
    return redirect(request.META.get('HTTP_REFERER', '/'))



@login_required
@role_required('teacher')
def create_exam(request, class_subject_id, term_id):
    class_subject = get_object_or_404(ClassSubject, id=class_subject_id)
    term = get_object_or_404(Term, id=term_id)

    if request.method == 'POST':
        form = ExamForm(request.POST)
        question_formset = QuestionFormSet(request.POST, request.FILES, prefix='questions')

        if form.is_valid() and question_formset.is_valid():
            exam = form.save(commit=False)
            exam.class_subject = class_subject
            exam.term = term
            exam.save()

            for question_form in question_formset:
                if question_form.cleaned_data:  
                    question = question_form.save(commit=False)
                    question.exam = exam
                    question.created_by = request.user
                    question.save()

            return redirect('teacher:class_subject_detail', class_subject_id)

    else:
        form = ExamForm()
        question_formset = QuestionFormSet(queryset=Question.objects.none(), prefix='questions')

    return render(request, 'dashboard/create_exam.html', {
        'form': form,
        'question_formset': question_formset,
        'class_subject': class_subject,
        'term': term,
    })


@login_required
def create_assignment(request, class_subject_id, term_id):
    class_subject = get_object_or_404(ClassSubject, id=class_subject_id)
    term = get_object_or_404(Term, id=term_id)

    if request.method == 'POST':
        form = AssignmentForm(request.POST)
        question_formset = QuestionFormSet(request.POST, request.FILES, prefix='questions')

        if form.is_valid() and question_formset.is_valid():
            assignment = form.save(commit=False)
            assignment.class_subject = class_subject
            assignment.term = term
            assignment.save()

            for question_form in question_formset:
                if question_form.cleaned_data:  # skip empty forms
                    question = question_form.save(commit=False)
                    question.assignment = assignment
                    question.created_by = request.user
                    question.save()

            return redirect('teacher:class_subject_detail', class_subject_id)

    else:
        form = AssignmentForm()
        question_formset = QuestionFormSet(queryset=Question.objects.none(), prefix='questions')

    return render(request, 'dashboard/create_assignment.html', {
        'form': form,
        'question_formset': question_formset,
        'class_subject': class_subject,
        'term': term,
    })



# Edit Exam
@login_required
@role_required('teacher')
def edit_exam(request, exam_id):
    exam = get_object_or_404(Exam, id=exam_id)
    class_subject = exam.class_subject
    term = exam.term

    QuestionFormSet = modelformset_factory(Question, form=QuestionForm, extra=0, can_delete=True)

    if request.method == 'POST':
        form = ExamForm(request.POST, instance=exam)
        formset = QuestionFormSet(request.POST, request.FILES, queryset=exam.questions.all(), prefix='questions')

        if form.is_valid() and formset.is_valid():
            form.save()
            for question_form in formset:
                if question_form.cleaned_data:
                    if question_form.cleaned_data.get('DELETE'):
                        if question_form.instance.pk:
                            question_form.instance.delete()
                    else:
                        question = question_form.save(commit=False)
                        question.exam = exam
                        question.created_by = request.user
                        question.save()
            messages.success(request, 'Exam updated successfully.')
            return redirect('teacher:class_subject_detail', class_subject.id)
    else:
        form = ExamForm(instance=exam)
        formset = QuestionFormSet(queryset=exam.questions.all(), prefix='questions')

    return render(request, 'dashboard/edit_exam.html', {
        'form': form,
        'question_formset': formset,
        'class_subject': class_subject,
        'term': term,
        'exam': exam,
    })

# Delete Exam
@login_required
@role_required('teacher')
def delete_exam(request, exam_id):
    exam = get_object_or_404(Exam, id=exam_id)
    class_subject_id = exam.class_subject.id

    if request.method == 'POST':
        exam.delete()
        messages.success(request, 'Exam deleted successfully.')
        return redirect('teacher:class_subject_detail', class_subject_id)

    return render(request, 'dashboard/confirm_delete.html', {
        'object': exam,
        'type': 'exam',
    })


@login_required
@role_required('teacher')
def edit_assignment(request, assignment_id):
    assignment = get_object_or_404(Assignment, id=assignment_id)
    class_subject = assignment.class_subject
    term = assignment.term

    QuestionFormSet = modelformset_factory(
        Question, form=QuestionForm, extra=0, can_delete=True
    )

    if request.method == 'POST':
        print("POST request received")

        form = AssignmentForm(request.POST, instance=assignment)
        formset = QuestionFormSet(
            request.POST, request.FILES,
            queryset=assignment.questions.all(), prefix='questions'
        )

        print("AssignmentForm valid:", form.is_valid())
        print("AssignmentForm errors:", form.errors)
        print("Formset valid:", formset.is_valid())
        print("Formset errors:", formset.errors)

        if form.is_valid() and formset.is_valid():
            updated_assignment = form.save()
            print("Assignment saved:", updated_assignment.name, updated_assignment.is_active)

            for question_form in formset:
                if question_form.cleaned_data:
                    if question_form.cleaned_data.get('DELETE'):
                        if question_form.instance.pk:
                            question_form.instance.delete()
                            print("Deleted question:", question_form.instance.pk)
                    else:
                        question = question_form.save(commit=False)
                        question.assignment = assignment
                        question.created_by = request.user
                        question.save()
                        print("Saved/Updated question:", question.id)

            messages.success(request, 'Assignment updated successfully.')
            return redirect('teacher:class_subject_detail', class_subject.id)
        else:
            messages.error(request, 'Please correct the errors below.')

    else:
        form = AssignmentForm(instance=assignment)
        formset = QuestionFormSet(queryset=assignment.questions.all(), prefix='questions')

    return render(request, 'dashboard/edit_assignment.html', {
        'form': form,
        'question_formset': formset,
        'class_subject': class_subject,
        'term': term,
        'assignment': assignment,
    })


@login_required
@role_required('teacher')
def delete_assignment(request, assignment_id):
    assignment = get_object_or_404(Assignment, id=assignment_id)
    class_subject_id = assignment.class_subject.id

    if request.method == 'POST':
        assignment.delete()
        messages.success(request, 'Assignment deleted successfully.')
        return redirect('teacher:class_subject_detail', class_subject_id)

    return render(request, 'dashboard/confirm_delete.html', {
        'object': assignment,
        'type': 'assignment',
    })



@login_required
@role_required('teacher')
def subject_student_list_view(request, class_subject_id):
    class_subject = get_object_or_404(ClassSubject, id=class_subject_id)
    school_class = class_subject.school_class

    query = request.GET.get('q')
    term_id = request.GET.get('term')

    # Determine term to use
    term = None
    if term_id:
        term = get_object_or_404(Term, id=term_id)
    else:
        try:
            term = ActiveTerm.get_active_term()
        except:
            term = None  # Handle case where no ActiveTerm is defined

    students = CustomUser.objects.filter(
        user_type='student',
        student_profile__student_class=school_class
    )

    if query:
        students = students.filter(
            Q(username__icontains=query) |
            Q(first_name__icontains=query) |
            Q(last_name__icontains=query)
        )

    # Retrieve the grade summaries for the students
    grade_summaries = SubjectGradeSummary.objects.filter(
        class_subject=class_subject,
        term=term,
    )

    # Create a dictionary to map student to their grade summary
    grade_summary_dict = {summary.student.id: summary for summary in grade_summaries}

    # Attach the grade summary to each student in the context
    student_with_grades = []
    for student in students:
        grade_summary = grade_summary_dict.get(student.id)
        student_with_grades.append({
            'student': student,
            'grade_summary': grade_summary
        })

    context = {
        "student_with_grades": student_with_grades,
        "class_subject": class_subject,
        "term": term, 
    }

    return render(request, "grades/class_subject_students.html", context)



# Importing it here because its the only view that needed it 
from django.db.models import Sum

@login_required
@role_required('teacher')
def grade_student(request, class_subject_id, student_id, term_id):
    class_subject = get_object_or_404(ClassSubject, id=class_subject_id)
    student = get_object_or_404(CustomUser, id=student_id, user_type='student')
    term = get_object_or_404(Term, id=term_id)

    # Aggregate internal scores (for display only)
    total_internal_assignment = StudentAssignmentRecord.objects.filter(
        student=student,
        assignment__class_subject=class_subject,
        term=term,
        is_submitted=True
    ).aggregate(score_sum=Sum('score'))['score_sum'] or 0

    total_internal_exam = StudentExamRecord.objects.filter(
        student=student,
        exam__class_subject=class_subject,
        term=term,
        is_submitted=True
    ).aggregate(score_sum=Sum('score'))['score_sum'] or 0

    if request.method == 'POST':
        try:
            external_exam_score = float(request.POST.get('external_exam_score') or 0)
            external_assignment_score = float(request.POST.get('external_assignment_score') or 0)
            external_test_score = float(request.POST.get('external_test_score') or 0)
        except (ValueError, TypeError):
            messages.error(request, "All external scores must be valid numbers.")
            return redirect(request.path)

        scores = {
            "External Exam": external_exam_score,
            "External Assignment": external_assignment_score,
            "External Test": external_test_score,
        }

        for label, score in scores.items():
            if not 0 <= score <= 100:
                messages.error(request, f"{label} score must be between 0 and 100.")
                return redirect(request.path)

        # Save/update only the external scores
        SubjectGradeSummary.objects.update_or_create(
            student=student,
            class_subject=class_subject,
            term=term,
            defaults={
                'external_exam_score': external_exam_score,
                'external_assignment_score': external_assignment_score,
                'external_test_score': external_test_score,
            }
        )

        messages.success(request, "Student grades updated successfully.")
        return redirect('teacher:subject_student_list', class_subject_id=class_subject.id)

    return render(request, 'grades/grade_student.html', {
        'student': student,
        'class_subject': class_subject,
        'term': term,
        'internal_exam_score': total_internal_exam,
        'internal_assignment_score': total_internal_assignment,
    })


# Edit Grade View 
@login_required
@role_required('teacher')
def edit_student_grade(request, class_subject_id, student_id, term_id):
    class_subject = get_object_or_404(ClassSubject, id=class_subject_id)
    student = get_object_or_404(CustomUser, id=student_id, user_type='student')
    term = get_object_or_404(Term, id=term_id)

    # Get grade summary if it exists
    grade_summary = get_object_or_404(
        SubjectGradeSummary,
        student=student,
        class_subject=class_subject,
        term=term
    )

    # Always recalculate internal scores
    total_internal_assignment = StudentAssignmentRecord.objects.filter(
        student=student,
        assignment__class_subject=class_subject,
        term=term,
        is_submitted=True
    ).aggregate(score_sum=Sum('score'))['score_sum'] or 0

    total_internal_exam = StudentExamRecord.objects.filter(
        student=student,
        exam__class_subject=class_subject,
        term=term,
        is_submitted=True
    ).aggregate(score_sum=Sum('score'))['score_sum'] or 0

    if request.method == 'POST':
        try:
            external_exam_score = float(request.POST.get('external_exam_score'))
            external_assignment_score = float(request.POST.get('external_assignment_score'))
            external_test_score = float(request.POST.get('external_test_score'))
        except (ValueError, TypeError):
            messages.error(request, "All external scores must be valid numbers.")
            return redirect(request.path)

        # Validate score ranges
        for label, score in {
            "External Exam": external_exam_score,
            "External Assignment": external_assignment_score,
            "External Test": external_test_score,
        }.items():
            if not 0 <= score <= 100:
                messages.error(request, f"{label} score must be between 0 and 100.")
                return redirect(request.path)

        # Update the existing grade summary
        grade_summary.total_exam_score = total_internal_exam
        grade_summary.total_assignment_score = total_internal_assignment
        grade_summary.external_exam_score = external_exam_score
        grade_summary.external_assignment_score = external_assignment_score
        grade_summary.external_test_score = external_test_score
        grade_summary.save()

        messages.success(request, "Grades successfully updated.")
        return redirect('teacher:subject_student_list', class_subject.id)

    return render(request, 'grades/edit_grade.html', {
        'student': student,
        'class_subject': class_subject,
        'term': term,
        'grade_summary': grade_summary,
        'internal_exam_score': total_internal_exam,
        'internal_assignment_score': total_internal_assignment,
        'external_exam_score': grade_summary.external_exam_score,
        'external_assignment_score': grade_summary.external_assignment_score,
        'external_test_score': grade_summary.external_test_score,
    })



@login_required
@role_required('teacher')
def class_posts_view(request):
    user = request.user

    if user.user_type != 'teacher':
        return redirect('unauthorized')  
    
    user_class = Class.objects.filter(form_master=user).first()
    if not user_class:
        return redirect('teacher:no_class_assigned')  # Or show a message

    posts = StudentPost.objects.filter(
        student__student_class=user_class
    ) | StudentPost.objects.filter(
        created_by=user
    )

    if request.method == 'POST':
        content = request.POST.get('content')
        if content:
            StudentPost.objects.create(
                content=content,
                created_by=user
            )
        return redirect('teacher:class_posts')

    return render(request, 'form_master/class_posts.html', {'posts': posts, 'form_master': user})



@login_required
@role_required('teacher')
def delete_post(request, post_id):
    post = get_object_or_404(StudentPost, id=post_id)
    
    
    post.delete()
    
    return redirect('teacher:class_posts')

@login_required
@role_required('teacher')
def no_class_assigned(request):
    return render(request, 'form_master/no_class_assigned.html')


def upcoming_feature(request):
    return render(request, "dashboard/upcoming.html")