from django.urls import path
from .views import ClientListCreateView, ClientDetailView

urlpatterns = [
    path("clients/", ClientListCreateView.as_view(), name="clients_list_create"),
    path("clients/<uuid:client_id>/", ClientDetailView.as_view(), name="clients_detail"),
]
