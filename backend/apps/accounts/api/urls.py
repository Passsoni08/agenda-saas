from django.urls import path
from .views import MeView, SignupView, TenantPingView

urlpatterns = [
    path("me/", MeView.as_view(), name="me"),
    path("signup/", SignupView.as_view(), name="signup"),
    path("tenant/ping/", TenantPingView.as_view(), name="tenant_ping"),
]
