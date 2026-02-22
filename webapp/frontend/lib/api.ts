export interface Patient {
  id: string
  firstName: string
  lastName: string
  dateOfBirth: string
  gender: string
  bloodType: string
  nfcId: string
  status: "active" | "discharged" | "critical"
  room: string
  admissionDate: string
  allergies: string[]
  primaryDiagnosis: string
  insuranceProvider?: string
  insuranceId?: string
  useAlbertaHealthCard?: boolean
  albertaHealthCardNumber?: string
  emergencyContact: {
    name: string
    relationship: string
    phone: string
  }
  medications: {
    name: string
    dosage: string
    frequency: string
  }[]
  currentPrescriptions?: string[]
  medicalHistory: string[]
  pastMedicalHistory?: string[]
  importantTestResults?: string
  notes: string[]
}

import { getAccessToken } from "./auth"

const API_BASE_URL =
  process.env.NEXT_PUBLIC_DJANGO_API_BASE_URL ||
  process.env.DJANGO_API_BASE_URL ||
  "http://127.0.0.1:8000"

async function fetchJson<T>(path: string, init?: RequestInit): Promise<T> {
  const headers: Record<string, string> = {
    "Content-Type": "application/json",
    ...((init?.headers as Record<string, string>) ?? {}),
  }
  const token = getAccessToken()
  if (token) headers.Authorization = `Bearer ${token}`

  const response = await fetch(`${API_BASE_URL}${path}`, {
    ...init,
    cache: "no-store",
    headers,
  })

  if (!response.ok) {
    throw new Error(`API request failed (${response.status}): ${path}`)
  }

  return (await response.json()) as T
}

export async function getPatients(): Promise<Patient[]> {
  return fetchJson<Patient[]>("/api/patients/")
}

export async function getPatientById(patientId: string): Promise<Patient | null> {
  try {
    return await fetchJson<Patient>(`/api/patients/${encodeURIComponent(patientId)}/`)
  } catch {
    return null
  }
}

/** Get patient by NFC tag ID (for edit page when tag is scanned). */
export async function getPatientByNfcId(nfcId: string): Promise<Patient | null> {
  try {
    return await fetchJson<Patient>(
      `/api/patients/by-nfc/${encodeURIComponent(nfcId.trim())}/`
    )
  } catch {
    return null
  }
}

/** Risk score from /api/patients/risk-score/ */
export interface PatientRiskScore {
  riskBand: "low" | "medium" | "high"
  riskProbability: number
  modelVersion: string
  topFactors: { feature: string; direction: string; contribution: number }[]
  scoringMode: "heuristic" | "supervised"
  seriousnessFactor: number
  seriousnessLevel: "low" | "moderate" | "high" | "critical"
  assessmentRecommendation: string
}

/** Get risk score for a patient (trained model or heuristic). */
export async function getPatientRiskScore(patientId: string): Promise<PatientRiskScore> {
  const res = await fetch(`${API_BASE_URL}/api/patients/risk-score/`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      ...(getAccessToken() ? { Authorization: `Bearer ${getAccessToken()}` } : {}),
    },
    body: JSON.stringify({ patient_id: patientId }),
    cache: "no-store",
  })
  const body = await res.json().catch(() => ({}))
  if (!res.ok) {
    const message =
      typeof body.detail === "string" ? body.detail : `Risk score failed (${res.status})`
    throw new Error(message)
  }
  return body as PatientRiskScore
}

/** Get AI-generated clinical overview for a patient (Ark Labs). */
export async function getPatientAiOverview(patientId: string): Promise<string> {
  const res = await fetch(`${API_BASE_URL}/api/patients/ai-overview/`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      ...(getAccessToken() ? { Authorization: `Bearer ${getAccessToken()}` } : {}),
    },
    body: JSON.stringify({ patient_id: patientId }),
    cache: "no-store",
  })
  const body = await res.json().catch(() => ({}))
  if (!res.ok) {
    const message =
      typeof body.error === "string"
        ? body.error
        : typeof body.detail === "string"
          ? body.detail
          : `AI overview failed (${res.status})`
    throw new Error(message)
  }
  return typeof body.overview === "string" ? body.overview : ""
}

/** Look up patient by NFC tag id read from Arduino. tagId must come from the reader; backend only returns patients that exist for that nfc_id. */
export async function scanNfcTag(tagId: string): Promise<Patient | null> {
  try {
    const result = await fetchJson<{ patient: Patient }>("/api/nfc/scan/", {
      method: "POST",
      body: JSON.stringify({ tag_id: tagId }),
    })
    return result.patient
  } catch {
    return null
  }
}

/** Create a patient linked to an NFC tag (minimal or full payload). */
export async function createPatient(data: {
  nfcId: string
  firstName: string
  lastName: string
  room?: string
  dateOfBirth?: string
  gender?: string
  bloodType?: string
  status?: string
  admissionDate?: string
  allergies?: string[]
  primaryDiagnosis?: string
  insuranceProvider?: string
  insuranceId?: string
  emergencyContact?: Patient["emergencyContact"]
  medications?: Patient["medications"]
  currentPrescriptions?: string[]
  medicalHistory?: string[]
  pastMedicalHistory?: string[]
  importantTestResults?: string
  useAlbertaHealthCard?: boolean
  albertaHealthCardNumber?: string
  notes?: string[]
}): Promise<Patient> {
  const headers: Record<string, string> = {
    "Content-Type": "application/json",
  }
  const token = getAccessToken()
  if (token) headers.Authorization = `Bearer ${token}`

  const res = await fetch(`${API_BASE_URL}/api/patients/create/`, {
    method: "POST",
    headers,
    body: JSON.stringify(data),
    cache: "no-store",
  })
  const body = await res.json().catch(() => ({}))
  if (!res.ok) {
    const message =
      typeof body.detail === "string" ? body.detail : `Failed to add patient (${res.status})`
    throw new Error(message)
  }
  return body as Patient
}

/** Update patient (full or partial). */
export async function updatePatient(
  patientId: string,
  data: Partial<Omit<Patient, "id" | "nfcId">> & { nfcId?: string }
): Promise<Patient> {
  const headers: Record<string, string> = {
    "Content-Type": "application/json",
  }
  const token = getAccessToken()
  if (token) headers.Authorization = `Bearer ${token}`

  const res = await fetch(
    `${API_BASE_URL}/api/patients/${encodeURIComponent(patientId)}/`,
    {
      method: "PATCH",
      headers,
      body: JSON.stringify(data),
      cache: "no-store",
    }
  )
  const body = await res.json().catch(() => ({}))
  if (!res.ok) {
    const message =
      typeof body.detail === "string" ? body.detail : `Failed to update (${res.status})`
    throw new Error(message)
  }
  return body as Patient
}
