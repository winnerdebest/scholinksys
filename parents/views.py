from django.shortcuts import render, get_object_or_404, redirect
import uuid
import requests
from django.conf import settings
from django.views import View
from django.http import HttpResponse
from django.contrib.auth.decorators import login_required

from academic_main.decorators import role_required
# App models imports
from stu_main.models import *
from academic_main.models import *
from teacher_logic.models import *
from principal.models import *

from django.db.models import Sum, F, Q
from datetime import datetime
from django.views.generic import TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin
from decimal import Decimal

#for sending mails 
from django.core.mail import send_mail



def parents_dashboard(request):
    return render(request, 'parents_dashboard.html')


@login_required
@role_required('parent')
def children_page(request):
    # Get the parent profile associated with the logged-in user
    parent = get_object_or_404(Parent, user=request.user)
    
    # Get all children associated with this parent through the ManyToMany relationship
    children = Student.objects.filter(parents=parent).select_related(
        'user',
        'student_class',
        'student_class__school'
    )
    
    children_data = []
    for child in children:
        # Get active term
        active_term = ActiveTerm.objects.filter(school=child.student_class.school).first()
        if active_term:
            term = active_term.term
            
            # Get academic performance
            class_grade = ClassGradeSummary.objects.filter(
                student=child.user,
                term=term,
                student_class=child.student_class
            ).first()
            
            subject_grades = SubjectGradeSummary.objects.filter(
                student=child.user,
                term=term
            ).select_related('class_subject', 'class_subject__subject')[:3]
            
            # Get fee payment status
            class_fee = ClassFee.objects.filter(
                school_class=child.student_class,
                term=term
            ).first()
            
            fee_payments = FeePayment.objects.filter(
                student=child,
                term=term
            ).aggregate(
                total_amount=Sum('amount'),
                total_paid=Sum('amount_paid')
            )
            
            payment_status = 'unpaid'
            if fee_payments['total_paid']:
                if fee_payments['total_paid'] >= fee_payments['total_amount']:
                    payment_status = 'paid'
                elif fee_payments['total_paid'] > 0:
                    payment_status = 'partial'
            
            children_data.append({
                'student': child,
                'grade_summary': class_grade,
                'recent_grades': subject_grades,
                'fee_status': payment_status,
                'term': term
            })
    
    context = {
        'children': children_data,
        'parent': parent
    }
    
    return render(request, 'children_page.html', context)




class ParentFeeOverviewView(LoginRequiredMixin, TemplateView):
    template_name = "payments/payments.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        parent = get_object_or_404(Parent, user=self.request.user)
        selected_term_id = self.request.GET.get('term')

        # Get term either from selected_term_id or fallback to active term
        if selected_term_id:
            term = get_object_or_404(Term, id=selected_term_id)
        else:
            active_term_obj = ActiveTerm.objects.first()
            if active_term_obj:
                term = active_term_obj.term
            else:
                raise Http404("No active term set and no term selected.")

        fee_data = []

        for student in parent.children.all():
            student_data = {
                'student': student,
                'class_fee': {},
                'additional_fees': [],
            }

            # Get class fee for this student's class (no term filter now)
            class_fee_obj = ClassFee.objects.filter(school_class=student.student_class).first()
            if class_fee_obj:
                # Get discount for student by term and class
                discount_qs = StudentDiscount.objects.filter(
                    student=student,
                    term=term,
                    school_class=student.student_class,
                    is_active=True
                ).first()

                original_amount = class_fee_obj.amount
                discount_amount = Decimal('0.00')
                if discount_qs:
                    discount_amount = discount_qs.calculate_discount_amount(original_amount)

                expected_amount = original_amount - discount_amount

                # Payment filtering by student, class_fee, and term (if your payment model supports term)
                payment = FeePayment.objects.filter(
                    student=student,
                    class_fee=class_fee_obj,
                    term=term  # Assuming FeePayment has a term field to track payment per term
                ).first()

                paid = payment.amount_paid if payment else Decimal('0.00')

                student_data['class_fee'] = {
                    'original': original_amount,
                    'discount': discount_amount,
                    'expected': expected_amount,
                    'paid': paid,
                    'balance': expected_amount - paid,
                    'status': payment.payment_status if payment else 'unpaid'
                }

            # Handle additional fees (no term filter on AdditionalFee)
            additional_fees = AdditionalFee.objects.filter(
                models.Q(is_general=True) | models.Q(applicable_classes=student.student_class)
            ).distinct()

            for add_fee in additional_fees:
                payment = FeePayment.objects.filter(
                    student=student,
                    additional_fee=add_fee,
                    term=term  # Again assuming FeePayment tracks term per payment
                ).first()

                paid = payment.amount_paid if payment else Decimal('0.00')

                student_data['additional_fees'].append({
                    'name': add_fee.name,
                    'amount': add_fee.amount,
                    'paid': paid,
                    'balance': add_fee.amount - paid,
                    'status': payment.payment_status if payment else 'unpaid'
                })

            fee_data.append(student_data)

        context.update({
            'term': term,
            'fee_data': fee_data
        })

        return context




