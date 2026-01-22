from django.urls import path

from .views import (
    AppointmentCancelView,
    AppointmentCreateView,
    AppointmentDayListView,
    AppointmentDetailView,
    AppointmentRangeListView,
    AppointmentRescheduleView,
)
from .views_services import ServiceDetailUpdateView, ServiceListCreateView
from apps.scheduling.api.views_availability import AppointmentAvailabilityView
from apps.scheduling.api.views_agenda import AgendaDayView
from .views_agenda_range import AgendaRangeView


urlpatterns = [
    path(
        "appointments/day/",
        AppointmentDayListView.as_view(),
        name="appointments_day",
    ),
    path(
        "appointments/range/",
        AppointmentRangeListView.as_view(),
        name="appointments_range",
    ),
    path("appointments/", AppointmentCreateView.as_view(), name="appointments_create"),
    path(
        "appointments/<uuid:appointment_id>/",
        AppointmentDetailView.as_view(),
        name="appointments_detail",
    ),
    path(
        "appointments/<uuid:appointment_id>/cancel/",
        AppointmentCancelView.as_view(),
        name="appointments_cancel",
    ),
    path(
        "appointments/<uuid:appointment_id>/reschedule/",
        AppointmentRescheduleView.as_view(),
        name="appointments_reschedule",
    ),

    path("services/", ServiceListCreateView.as_view(), name="services_list_create"),
    path(
        "services/<uuid:service_id>/",
        ServiceDetailUpdateView.as_view(),
        name="services_detail_update",
    ),
    path(
        "appointments/availability/",
        AppointmentAvailabilityView.as_view(),
        name="appointments_availability",
    ),
    path(
        "agenda/day/",
        AgendaDayView.as_view(),
        name="agenda_day"
    ),
    path(
        "agenda/range/",
        AgendaRangeView.as_view(),
        name="agenda_range"
    ),
]
