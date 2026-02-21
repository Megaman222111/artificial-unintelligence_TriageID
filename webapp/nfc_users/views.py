"""
REST API for NFC user lookup, create, and Patient API for React frontend.
"""
import json
import logging
import subprocess
import urllib.error
import urllib.request
from django.conf import settings

logger = logging.getLogger(__name__)
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_GET, require_POST, require_http_methods

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


def _patient_api_dict_from_body(body):
    """Build patient field dict from JSON body (camelCase or snake_case)."""
    def get(key_camel, key_snake=None):
        k = key_snake or key_camel
        return body.get(key_camel) if body.get(key_camel) is not None else body.get(k)
    return {
        "first_name": (get("firstName", "first_name") or "").strip() or None,
        "last_name": (get("lastName", "last_name") or "").strip() or None,
        "date_of_birth": get("dateOfBirth", "date_of_birth") or "",
        "gender": get("gender") or "",
        "blood_type": get("bloodType", "blood_type") or "",
        "status": get("status") or "active",
        "room": get("room") or "",
        "admission_date": get("admissionDate", "admission_date") or "",
        "primary_diagnosis": get("primaryDiagnosis", "primary_diagnosis") or "",
        "insurance_provider": get("insuranceProvider", "insurance_provider") or "",
        "insurance_id": get("insuranceId", "insurance_id") or "",
        "use_alberta_health_card": get("useAlbertaHealthCard", "use_alberta_health_card") if get("useAlbertaHealthCard", "use_alberta_health_card") is not None else None,
        "alberta_health_card_number": get("albertaHealthCardNumber", "alberta_health_card_number") or "",
        "allergies": get("allergies") if get("allergies") is not None else [],
        "emergency_contact": get("emergencyContact", "emergency_contact") if get("emergencyContact", "emergency_contact") is not None else {},
        "medications": get("medications") if get("medications") is not None else [],
        "current_prescriptions": get("currentPrescriptions", "current_prescriptions") if get("currentPrescriptions", "current_prescriptions") is not None else [],
        "medical_history": get("medicalHistory", "medical_history") if get("medicalHistory", "medical_history") is not None else [],
        "past_medical_history": get("pastMedicalHistory", "past_medical_history") if get("pastMedicalHistory", "past_medical_history") is not None else [],
        "notes": get("notes") if get("notes") is not None else [],
    }


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


@csrf_exempt
@require_http_methods(["PUT", "PATCH"])
def patient_update(request, patient_id: str):
    """PUT/PATCH /api/patients/<id>/ – Update patient (full or partial)."""
    try:
        body = json.loads(request.body) if request.body else {}
    except json.JSONDecodeError:
        return JsonResponse({"detail": "Invalid JSON."}, status=400)

    try:
        p = Patient.objects.get(pk=patient_id.strip())
    except Patient.DoesNotExist:
        return JsonResponse(
            {"detail": f"Patient '{patient_id}' not found."},
            status=404,
        )

    data = _patient_api_dict_from_body(body)
    for key, value in data.items():
        if value is not None:
            setattr(p, key, value)
    p.save()
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
def patient_create(request):
    """
    POST /api/patients/create/ – Create a patient (e.g. when scanning an empty card).
    Body: JSON with nfcId (required), firstName, lastName (required); optional room, etc.
    Uses nfc_id as patient id. Other fields get sensible defaults.
    """
    try:
        body = json.loads(request.body) if request.body else {}
    except json.JSONDecodeError:
        return JsonResponse({"detail": "Invalid JSON."}, status=400)

    nfc_id = (body.get("nfcId") or body.get("nfc_id") or "").strip()[:15]
    first_name = (body.get("firstName") or body.get("first_name") or "").strip()
    last_name = (body.get("lastName") or body.get("last_name") or "").strip()

    if not nfc_id:
        return JsonResponse({"detail": "nfcId is required."}, status=400)
    if not first_name:
        return JsonResponse({"detail": "firstName is required."}, status=400)
    if not last_name:
        return JsonResponse({"detail": "lastName is required."}, status=400)

    if Patient.objects.filter(nfc_id=nfc_id).exists():
        return JsonResponse(
            {"detail": f"A patient is already linked to NFC tag '{nfc_id}'."},
            status=409,
        )

    patient_id = nfc_id
    p = Patient(
        id=patient_id,
        nfc_id=nfc_id,
        first_name=first_name,
        last_name=last_name,
        date_of_birth=body.get("dateOfBirth") or body.get("date_of_birth") or "",
        gender=body.get("gender") or "",
        blood_type=body.get("bloodType") or body.get("blood_type") or "",
        status=body.get("status") or "active",
        room=body.get("room") or "",
        admission_date=body.get("admissionDate") or body.get("admission_date") or "",
        primary_diagnosis=body.get("primaryDiagnosis") or body.get("primary_diagnosis") or "",
        insurance_provider=body.get("insuranceProvider") or body.get("insurance_provider") or "",
        insurance_id=body.get("insuranceId") or body.get("insurance_id") or "",
        use_alberta_health_card=body.get("useAlbertaHealthCard") or body.get("use_alberta_health_card") or False,
        alberta_health_card_number=(body.get("albertaHealthCardNumber") or body.get("alberta_health_card_number") or "").strip()[:32],
        allergies=body.get("allergies") or [],
        emergency_contact=body.get("emergencyContact") or body.get("emergency_contact") or {},
        medications=body.get("medications") or [],
        current_prescriptions=body.get("currentPrescriptions") or [],
        medical_history=body.get("medicalHistory") or body.get("medical_history") or [],
        past_medical_history=body.get("pastMedicalHistory") or body.get("past_medical_history") or [],
        notes=body.get("notes") or [],
    )
    p.save()
    return JsonResponse(p.to_api_dict(), status=201)


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


