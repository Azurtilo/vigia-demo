from django.urls import path

from . import views

app_name = "PrivacidadApp"
urlpatterns = [
    path("", views.PolicyView.as_view(), name="policy"),
    path("aceptar/", views.AcceptView.as_view(), name="accept"),
    path("mis-datos/", views.ExportAccountView.as_view(), name="export_account"),
    path("eliminar-cuenta/", views.DeleteAccountView.as_view(), name="delete_account"),
    path(
        "pacientes/<int:pk>/consentimiento/",
        views.ConsentView.as_view(),
        name="consent",
    ),
    path(
        "pacientes/<int:pk>/consentimiento/<str:scope>/revocar/",
        views.RevokeConsentView.as_view(),
        name="consent_revoke",
    ),
    path(
        "pacientes/<int:pk>/exportar/",
        views.ExportPatientView.as_view(),
        name="export_patient",
    ),
    path(
        "pacientes/<int:pk>/eliminar/",
        views.DeletePatientView.as_view(),
        name="delete_patient",
    ),
]
