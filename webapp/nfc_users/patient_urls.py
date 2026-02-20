from django.urls import path
from . import views

urlpatterns = [
    path("", views.patient_list),
    path("by-nfc/<str:nfc_id>/", views.patient_by_nfc),
    path("<str:patient_id>/", views.patient_by_id),
]
