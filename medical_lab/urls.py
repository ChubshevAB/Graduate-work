from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

app_name = "medical_lab"

router = DefaultRouter()
router.register(r"patients", views.PatientViewSet)
router.register(r"analyses", views.AnalysisViewSet)

urlpatterns = [
    # API endpoints
    path("api/", include(router.urls)),
    path("api/overview/", views.api_overview, name="api_overview"),
    path("api/public/services/", views.public_services, name="public_services"),
    # HTML pages
    path("", views.home, name="home"),
    path("about/", views.about, name="about"),
    path("services/", views.services, name="services"),
    path("contacts/", views.contacts, name="contacts"),
    # Patient management
    path("patients/", views.patients_list, name="patients_list"),
    path("patients/create/", views.create_patient, name="create_patient"),
    path("patients/<int:patient_id>/", views.patient_detail, name="patient_detail"),
    path("patients/<int:patient_id>/edit/", views.edit_patient, name="edit_patient"),
    # Analysis management
    path("analyses/", views.analyses_list, name="analyses_list"),
    path("analyses/create/", views.create_analysis, name="create_analysis"),
    path("analyses/<int:analysis_id>/", views.analysis_detail, name="analysis_detail"),
    path("analyses/<int:analysis_id>/edit/", views.edit_analysis, name="edit_analysis"),
    path(
        "analyses/<int:analysis_id>/result/",
        views.add_analysis_result,
        name="add_analysis_result",
    ),
    # Reports
    path("reports/", views.reports, name="reports"),
]