def _patient_text_summary(api_dict):
    """Build a plain-text summary of patient data for the AI overview prompt."""
    parts = []
    parts.append(f"Patient: {api_dict.get('firstName', '')} {api_dict.get('lastName', '')} (ID: {api_dict.get('id', '')})")
    parts.append(f"Status: {api_dict.get('status', '')}; Room: {api_dict.get('room', '')}; Admission: {api_dict.get('admissionDate', '')}")
    parts.append(f"DOB: {api_dict.get('dateOfBirth', '')}; Gender: {api_dict.get('gender', '')}; Blood type: {api_dict.get('bloodType', '')}")
    if api_dict.get("primaryDiagnosis"):
        parts.append(f"Primary diagnosis: {api_dict['primaryDiagnosis']}")
    if api_dict.get("allergies"):
        parts.append(f"Allergies: {', '.join(api_dict['allergies'])}")
    if api_dict.get("medications"):
        meds = [f"{m.get('name', '')} ({m.get('dosage', '')})" for m in api_dict["medications"]]
        parts.append(f"Medications: {'; '.join(meds)}")
    ec = api_dict.get("emergencyContact") or {}
    if ec.get("name"):
        parts.append(f"Emergency contact: {ec.get('name')} ({ec.get('relationship')}) {ec.get('phone', '')}")
    if api_dict.get("medicalHistory"):
        parts.append(f"Medical history: {', '.join(api_dict['medicalHistory'])}")
    if api_dict.get("notes"):
        parts.append(f"Notes: {'; '.join(api_dict['notes'])}")
    return "\n".join(parts)


@csrf_exempt
@require_POST
def patient_ai_overview(request):
    """
    POST /api/patients/ai-overview/ – Get an AI-generated clinical overview for a patient.
    Body: JSON with patient_id. Uses Ark Labs API (chat completions).
    """
    try:
        body = json.loads(request.body) if request.body else {}
    except json.JSONDecodeError:
        return JsonResponse({"detail": "Invalid JSON."}, status=400)

    patient_id = (body.get("patient_id") or body.get("patientId") or "").strip()
    if not patient_id:
        return JsonResponse({"detail": "patient_id is required."}, status=400)

    try:
        p = Patient.objects.get(pk=patient_id)
    except Patient.DoesNotExist:
        return JsonResponse(
            {"detail": f"Patient '{patient_id}' not found."},
            status=404,
        )

    api_url = getattr(settings, "ARK_LABS_API_URL", "").strip() or "https://api.ark-labs.cloud/api/v1/chat/completions"
    api_key = getattr(settings, "ARK_LABS_API_KEY", "").strip()
    model = getattr(settings, "ARK_LABS_MODEL", "gpt-4o").strip() or "gpt-4o"
    summary = _patient_text_summary(p.to_api_dict())
    prompt = (
        "You are a clinical assistant. Based on the following patient record, provide a brief, "
        "clear clinical overview in 2–4 sentences. Highlight key risks (e.g. allergies), current "
        "diagnosis, and the most relevant care points. Use plain language.\n\nPatient record:\n"
    ) + summary

    payload = {
        "model": model,
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.7,
    }
    body_json = json.dumps(payload)

    content = ""
    error_detail = None
    try:
        if not api_key:
            error_detail = "ARK_LABS_API_KEY is not set. Add it to webapp/.env"
        else:
            # Use curl so the request matches the working command exactly
            proc = subprocess.run(
                [
                    "curl",
                    "-s",
                    "-X",
                    "POST",
                    api_url,
                    "-H",
                    "Content-Type: application/json",
                    "-H",
                    f"Authorization: Bearer {api_key}",
                    "-d",
                    body_json,
                ],
                capture_output=True,
                text=True,
                timeout=90,
            )
            out = (proc.stdout or "").strip()
            err = (proc.stderr or "").strip()
            if err:
                logger.warning("Ark Labs curl stderr: %s", err[:500])
            if proc.returncode != 0:
                error_detail = err or f"curl exited {proc.returncode}"
            else:
                result = json.loads(out) if out else {}
                if result.get("error"):
                    err_obj = result["error"]
                    error_detail = (
                        err_obj.get("message") if isinstance(err_obj, dict) else str(err_obj)
                    )
                else:
                    choices = result.get("choices") or []
                    if choices:
                        msg = choices[0].get("message") or {}
                        content = (msg.get("content") or "").strip()
    except subprocess.TimeoutExpired:
        error_detail = "Request timed out"
        logger.warning("Ark Labs curl timed out")
    except json.JSONDecodeError as e:
        error_detail = f"Invalid response: {e}"
        logger.warning("Ark Labs response not JSON", exc_info=True)
    except FileNotFoundError:
        error_detail = "curl not found. Install curl or use a system that has it."
        logger.warning("curl not found")
    except Exception as e:
        error_detail = str(e) if e else "Request failed"
        logger.warning("Ark Labs request failed: %s", error_detail, exc_info=True)

    if error_detail:
        if not api_key:
            logger.warning("AI overview: ARK_LABS_API_KEY not set (check webapp/.env and restart runserver)")
        return JsonResponse({"overview": "", "error": error_detail}, status=503)
    return JsonResponse({"overview": content or ""})
