"""
Doctor login API: email + password -> JWT; GET me with Bearer token.
"""
import json
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_GET, require_POST
from django.contrib.auth import authenticate, get_user_model

from .auth_jwt import make_access_token, decode_access_token

User = get_user_model()


def _user_to_json(user):
    return {
        "id": user.pk,
        "email": user.email or "",
        "firstName": user.first_name or "",
        "lastName": user.last_name or "",
    }


def _get_user_from_request(request):
    auth = request.headers.get("Authorization") or ""
    if not auth.startswith("Bearer "):
        return None
    token = auth[7:].strip()
    if not token:
        return None
    payload = decode_access_token(token)
    if not payload or payload.get("type") != "access":
        return None
    user_id = payload.get("sub")
    if user_id is None:
        return None
    try:
        return User.objects.get(pk=int(user_id))
    except (ValueError, User.DoesNotExist):
        return None


@csrf_exempt
@require_POST
def login(request):
    """
    POST /api/auth/login/
    Body: { "email": "...", "password": "..." }
    Returns: { "accessToken": "...", "user": { id, email, firstName, lastName } }
    Doctors are staff users; login by email (case-insensitive).
    """
    try:
        body = json.loads(request.body) if request.body else {}
    except json.JSONDecodeError:
        return JsonResponse({"detail": "Invalid JSON."}, status=400)

    email = (body.get("email") or "").strip()
    password = body.get("password") or ""

    if not email:
        return JsonResponse({"detail": "Email is required."}, status=400)
    if not password:
        return JsonResponse({"detail": "Password is required."}, status=400)

    user = User.objects.filter(email__iexact=email).first()
    if not user:
        return JsonResponse({"detail": "Invalid email or password."}, status=401)
    if not user.check_password(password):
        return JsonResponse({"detail": "Invalid email or password."}, status=401)
    if not user.is_active:
        return JsonResponse({"detail": "Account is disabled."}, status=401)
    if not user.is_staff:
        return JsonResponse(
            {"detail": "Only staff (doctors) can sign in here."},
            status=403,
        )

    access_token = make_access_token(user.pk, user.email or "")
    return JsonResponse({
        "accessToken": access_token,
        "user": _user_to_json(user),
    })


@require_GET
def me(request):
    """
    GET /api/auth/me/
    Authorization: Bearer <accessToken>
    Returns: { "user": { id, email, firstName, lastName } } or 401.
    """
    user = _get_user_from_request(request)
    if not user:
        return JsonResponse({"detail": "Invalid or missing token."}, status=401)
    return JsonResponse({"user": _user_to_json(user)})
