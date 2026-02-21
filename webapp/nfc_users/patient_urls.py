from django.http import JsonResponse
from django.urls import path
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods

from . import views


@csrf_exempt
@require_http_methods(["GET", "PUT", "PATCH"])
def patient_detail(request, patient_id: str):
    if request.method == "GET":
        return views.patient_by_id(request, patient_id)
    return views.patient_update(request, patient_id)


urlpatterns = [
    path("", views.patient_list),
    path("create/", views.patient_create),
    path("ai-overview/", views.patient_ai_overview),
    path("risk-score/", views.patient_risk_score),
    path("outcomes/", views.patient_outcome_create),
    path("by-nfc/<str:nfc_id>/", views.patient_by_nfc),
    path("<str:patient_id>/outcomes/", views.patient_outcome_list),
    path("<str:patient_id>/", patient_detail),
]
