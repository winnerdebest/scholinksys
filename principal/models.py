from django.db import models
from academic_main.models import *
from stu_main.models import *
from django.core.validators import MinValueValidator
from django.utils import timezone
from decimal import Decimal
import uuid

class ExpenseCategory(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    school = models.ForeignKey(School, on_delete=models.CASCADE, related_name='expense_categories')

    class Meta:
        verbose_name_plural = "Expense Categories"
        unique_together = ('name', 'school')

    def __str__(self):
        return f"{self.name} - {self.school.name}"


class Expense(models.Model):
    PAYMENT_STATUS = (
        ('pending', 'Pending'),
        ('paid', 'Paid'),
        ('cancelled', 'Cancelled'),
    )

    school = models.ForeignKey(School, on_delete=models.CASCADE, related_name='expenses')
    category = models.ForeignKey(ExpenseCategory, on_delete=models.SET_NULL, null=True, related_name='expenses')
    amount = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0)])
    description = models.TextField()
    date = models.DateField()
    payment_status = models.CharField(max_length=10, choices=PAYMENT_STATUS, default='pending')
    payment_date = models.DateField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    receipt = models.FileField(upload_to='expense_receipts/', null=True, blank=True)

    def __str__(self):
        return f"{self.category.name if self.category else 'Uncategorized'} - {self.amount} ({self.date})"


class TeacherSalaryPayment(models.Model):
    teacher = models.ForeignKey(Teacher, on_delete=models.CASCADE, related_name='salary_payments')
    expense = models.OneToOneField(Expense, on_delete=models.CASCADE, related_name='teacher_salary')
    month = models.DateField(help_text="The month for which the salary is being paid")
    basic_salary = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0)])
    allowances = models.DecimalField(max_digits=10, decimal_places=2, default=0, validators=[MinValueValidator(0)])
    deductions = models.DecimalField(max_digits=10, decimal_places=2, default=0, validators=[MinValueValidator(0)])
    comments = models.TextField(blank=True)

    class Meta:
        unique_together = ('teacher', 'month')

    def __str__(self):
        return f"Salary Payment - {self.teacher} - {self.month.strftime('%B %Y')}"

    @property
    def net_salary(self):
        return self.basic_salary + self.allowances - self.deductions

    def save(self, *args, **kwargs):
        if not self.expense_id:
            category, _ = ExpenseCategory.objects.get_or_create(
                name='Teacher Salary',
                school=self.teacher.school,
                defaults={'description': 'Teacher salary payments'}
            )
            self.expense = Expense.objects.create(
                school=self.teacher.school,
                category=category,
                amount=self.net_salary,
                description=f"Salary payment for {self.teacher} - {self.month.strftime('%B %Y')}",
                date=self.month,
            )
        else:
            self.expense.amount = self.net_salary
            self.expense.description = f"Salary payment for {self.teacher} - {self.month.strftime('%B %Y')}"
            self.expense.save()
        super().save(*args, **kwargs)


class Announcement(models.Model):
    PRIORITY_CHOICES = (
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
    )

    school = models.ForeignKey(School, on_delete=models.CASCADE, related_name='announcements')
    title = models.CharField(max_length=200)
    content = models.TextField()
    created_by = models.ForeignKey('stu_main.CustomUser', on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    priority = models.CharField(max_length=10, choices=PRIORITY_CHOICES, default='medium')
    is_active = models.BooleanField(default=True)
    expiry_date = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return self.title

    @property
    def is_expired(self):
        return self.expiry_date and timezone.now() > self.expiry_date



class ClassFee(models.Model):
    school_class = models.ForeignKey(Class, on_delete=models.CASCADE, related_name="class_fees")
    amount = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return f"{self.school_class.name} - {self.amount} Fee"


class AdditionalFee(models.Model):
    name = models.CharField(max_length=100)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    applicable_classes = models.ManyToManyField(Class, blank=True, related_name="additional_fees")
    is_general = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.name} - {self.amount}"


class StudentDiscount(models.Model):
    DISCOUNT_TYPE_CHOICES = (
        ('percentage', 'Percentage'),
        ('fixed', 'Fixed Amount'),
    )

    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name="discounts")
    term = models.ForeignKey(Term, on_delete=models.CASCADE, related_name="student_discounts")
    academic_year = models.CharField(max_length=9, null=True, blank=True)  # Format: 2023-2024
    school_class = models.ForeignKey(Class, on_delete=models.CASCADE, related_name="discounts", null=True, blank=True)

    discount_type = models.CharField(max_length=10, choices=DISCOUNT_TYPE_CHOICES, default='percentage')
    discount_value = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0)], null=True, blank=True)
    reason = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True, null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True, null=True, blank=True)

    class Meta:
        unique_together = ('student', 'term', 'academic_year', 'school_class')

    def __str__(self):
        return f"{self.student.user.get_full_name()} - Discount for {self.term.name}"

    def calculate_discount_amount(self, original_amount):
        if not self.is_active:
            return Decimal('0.00')
        if self.discount_type == 'percentage':
            return (original_amount * self.discount_value) / 100
        return min(self.discount_value, original_amount)


class FeePayment(models.Model):
    PAYMENT_STATUS = (
        ('paid', 'Paid'),
        ('partial', 'Partial'),
        ('unpaid', 'Unpaid'),
    )

    PAYMENT_METHOD = (
        ('cash', 'Cash'),
        ('bank_transfer', 'Bank Transfer'),
        ('card', 'Card'),
        ('other', 'Other'),
    )

    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='fee_payments')
    school = models.ForeignKey(School, on_delete=models.CASCADE, related_name='fee_payments')

    payment_type = models.CharField(
        max_length=20,
        choices=(('class_fee', 'Class Fee'), ('additional_fee', 'Additional Fee'))
    )

    class_fee = models.ForeignKey(
        ClassFee, on_delete=models.SET_NULL, null=True, blank=True, related_name="payments"
    )
    additional_fee = models.ForeignKey(
        AdditionalFee, on_delete=models.SET_NULL, null=True, blank=True, related_name='payments'
    )

    amount = models.DecimalField(max_digits=10, decimal_places=2)  # Final amount, includes discount if applicable
    amount_paid = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    payment_status = models.CharField(max_length=10, choices=PAYMENT_STATUS, default='unpaid')
    payment_method = models.CharField(max_length=20, choices=PAYMENT_METHOD)
    payment_date = models.DateField()

    term = models.ForeignKey(Term, on_delete=models.SET_NULL, null=True)
    academic_year = models.CharField(max_length=9)  # Format: 2023-2024
    receipt_number = models.CharField(max_length=20, unique=True)
    notes = models.TextField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-payment_date']
        constraints = [
            models.UniqueConstraint(fields=['student', 'class_fee'], name='unique_class_fee_payment'),
            models.UniqueConstraint(fields=['student', 'additional_fee'], name='unique_additional_fee_payment'),
        ]

    def __str__(self):
        return f"{self.student.user.get_full_name()} - {self.amount} ({self.payment_date})"

    def save(self, *args, **kwargs):
        if not self.receipt_number:
            self.receipt_number = f"FEE-{uuid.uuid4().hex[:8].upper()}"
        if self.amount_paid >= self.amount:
            self.payment_status = 'paid'
        elif self.amount_paid > 0:
            self.payment_status = 'partial'
        else:
            self.payment_status = 'unpaid'
        super().save(*args, **kwargs)

    @property
    def balance(self):
        return self.amount - self.amount_paid
