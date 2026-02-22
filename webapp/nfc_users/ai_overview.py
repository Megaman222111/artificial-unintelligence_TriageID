"""
AI overview for patients using the OpenAI client pointed at Ark Labs.
Requires AI_OVERVIEW_API_KEY and AI_OVERVIEW_BASE_URL in webapp/.env.
Optional: AI_OVERVIEW_MODEL (default: gpt-4o).
"""
from __future__ import annotations

import json
import os
from typing import Any


class AiOverviewError(RuntimeError):
    pass


def _get_config() -> tuple[str, str, str]:
    api_key = (os.getenv("AI_OVERVIEW_API_KEY") or "").strip().strip("'\"")
    if not api_key:
        raise AiOverviewError("AI_OVERVIEW_API_KEY is not set in webapp/.env")
    base_url = (os.getenv("AI_OVERVIEW_BASE_URL") or "https://api.ark-labs.cloud/api/v1").strip().rstrip("/")
    model = (os.getenv("AI_OVERVIEW_MODEL") or "gpt-4o").strip() or "gpt-4o"
    return api_key, base_url, model


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
    notes = _clean_list(getattr(patient, "notes", []))
    if notes:
        lines.append(f"Notes: {'; '.join(notes)}")
    if prediction is not None:
        prob = getattr(prediction, "risk_probability", None)
        band = getattr(prediction, "risk_band", None)
        if prob is not None and band is not None:
            lines.append(f"Readmission risk: {band} ({float(prob)*100:.1f}%)")

    return "\n".join(lines)


def generate_ai_overview(patient: Any, prediction: Any | None = None) -> str:
    try:
        from openai import OpenAI
    except ImportError as exc:
        raise AiOverviewError("openai package is not installed. Run: pip install openai") from exc

    api_key, base_url, model = _get_config()
    client = OpenAI(api_key=api_key, base_url=base_url, timeout=60)

    patient_text = _build_prompt(patient, prediction)

    try:
        response = client.chat.completions.create(
            model=model,
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are a clinical assistant. "
                        "Write a concise 2-4 sentence patient overview in plain language. "
                        "Use only the provided data. Do not invent facts. "
                        "Reply with only the summary, no preamble or reasoning."
                    ),
                },
                {
                    "role": "user",
                    "content": f"Patient record:\n{patient_text}",
                },
            ],
            max_tokens=300,
            temperature=0.4,
        )
    except Exception as exc:
        raise AiOverviewError(f"AI overview API call failed: {exc}") from exc

    if not response.choices:
        raise AiOverviewError("AI overview API returned no choices")

    content = (response.choices[0].message.content or "").strip()
    # Strip chain-of-thought blocks like <think>...</think>
    if "</think>" in content:
        content = content[content.rfind("</think>") + 8:].strip()

    return content
