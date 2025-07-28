from django.db import models
from django.utils import timezone

# All models import 
from stu_main.models import *
from academic_main.models import *



class SubjectGradeSummary(models.Model):
    student = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='subject_grade_summaries')
    class_subject = models.ForeignKey(ClassSubject, on_delete=models.SET_NULL, related_name='grade_summaries', null=True, blank=True)
    term = models.ForeignKey(Term, on_delete=models.SET_NULL, related_name='subject_grade_summaries', null=True, blank=True)

    external_exam_score = models.FloatField(default=0)
    external_assignment_score = models.FloatField(default=0)   
    external_test_score = models.FloatField(default=0)

    def get_internal_exam_average(self):
        from exams.models import StudentExamRecord
        exam_records = StudentExamRecord.objects.filter(
            student=self.student,
            exam__class_subject=self.class_subject,
            exam__term=self.term,
        )
        scores = [r.score for r in exam_records]
        return sum(scores) / len(scores) if scores else 0

    def get_internal_assignment_average(self):
        from assignments.models import StudentAssignmentRecord  
        assignment_records = StudentAssignmentRecord.objects.filter(
            student=self.student,
            assignment__class_subject=self.class_subject,
            assignment__term=self.term,
        )
        scores = [r.score for r in assignment_records]
        return sum(scores) / len(scores) if scores else 0

    @property
    def total_score(self):
        internal_exam_avg = self.get_internal_exam_average()
        internal_assignment_avg = self.get_internal_assignment_average()

        # Get school's grading policy
        policy = GradingPolicy.objects.get(school=self.class_subject.school_class.school)
        
        # Calculate exam score using policy weights
        exam_internal_weight = (policy.exam_weight * policy.exam_internal_ratio) / 100
        exam_external_weight = (policy.exam_weight * (100 - policy.exam_internal_ratio)) / 100
        exam_score = ((internal_exam_avg / 100) * exam_internal_weight) + \
                    ((self.external_exam_score / 100) * exam_external_weight)

        # Calculate assignment score using policy weights
        assignment_internal_weight = (policy.assignment_weight * policy.assignment_internal_ratio) / 100
        assignment_external_weight = (policy.assignment_weight * (100 - policy.assignment_internal_ratio)) / 100
        assignment_score = ((internal_assignment_avg / 100) * assignment_internal_weight) + \
                         ((self.external_assignment_score / 100) * assignment_external_weight)

        # Calculate test score (external only)
        test_score = (self.external_test_score / 100) * policy.test_weight

        total = exam_score + assignment_score + test_score
        return round(total, 2)

    def __str__(self):
        return f"{self.student} - {self.class_subject} - {self.term}"


# This stores the Grade summary for all subjects for the student 
class ClassGradeSummary(models.Model):
    student = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='class_grade_summaries')
    term = models.ForeignKey(Term, on_delete=models.CASCADE, related_name='class_grade_summaries')
    student_class = models.ForeignKey(Class, on_delete=models.CASCADE, related_name='grade_summaries')

    average_score = models.FloatField(blank=True, null=True)
    rank = models.PositiveIntegerField(blank=True, null=True)

    class Meta:
        unique_together = ('student', 'term', 'student_class')
        ordering = ['-average_score'] 

    def __str__(self):
        return f"{self.student.get_full_name()} - {self.term} - Rank {self.rank}"


class GradingPolicy(models.Model):
    school = models.ForeignKey(School, on_delete=models.CASCADE, related_name='grading_policy')
    
    # Exam weights (60% total)
    exam_weight = models.FloatField(default=60)
    exam_internal_ratio = models.FloatField(default=50)  # percentage split for internal
    
    # Assignment weights (20% total)
    assignment_weight = models.FloatField(default=20)
    assignment_internal_ratio = models.FloatField(default=50)  # percentage split for internal
    
    # Test weight (20%)
    test_weight = models.FloatField(default=20)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name_plural = "Grading Policies"
    
    def clean(self):
        # Validate total weights equal 100%
        total = self.exam_weight + self.assignment_weight + self.test_weight
        if total != 100:
            raise ValidationError("Total weights must equal 100%")
            
        # Validate ratios between 0-100
        for ratio in [self.exam_internal_ratio, self.assignment_internal_ratio]:
            if not 0 <= ratio <= 100:
                raise ValidationError("Internal/External ratios must be between 0 and 100")
    
    def save(self, *args, **kwargs):
        self.clean()
        super().save(*args, **kwargs)
    
    def __str__(self):
        return f"{self.school.name} Grading Policy"