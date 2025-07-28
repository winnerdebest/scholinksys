from .models import SubjectGradeSummary, ClassGradeSummary
from django.db.models import Avg
from stu_main.models import CustomUser

def generate_class_rankings(term, student_class):
    students = CustomUser.objects.filter(
        student_profile__student_class=student_class,
        user_type='student'
    )

    summaries = []

    for student in students:
        subject_summaries = SubjectGradeSummary.objects.filter(
            student=student,
            term=term,
            class_subject__school_class=student_class
        )

        if subject_summaries.exists():
            total = sum(s.total_score for s in subject_summaries)
            avg = total / subject_summaries.count()
        else:
            avg = 0

        summaries.append((student, avg))

    # Sort by average score descending
    summaries.sort(key=lambda x: x[1], reverse=True)

    # Save to DB with ranking
    for rank, (student, avg) in enumerate(summaries, start=1):
        summary, created = ClassGradeSummary.objects.get_or_create(
            student=student,
            student_class=student_class,
            term=term
        )
        summary.average_score = round(avg, 2)
        summary.rank = rank
        summary.save()