class SelectPaymentAmountView(View):
    def get(self, request, student_id, fee_type, fee_id, term_id):
        student = Student.objects.get(id=student_id)
        term = Term.objects.get(id=term_id)
        if fee_type == 'class':
            fee = ClassFee.objects.get(id=fee_id)
            paid = FeePayment.objects.filter(student=student, class_fee=fee, term=term).aggregate(total=models.Sum("amount_paid"))['total'] or Decimal("0.00")
            balance = fee.amount - paid
        else:
            fee = AdditionalFee.objects.get(id=fee_id)
            paid = FeePayment.objects.filter(student=student, additional_fee=fee, term=term).aggregate(total=models.Sum("amount_paid"))['total'] or Decimal("0.00")
            balance = fee.amount - paid

        return render(request, "payments/select_payment_amount.html", {
            "student": student,
            "term": term,
            "fee": fee,
            "fee_type": fee_type,
            "fee_id": fee_id,
            "balance": balance,
        })

    def post(self, request, student_id, fee_type, fee_id, term_id):
        student = Student.objects.get(id=student_id)
        term = Term.objects.get(id=term_id)
        amount = Decimal(request.POST.get('amount'))

        # Validate balance
        if fee_type == 'class':
            fee = ClassFee.objects.get(id=fee_id)
            paid = FeePayment.objects.filter(student=student, class_fee=fee, term=term).aggregate(total=models.Sum("amount_paid"))['total'] or Decimal("0.00")
            balance = fee.amount - paid
        else:
            fee = AdditionalFee.objects.get(id=fee_id)
            paid = FeePayment.objects.filter(student=student, additional_fee=fee, term=term).aggregate(total=models.Sum("amount_paid"))['total'] or Decimal("0.00")
            balance = fee.amount - paid

        if amount > balance:
            return HttpResponse("Amount exceeds balance", status=400)

        return redirect(
            f"/start-payment/?student_id={student.id}&term_id={term.id}&fee_type={fee_type}&fee_id={fee_id}&amount={amount}"
        )


class StartPaymentView(View):
    def get(self, request):
        student_id = request.GET.get('student_id')
        term_id = request.GET.get('term_id')
        fee_type = request.GET.get('fee_type')
        fee_id = request.GET.get('fee_id')
        amount = Decimal(request.GET.get('amount'))

        student = Student.objects.get(id=student_id)
        term = Term.objects.get(id=term_id)

        reference = str(uuid.uuid4())
        callback_url = request.build_absolute_uri(reverse('flutterwave_callback'))

        payment = FeePayment.objects.create(
            student=student,
            term=term,
            class_fee_id=fee_id if fee_type == 'class' else None,
            additional_fee_id=fee_id if fee_type == 'additional' else None,
            amount_paid=amount,
            flutterwave_ref=reference,
            payment_status='pending',
        )

        headers = {
            "Authorization": f"Bearer {settings.FLUTTERWAVE_SECRET_KEY}",
            "Content-Type": "application/json"
        }

        payload = {
            "tx_ref": reference,
            "amount": str(amount),
            "currency": "NGN",
            "redirect_url": callback_url,
            "customer": {
                "email": student.parent.user.email,
                "name": student.full_name
            },
            "customizations": {
                "title": "Scholink Fee Payment",
                "description": f"{fee_type.title()} Fee for {student.full_name}"
            }
        }

        response = requests.post("https://api.flutterwave.com/v3/payments", json=payload, headers=headers)
        data = response.json()

        if data["status"] == "success":
            return redirect(data["data"]["link"])
        return HttpResponse("Unable to initiate payment", status=400)




class FlutterwaveCallbackView(View):
    def get(self, request):
        tx_ref = request.GET.get('tx_ref')
        status = request.GET.get('status')

        payment = get_object_or_404(FeePayment, flutterwave_ref=tx_ref)

        if status != "successful":
            payment.payment_status = "failed"
            payment.save()
            return render(request, "payment_failed.html")

        # Step 1: Verify with Flutterwave
        headers = {
            "Authorization": f"Bearer {settings.FLUTTERWAVE_SECRET_KEY}",
        }
        verify_url = f"https://api.flutterwave.com/v3/transactions/verify_by_reference?tx_ref={tx_ref}"
        res = requests.get(verify_url, headers=headers)
        res_data = res.json()

        if res_data["status"] != "success":
            payment.payment_status = "failed"
            payment.save()
            return HttpResponse("Payment not verified", status=400)

        charge_amount = Decimal(str(res_data["data"]["amount"]))
        if charge_amount != payment.amount_paid:
            payment.payment_status = "failed"
            payment.save()
            return HttpResponse("Amount mismatch", status=400)

        # Step 2: Mark this payment as successful
        payment.payment_status = "paid"
        payment.save()

        # Step 3: Check total paid so far for this student+fee+term
        student = payment.student
        term = payment.term

        if payment.class_fee:
            fee = payment.class_fee
            fee_type = "class"
            total_fee = fee.amount
            total_paid = FeePayment.objects.filter(
                student=student, class_fee=fee, term=term, payment_status="paid"
            ).aggregate(total=models.Sum("amount_paid"))["total"] or Decimal("0.00")
        else:
            fee = payment.additional_fee
            fee_type = "additional"
            total_fee = fee.amount
            total_paid = FeePayment.objects.filter(
                student=student, additional_fee=fee, term=term, payment_status="paid"
            ).aggregate(total=models.Sum("amount_paid"))["total"] or Decimal("0.00")

        balance = total_fee - total_paid

        # Step 4: Send confirmation email
        subject = f"Payment Received - Scholink"
        if balance <= 0:
            message = (
                f"Dear Parent,\n\nWe have received your full payment of ₦{total_paid} for {student.full_name} "
                f"({fee_type.title()} Fee). Thank you!\n\nScholink."
            )
        else:
            message = (
                f"Dear Parent,\n\nWe have received a partial payment of ₦{payment.amount_paid} for {student.full_name} "
                f"({fee_type.title()} Fee). Outstanding balance: ₦{balance}.\n\nScholink."
            )

        send_mail(
            subject=subject,
            message=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[student.parent.user.email],
        )

        return render(request, "payment_success.html", {
            "payment": payment,
            "total_paid": total_paid,
            "balance": balance,
            "fee_type": fee_type,
            "student": student,
        })




def messages(request):
    return render(request, 'messages.html')
