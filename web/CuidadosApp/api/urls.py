from django.urls import path

from . import views

urlpatterns = [
    path("timer-schedule", views.TimerScheduleView.as_view()),
    path("me", views.MeView.as_view()),
    path("capabilities", views.CapabilitiesView.as_view()),
    path("patients", views.PatientsView.as_view()),
    path("patients/<int:pk>", views.PatientView.as_view()),
    path("patients/<int:pk>/<str:action>/active", views.ActiveView.as_view()),
    path("patients/<int:pk>/daily/<str:kind>", views.DailyView.as_view()),
    path(
        "patients/<int:pk>/daily/<str:kind>/<int:object_pk>", views.DailyView.as_view()
    ),
    path("patients/<int:pk>/events", views.EventView.as_view()),
    path("patients/<int:pk>/posture", views.PostureView.as_view()),
    path("patients/<int:pk>/timer", views.TimerView.as_view()),
    path("patients/<int:pk>/history", views.HistoryView.as_view()),
    path(
        "patients/<int:pk>/history/<int:event_pk>/correction",
        views.CorrectionView.as_view(),
    ),
    path("agenda", views.AgendaView.as_view()),
    path("guides", views.GuidesView.as_view()),
    path("reminders", views.RemindersView.as_view()),
    path("capacity", views.CapacityView.as_view()),
]

from . import detection

urlpatterns += [
    path("patients/<int:pk>/phone-observations", detection.PhoneObservationsView.as_view()),
    path("patients/<int:pk>/nodes", detection.NodesView.as_view()),
    path("patients/<int:pk>/observations", detection.ObservationsView.as_view()),
    path("nodes/<uuid:node_id>/revoke", detection.RevokeNodeView.as_view()),
    path("edge/status", detection.EdgeView.as_view()),
    path("edge/observations", detection.EdgeView.as_view()),
]
from .devices import DevicesView, ReminderModeView

urlpatterns += [path("devices", DevicesView.as_view()), path("devices/reminder-mode", ReminderModeView.as_view())]
