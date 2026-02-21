from __future__ import annotations

import json
import os
import ssl
from functools import lru_cache
from urllib import error, request
from typing import Any


class AiOverviewError(RuntimeError):
    pass


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


def _patient_payload(patient: Any, prediction: Any | None) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "id": str(getattr(patient, "id", "") or ""),
        "firstName": str(getattr(patient, "first_name", "") or ""),
        "lastName": str(getattr(patient, "last_name", "") or ""),
        "dateOfBirth": str(getattr(patient, "date_of_birth", "") or ""),
        "gender": str(getattr(patient, "gender", "") or ""),
        "status": str(getattr(patient, "status", "") or ""),
        "admissionDate": str(getattr(patient, "admission_date", "") or ""),
        "primaryDiagnosis": str(getattr(patient, "primary_diagnosis", "") or ""),
        "allergies": _clean_list(getattr(patient, "allergies", [])),
        "medications": _clean_list(getattr(patient, "medications", [])),
        "medicalHistory": _clean_list(getattr(patient, "medical_history", [])),
        "pastMedicalHistory": _clean_list(getattr(patient, "past_medical_history", [])),
        "notes": _clean_list(getattr(patient, "notes", [])),
    }
    if prediction is not None:
        payload["risk"] = {
            "probability": float(getattr(prediction, "risk_probability", 0.0)),
            "band": str(getattr(prediction, "risk_band", "")),
            "modelVersion": str(getattr(prediction, "model_version", "")),
            "scoringMode": str(getattr(prediction, "scoring_mode", "")),
            "topFactors": getattr(prediction, "top_factors", []),
        }
    return payload


def _require_config() -> tuple[str, str, str]:
    api_key = (os.getenv("AI_OVERVIEW_API_KEY") or "").strip()
    if not api_key:
        raise AiOverviewError(
            "AI overview API key is missing. Set AI_OVERVIEW_API_KEY."
        )
    model = (os.getenv("AI_OVERVIEW_MODEL") or "gpt-4o-mini").strip()
    base_url = (os.getenv("AI_OVERVIEW_BASE_URL") or "").strip()
    if not base_url:
        raise AiOverviewError("AI overview base URL is missing. Set AI_OVERVIEW_BASE_URL.")
    return api_key, model, base_url


def _candidate_api_keys(raw_key: str) -> list[str]:
    out: list[str] = []
    k1 = raw_key.strip()
    if k1:
        out.append(k1)
    # Common copy/paste issue: key copied with leading ".".
    k2 = k1.lstrip(".")
    if k2 and k2 not in out:
        out.append(k2)
    return out


def _auth_header_variants(raw_key: str) -> list[dict[str, str]]:
    variants: list[dict[str, str]] = []
    for key in _candidate_api_keys(raw_key):
        variants.append({"Authorization": f"Bearer {key}"})
        variants.append({"x-api-key": key})
        variants.append({"Authorization": key})
    # Deduplicate while preserving order.
    unique: list[dict[str, str]] = []
    seen: set[tuple[tuple[str, str], ...]] = set()
    for item in variants:
        tag = tuple(sorted(item.items()))
        if tag not in seen:
            seen.add(tag)
            unique.append(item)
    return unique


def _extract_text_content(content: Any) -> str:
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
    return str(content or "").strip()


def _post_json(url: str, payload: dict[str, Any], headers: dict[str, str]) -> dict[str, Any]:
    body = json.dumps(payload, ensure_ascii=True).encode("utf-8")
    req = request.Request(url=url, method="POST", data=body, headers=headers)
    try:
        with request.urlopen(req, timeout=45, context=_ssl_context()) as res:
            raw = res.read().decode("utf-8", errors="replace")
    except error.HTTPError as exc:
        raw = exc.read().decode("utf-8", errors="replace")
        detail = raw.strip().replace("\n", " ")[:300]
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


def _extract_from_chat_completions(payload: dict[str, Any]) -> str:
    choices = payload.get("choices")
    if not isinstance(choices, list) or not choices:
        return ""
    first = choices[0] if isinstance(choices[0], dict) else {}
    message = first.get("message") if isinstance(first, dict) else {}
    if not isinstance(message, dict):
        return ""
    return _extract_text_content(message.get("content"))


def _extract_from_responses(payload: dict[str, Any]) -> str:
    output_text = payload.get("output_text")
    if isinstance(output_text, str) and output_text.strip():
        return output_text.strip()

    output = payload.get("output")
    if not isinstance(output, list):
        return ""
    parts: list[str] = []
    for item in output:
        if not isinstance(item, dict):
            continue
        content = item.get("content")
        if not isinstance(content, list):
            continue
        for chunk in content:
            if not isinstance(chunk, dict):
                continue
            text = str(chunk.get("text", "")).strip()
            if text:
                parts.append(text)
    return "\n".join(parts).strip()


def generate_ai_overview(patient: Any, prediction: Any | None = None) -> str:
    api_key, model, base_url = _require_config()
    root = base_url.rstrip("/")
    base_headers = {
        "Content-Type": "application/json",
        "Accept": "application/json",
        "User-Agent": "hacked-2025-ai-overview/1.0",
    }

    patient_json = json.dumps(_patient_payload(patient, prediction), ensure_ascii=True, indent=2)
    system_prompt = (
        "You are a clinical assistant. Write a concise patient overview in plain language. "
        "Use only provided data. Do not invent facts."
    )
    user_prompt = f"Patient data:\n{patient_json}"

    errors: list[str] = []
    for auth_headers in _auth_header_variants(api_key):
        headers = {**base_headers, **auth_headers}

        try:
            chat_payload = _post_json(
                f"{root}/chat/completions",
                payload={
                    "model": model,
                    "messages": [
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt},
                    ],
                },
                headers=headers,
            )
            text = _extract_from_chat_completions(chat_payload)
            if text:
                return text
            errors.append("empty text from /chat/completions")
        except AiOverviewError as exc:
            errors.append(str(exc))

        try:
            responses_payload = _post_json(
                f"{root}/responses",
                payload={
                    "model": model,
                    "input": [
                        {"role": "system", "content": [{"type": "text", "text": system_prompt}]},
                        {"role": "user", "content": [{"type": "text", "text": user_prompt}]},
                    ],
                },
                headers=headers,
            )
            text = _extract_from_responses(responses_payload)
            if text:
                return text
            errors.append("empty text from /responses")
        except AiOverviewError as exc:
            errors.append(str(exc))

    detail = " | ".join(errors[:2]) if errors else "unknown error"
    raise AiOverviewError(f"AI overview generation failed: {detail}")
