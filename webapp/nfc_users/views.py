"""
REST API for NFC user lookup, create, and Patient API for React frontend.
"""
import json
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_GET, require_POST

from .models import UserProfile, Patient


def _get_user_json(profile):
    return profile.to_api_dict()


@require_GET
def user_by_id(request, user_id: str):
    """GET /api/users/<user_id>/ – Look up user by NFC user_id."""
    try:
        profile = UserProfile.objects.get(user_id=user_id.strip())
    except UserProfile.DoesNotExist:
        return JsonResponse(
            {"detail": f"No user found for ID '{user_id}'."},
            status=404,
        )
    return JsonResponse(_get_user_json(profile))


@require_GET
def user_list(request):
    """GET /api/users/ – List all users (user_id only for privacy, or full if needed)."""
    profiles = UserProfile.objects.all().order_by("user_id")
    return JsonResponse({
        "users": [p.to_api_dict() for p in profiles],
    })


@csrf_exempt
@require_POST
def user_create(request):
    """
    POST /api/users/ – Create a user.
    Body: JSON with userId (required), firstName, lastName, email, phone, notes.
    """
    try:
        body = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({"detail": "Invalid JSON."}, status=400)

    user_id = (body.get("userId") or "").strip()[:15]
    if not user_id:
        return JsonResponse({"detail": "userId is required (max 15 characters)."}, status=400)

    if UserProfile.objects.filter(user_id=user_id).exists():
        return JsonResponse(
            {"detail": f"A user with ID '{user_id}' already exists."},
            status=409,
        )

    profile = UserProfile(user_id=user_id)
    profile.set_plain_fields(
        first_name=body.get("firstName", ""),
        last_name=body.get("lastName", ""),
        email=body.get("email", ""),
        phone=body.get("phone", ""),
        notes=body.get("notes", ""),
    )
    profile.save()
    return JsonResponse(_get_user_json(profile), status=201)


# ----- Patient API (React frontend) -----

@require_GET
def patient_list(request):
    """GET /api/patients/ – List all patients."""
    patients = Patient.objects.all().order_by("id")
    return JsonResponse([p.to_api_dict() for p in patients], safe=False)


@require_GET
def patient_by_id(request, patient_id: str):
    """GET /api/patients/<id>/ – Get patient by id."""
    try:
        p = Patient.objects.get(pk=patient_id.strip())
    except Patient.DoesNotExist:
        return JsonResponse(
            {"detail": f"Patient '{patient_id}' not found."},
            status=404,
        )
    return JsonResponse(p.to_api_dict())


@require_GET
def patient_by_nfc(request, nfc_id: str):
    """GET /api/patients/by-nfc/<nfc_id>/ – Get patient by NFC tag id."""
    try:
        p = Patient.objects.get(nfc_id=nfc_id.strip())
    except Patient.DoesNotExist:
        return JsonResponse(
            {"detail": f"No patient mapped to NFC tag '{nfc_id}'."},
            status=404,
        )
    return JsonResponse(p.to_api_dict())


@csrf_exempt
@require_POST
def nfc_scan(request):
    """
    POST /api/nfc/scan/ – Look up patient by NFC tag id from reader.
    Body must include tag_id (the User ID read from the Arduino). Only returns
    patients that exist in the database for that nfc_id.
    """
    try:
        body = json.loads(request.body) if request.body else {}
    except json.JSONDecodeError:
        return JsonResponse({"detail": "Body must be valid JSON."}, status=400)

    tag_id = (body.get("tag_id") or "").strip()
    if not tag_id:
        return JsonResponse(
            {"detail": "tag_id is required. Use the NFC reader to get the User ID."},
            status=400,
        )

    try:
        p = Patient.objects.get(nfc_id=tag_id)
        return JsonResponse({"mode": "nfc-tag", "patient": p.to_api_dict()})
    except Patient.DoesNotExist:
        return JsonResponse(
            {"detail": f"No patient mapped to NFC tag '{tag_id}'."},
            status=404,
        )
