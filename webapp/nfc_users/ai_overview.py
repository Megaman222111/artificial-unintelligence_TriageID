"""
AI overview via Ark Labs chat API.
Uses Ark-compatible auth headers (Bearer first, then x-api-key fallback).
"""
from __future__ import annotations

import json
import os
import ssl
import time
from functools import lru_cache
from urllib import error, request
from typing import Any


class AiOverviewError(RuntimeError):
    pass


def _clean_list(value: Any) -> list[str]:
    if not value:
        return []
    if isinstance(value, list):
        out: list[str] = []
        for item in value:
            if isinstance(item, dict):
                text = " ".join(str(v).strip() for v in item.values() if str(v).strip())
            else:
                text = str(item).strip()
            if text:
                out.append(text)
        return out
    text = str(value).strip()
    return [text] if text else []


def _normalize_api_key(raw: str) -> str:
    # Keep exact key value except surrounding quotes/spaces.
    return raw.strip().strip("'\"")


def _candidate_api_keys() -> list[str]:
    raw = _normalize_api_key(os.getenv("AI_OVERVIEW_API_KEY") or "")
    if not raw:
        return []
    keys = [raw]
    trimmed = raw.lstrip(".")
    if trimmed and trimmed != raw:
        keys.append(trimmed)
    return keys


def _get_config() -> tuple[list[str], str, str]:
    api_keys = _candidate_api_keys()
    if not api_keys:
        raise AiOverviewError("AI_OVERVIEW_API_KEY is not set in webapp/.env")

    base_url = (os.getenv("AI_OVERVIEW_BASE_URL") or "https://api.ark-labs.cloud/api/v1").strip().rstrip("/")
    if not base_url:
        raise AiOverviewError("AI_OVERVIEW_BASE_URL is not set in webapp/.env")

    model = (os.getenv("AI_OVERVIEW_MODEL") or "gpt-4o-mini").strip()
    return api_keys, base_url, model


@lru_cache(maxsize=1)
def _ssl_context() -> ssl.SSLContext:
    custom_bundle = (os.getenv("AI_OVERVIEW_CA_BUNDLE") or "").strip()
    if custom_bundle:
        return ssl.create_default_context(cafile=custom_bundle)
    try:
        import certifi

        return ssl.create_default_context(cafile=certifi.where())
    except Exception:
        return ssl.create_default_context()


def _post_json(url: str, payload: dict[str, Any], headers: dict[str, str]) -> dict[str, Any]:
    body = json.dumps(payload, ensure_ascii=True).encode("utf-8")
    req = request.Request(url=url, method="POST", data=body, headers=headers)
    try:
        with request.urlopen(req, timeout=45, context=_ssl_context()) as response:
            raw = response.read().decode("utf-8", errors="replace")
    except error.HTTPError as exc:
        raw = exc.read().decode("utf-8", errors="replace")
        detail = raw.strip().replace("\n", " ")[:400]
        raise AiOverviewError(
            f"Ark Labs API error ({exc.code}) at {url}: {detail or 'no response body'}"
        ) from exc
    except Exception as exc:
        raise AiOverviewError(f"Ark Labs request failed at {url}: {exc}") from exc

    try:
        parsed = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise AiOverviewError(f"Ark Labs API returned invalid JSON at {url}.") from exc
    if not isinstance(parsed, dict):
        raise AiOverviewError(f"Ark Labs API returned unexpected payload at {url}.")
    return parsed


def _extract_chat_content(payload: dict[str, Any]) -> str:
    choices = payload.get("choices")
    if not isinstance(choices, list) or not choices:
        return ""
    first = choices[0] if isinstance(choices[0], dict) else {}
    message = first.get("message") if isinstance(first, dict) else {}
    if not isinstance(message, dict):
        return ""
    content = message.get("content")
    if isinstance(content, str):
        return content.strip()
    if isinstance(content, list):
        parts: list[str] = []
        for item in content:
            if isinstance(item, dict):
                text = str(item.get("text", "")).strip()
                if text:
                    parts.append(text)
        return "\n".join(parts).strip()
    return ""


