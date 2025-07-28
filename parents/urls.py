from django.urls import path

from .views import *

app_name = 'parents'


urlpatterns = [
    path('', parents_dashboard, name='parents_dashboard'),
    path('your-kids/', children_page, name='children_page'),
    #path('payments/', payments_page, name='payments_page'),


    path('payments/', ParentFeeOverviewView.as_view(), name='payments_page'),
    path("select-payment-amount/<int:student_id>/<str:fee_type>/<int:fee_id>/<int:term_id>/",
        SelectPaymentAmountView.as_view(),
        name="select_payment_amount",
    ),
    path("start-payment/", StartPaymentView.as_view(), name="start_payment",),
    path("flutterwave/callback/", FlutterwaveCallbackView.as_view(), name="flutterwave_callback",),


    path('messages/', messages, name='messages'),



]
