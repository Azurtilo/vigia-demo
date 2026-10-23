from django.urls import path

from . import views

app_name = "CuidadosApp"
urlpatterns = [
    path("", views.PanelView.as_view(), name="panel"),
    path("pacientes/", views.PatientListView.as_view(), name="patients"),
    path("pacientes/nuevo/", views.PatientFormView.as_view(), name="patient_new"),
    path("pacientes/<int:pk>/", views.PatientDetailView.as_view(), name="patient"),
    path(
        "pacientes/<int:pk>/editar/",
        views.PatientFormView.as_view(),
        name="patient_edit",
    ),
    path("pacientes/<int:pk>/archivar/", views.ArchiveView.as_view(), name="archive"),
    path(
        "pacientes/<int:pk>/reactivar/",
        views.ReactivateView.as_view(),
        name="reactivate",
    ),
    path(
        "pacientes/<int:pk>/medicamentos/nuevo/",
        views.DailyFormView.as_view(),
        name="medication_new",
    ),
    path(
        "pacientes/<int:pk>/medicamentos/<int:object_pk>/",
        views.DailyFormView.as_view(),
        name="medication_edit",
    ),
    path(
        "pacientes/<int:pk>/cuidados/nuevo/",
        views.TaskFormView.as_view(),
        name="task_new",
    ),
    path(
        "pacientes/<int:pk>/cuidados/<int:object_pk>/",
        views.TaskFormView.as_view(),
        name="task_edit",
    ),
    path("pacientes/<int:pk>/postura/", views.PostureView.as_view(), name="posture"),
    path("pacientes/<int:pk>/reloj/", views.TimerView.as_view(), name="timer"),
    path("pacientes/<int:pk>/actividad/", views.DailyEventView.as_view(), name="event"),
    path("pacientes/<int:pk>/historial/", views.HistoryView.as_view(), name="history"),
    path(
        "pacientes/<int:pk>/historial/<int:event_pk>/corregir/",
        views.CorrectionView.as_view(),
        name="correction",
    ),
    path("agenda/", views.AgendaView.as_view(), name="agenda"),
    path("guias/", views.GuidesView.as_view(), name="guides"),
    path("pacientes-activos/", views.SelectionView.as_view(), name="selection"),
    path("avisos/", views.RemindersView.as_view(), name="reminders"),
    path("avisos/acuse/", views.ClaimView.as_view(), name="claim"),
]