def _build_prompt(patient: Any, prediction: Any | None) -> str:
    lines: list[str] = []
    name = f"{getattr(patient, 'first_name', '') or ''} {getattr(patient, 'last_name', '') or ''}".strip()
    if name:
        lines.append(f"Patient: {name}")
    dob = getattr(patient, "date_of_birth", "") or ""
    gender = getattr(patient, "gender", "") or ""
    if dob or gender:
        lines.append(f"DOB: {dob}  Gender: {gender}")
    status = getattr(patient, "status", "") or ""
    admission = getattr(patient, "admission_date", "") or ""
    if status or admission:
        lines.append(f"Status: {status}  Admission: {admission}")

    diagnosis = getattr(patient, "primary_diagnosis", "") or ""
    if diagnosis:
        lines.append(f"Primary diagnosis: {diagnosis}")
    allergies = _clean_list(getattr(patient, "allergies", []))
    if allergies:
        lines.append(f"Allergies: {', '.join(allergies)}")
    medications = _clean_list(getattr(patient, "medications", []))
    if medications:
        lines.append(f"Medications: {', '.join(medications)}")
    history = _clean_list(getattr(patient, "medical_history", []))
    if history:
        lines.append(f"Medical history: {', '.join(history)}")

    if prediction is not None:
        prob = getattr(prediction, "risk_probability", None)
        band = getattr(prediction, "risk_band", None)
        if prob is not None and band is not None:
            lines.append(f"Deterioration risk: {band} ({float(prob) * 100:.1f}%)")
    return "\n".join(lines)


def build_fallback_overview(patient: Any, prediction: Any | None = None) -> str:
    first_name = str(getattr(patient, "first_name", "") or "").strip()
    last_name = str(getattr(patient, "last_name", "") or "").strip()
    full_name = f"{first_name} {last_name}".strip() or "Patient"

    status = str(getattr(patient, "status", "") or "active").strip().lower() or "active"
    diagnosis = str(getattr(patient, "primary_diagnosis", "") or "").strip()
    diagnosis_part = diagnosis if diagnosis else "no primary diagnosis documented"

    meds = _clean_list(getattr(patient, "medications", []))
    history = _clean_list(getattr(patient, "medical_history", []))

    risk_part = "Risk score unavailable."
    if prediction is not None:
        prob = getattr(prediction, "risk_probability", None)
        band = getattr(prediction, "risk_band", None)
        if prob is not None and band:
            risk_part = f"30-day deterioration risk is {band} at {float(prob) * 100:.1f}%."

    return (
        f"{full_name} is currently {status} with {diagnosis_part}. "
        f"{risk_part} "
        f"Medications listed: {len(meds)}. Medical history entries: {len(history)}."
    )


def generate_ai_overview(patient: Any, prediction: Any | None = None) -> str:
    api_keys, base_url, model = _get_config()
    url = f"{base_url}/chat/completions"
    base_headers = {
        "Content-Type": "application/json",
        "Accept": "application/json",
        "User-Agent": "hacked-2025-ai-overview/1.0",
    }
    auth_header_variants: list[dict[str, str]] = []
    for api_key in api_keys:
        auth_header_variants.append({"Authorization": f"Bearer {api_key}"})
        auth_header_variants.append({"x-api-key": api_key})

    messages = [
        {
            "role": "system",
            "content": (
                "You are a clinical assistant. Write a concise 2-4 sentence patient overview. "
                "Use only provided data. Do not invent facts. Return only the summary."
            ),
        },
        {
            "role": "user",
            "content": f"Patient record:\n{_build_prompt(patient, prediction)}",
        },
    ]

    last_error = "unknown error"
    for auth_headers in auth_header_variants:
        headers = {**base_headers, **auth_headers}
        for attempt in range(2):
            try:
                payload = {
                    "model": model,
                    "messages": messages,
                }
                response_payload = _post_json(url, payload, headers)
                text = _extract_chat_content(response_payload)
                if text:
                    return text
                last_error = f"empty content for model '{model}'"
                break
            except AiOverviewError as exc:
                last_error = str(exc)
                retryable = any(code in last_error for code in ("(500)", "(502)", "(503)", "(504)"))
                if retryable and attempt == 0:
                    time.sleep(0.4)
                    continue
                break

    raise AiOverviewError(f"AI overview API call failed: {last_error}")
