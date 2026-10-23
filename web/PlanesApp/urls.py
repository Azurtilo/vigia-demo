from django.urls import path

from . import views

app_name = "PlanesApp"
urlpatterns = [
    path("", views.CatalogView.as_view(), name="catalogo"),
    path("mi-suscripcion/", views.SummaryView.as_view(), name="mi_suscripcion"),
    path("metodos/", views.MethodsView.as_view(), name="metodos"),
    path(
        "metodos/<int:pk>/predeterminado/",
        views.DefaultMethodView.as_view(),
        name="metodo_predeterminado",
    ),
    path(
        "metodos/<int:pk>/eliminar/",
        views.DeleteMethodView.as_view(),
        name="metodo_eliminar",
    ),
    path("contratar/<slug:code>/", views.CheckoutView.as_view(), name="contratar"),
    path("operaciones/<uuid:reference>/", views.ResultView.as_view(), name="resultado"),
    path("cancelar/", views.CancelView.as_view(), name="cancelar"),
    path(
        "retirar-cancelacion/", views.ResumeView.as_view(), name="retirar_cancelacion"
    ),
    path("renovar/", views.RenewView.as_view(), name="renovar"),
    path("historial/", views.HistoryView.as_view(), name="historial"),
]
