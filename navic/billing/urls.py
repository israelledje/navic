from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    BillingPackageViewSet, DeviceTariffPlanViewSet, SubscriptionViewSet, 
    PaymentViewSet, InvoiceViewSet
)

router = DefaultRouter()
router.register(r'packages', BillingPackageViewSet, basename='billingpackage')
router.register(r'device-plans', DeviceTariffPlanViewSet, basename='devicetariffplan')
router.register(r'subscriptions', SubscriptionViewSet, basename='subscription')
router.register(r'payments', PaymentViewSet, basename='payment')
router.register(r'invoices', InvoiceViewSet, basename='invoice')

urlpatterns = [
    path('', include(router.urls)),
]
