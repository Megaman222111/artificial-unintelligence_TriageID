"use client"

import { useState, useCallback, useEffect, useRef } from "react"
import Link from "next/link"
import { useSearchParams } from "next/navigation"
import { DashboardShell } from "@/components/dashboard/dashboard-shell"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { DatePicker } from "@/components/ui/date-picker"
import { Usb, ArrowLeft, Loader2 } from "lucide-react"
import type { Patient } from "@/lib/api"
import {
  getPatientByNfcId,
  createPatient,
  updatePatient,
} from "@/lib/api"
import { useSerialContext } from "@/contexts/serial-context"

const emptyForm = (nfcId: string): Partial<Patient> => ({
  id: nfcId,
  nfcId,
  firstName: "",
  lastName: "",
  dateOfBirth: "",
  gender: "",
  bloodType: "",
  status: "active",
  admissionDate: "",
  allergies: [],
  insuranceProvider: "",
  insuranceId: "",
  useAlbertaHealthCard: false,
  albertaHealthCardNumber: "",
  emergencyContact: { name: "", relationship: "", phone: "" },
  medications: [],
  currentPrescriptions: [],
  medicalHistory: [],
  pastMedicalHistory: [],
  notes: [],
})

function patientToForm(p: Patient): Partial<Patient> {
  return {
    ...p,
    emergencyContact: p.emergencyContact || { name: "", relationship: "", phone: "" },
    allergies: p.allergies || [],
    medications: p.medications || [],
    currentPrescriptions: p.currentPrescriptions || [],
    medicalHistory: p.medicalHistory || [],
    pastMedicalHistory: p.pastMedicalHistory || [],
    notes: p.notes || [],
  }
}

const ALLERGY_OPTIONS = [
  "Penicillin",
  "Sulfa",
  "Latex",
  "Iodine/Contrast",
  "Peanut",
  "Shellfish",
  "Grass",
  "Dust",
]

const CURRENT_PRESCRIPTION_OPTIONS = [
  "Aspirin",
  "Insulin",
  "Warfarin",
  "Heparin",
  "Metformin",
  "Prednisone",
  "Morphine",
  "Fentanyl",
  "Antibiotics",
  "Chemotherapy",
]

const MEDICAL_HISTORY_OPTIONS = [
  "Diabetes",
  "Hypertension",
  "Coronary artery disease",
  "Heart failure",
  "Stroke",
  "COPD",
  "Chronic kidney disease",
  "Cancer",
  "Sepsis",
  "Pneumonia",
]

const PAST_MEDICAL_HISTORY_OPTIONS = [
  "Past MI",
  "Past stroke",
  "Past cancer",
  "Past surgery",
  "Chronic liver disease",
  "Asthma",
  "Dementia",
  "Atrial fibrillation",
  "Peripheral vascular disease",
  "Renal failure",
]

function mergeOptions(base: string[], current?: string[]) {
  return Array.from(new Set([...base, ...((current || []).filter(Boolean))]))
}

function toggleListValue(current: string[] | undefined, option: string, checked: boolean) {
  const list = current || []
  if (checked) return list.includes(option) ? list : [...list, option]
  return list.filter((x) => x !== option)
}

export default function PatientEditPage() {
  const searchParams = useSearchParams()
  const [nfcIdInput, setNfcIdInput] = useState("")
  const [loadedPatient, setLoadedPatient] = useState<Patient | null>(null)
  const [form, setForm] = useState<Partial<Patient>>(emptyForm(""))
  const [loadError, setLoadError] = useState<string | null>(null)
  const [saving, setSaving] = useState(false)
  const [saveSuccess, setSaveSuccess] = useState(false)
  const [pendingWriteNfcId, setPendingWriteNfcId] = useState<string | null>(null)
  const [writeToTagDone, setWriteToTagDone] = useState(false)
  const pendingWriteNfcIdRef = useRef<string | null>(null)
  const serialSendRef = useRef<(text: string) => Promise<void>>(async () => {})

  useEffect(() => {
    pendingWriteNfcIdRef.current = pendingWriteNfcId
  }, [pendingWriteNfcId])

  const nfcIdFromQuery = searchParams.get("nfcId")
  useEffect(() => {
    if (nfcIdFromQuery?.trim()) {
      setNfcIdInput(nfcIdFromQuery.trim())
      setForm((f) => ({ ...f, nfcId: nfcIdFromQuery.trim(), id: nfcIdFromQuery.trim() }))
    }
  }, [nfcIdFromQuery])

  const generateRandomNfcId = useCallback(() => {
    const chars = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"
    let id = "TI-"
    for (let i = 0; i < 8; i++) id += chars[Math.floor(Math.random() * chars.length)]
    return id
  }, [])

  const handleTagRead = useCallback(async (tagId: string) => {
    if (pendingWriteNfcIdRef.current != null && serialSendRef.current) {
      const toWrite = pendingWriteNfcIdRef.current
      setPendingWriteNfcId(null)
      setWriteToTagDone(true)
      await serialSendRef.current(`WRITE|${toWrite}`)
      // Reset scanner to read mode so the next scan works
      await serialSendRef.current("READ")
      return
    }
    setLoadError(null)
    const isEmptyCard = tagId.trim() === ""
    const idToUse = isEmptyCard ? generateRandomNfcId() : tagId
    setNfcIdInput(idToUse)
    const patient = await getPatientByNfcId(idToUse)
    if (patient) {
      setLoadedPatient(patient)
      setForm(patientToForm(patient))
    } else {
      setLoadedPatient(null)
      setForm(emptyForm(idToUse))
    }
    if (isEmptyCard) setLoadError("Card had no ID. A new ID was generated. After saving the patient, scan a tag to write the ID to the wristband.")
  }, [generateRandomNfcId])

  const { isSupported: serialSupported, isConnected: serialConnected, isReconnecting: serialReconnecting, connect: serialConnect, send: serialSend, setOnTagRead } = useSerialContext()
  serialSendRef.current = serialSend

  useEffect(() => {
    setOnTagRead(handleTagRead)
    return () => setOnTagRead(null)
  }, [handleTagRead, setOnTagRead])

  const handleLoadByNfcId = useCallback(async () => {
    const id = nfcIdInput.trim()
    if (!id) return
    setLoadError(null)
    const patient = await getPatientByNfcId(id)
    if (patient) {
      setLoadedPatient(patient)
      setForm(patientToForm(patient))
    } else {
      setLoadedPatient(null)
      setForm(emptyForm(id))
    }
  }, [nfcIdInput])

  useEffect(() => {
    if (nfcIdInput.trim() && !form.nfcId) setForm((f) => ({ ...f, nfcId: nfcIdInput.trim(), id: nfcIdInput.trim() }))
  }, [nfcIdInput, form.nfcId])

  const updateField = useCallback(<K extends keyof Patient>(key: K, value: Patient[K]) => {
    setForm((f) => ({ ...f, [key]: value }))
  }, [])

  const handleSave = useCallback(async () => {
    let nfcId = (form.nfcId || nfcIdInput).trim()
    if (!loadedPatient && !nfcId) {
      nfcId = generateRandomNfcId()
      setNfcIdInput(nfcId)
      setForm((f) => ({ ...f, nfcId, id: nfcId }))
    }
    const firstName = (form.firstName || "").trim()
    const lastName = (form.lastName || "").trim()
    if (!nfcId || !firstName || !lastName) return
    setSaving(true)
    setSaveSuccess(false)
    try {
      if (loadedPatient) {
        await updatePatient(loadedPatient.id, {
          firstName,
          lastName,
          dateOfBirth: form.dateOfBirth ?? "",
          gender: form.gender ?? "",
          bloodType: form.bloodType ?? "",
          status: (form.status as Patient["status"]) ?? "active",
          admissionDate: form.admissionDate ?? "",
          allergies: form.allergies ?? [],
          insuranceProvider: form.insuranceProvider ?? "",
          insuranceId: form.insuranceId ?? "",
          useAlbertaHealthCard: form.useAlbertaHealthCard ?? false,
          albertaHealthCardNumber: form.albertaHealthCardNumber ?? "",
          emergencyContact: form.emergencyContact ?? {},
          medications: form.medications ?? [],
          currentPrescriptions: form.currentPrescriptions ?? [],
          medicalHistory: form.medicalHistory ?? [],
          pastMedicalHistory: form.pastMedicalHistory ?? [],
          notes: form.notes ?? [],
        })
      } else {
        const created = await createPatient({
          nfcId,
          firstName,
          lastName,
          dateOfBirth: form.dateOfBirth || undefined,
          gender: form.gender || undefined,
          bloodType: form.bloodType || undefined,
          status: (form.status as Patient["status"]) || "active",
          admissionDate: form.admissionDate || undefined,
          allergies: form.allergies?.length ? form.allergies : undefined,
          insuranceProvider: form.insuranceProvider || undefined,
          insuranceId: form.insuranceId || undefined,
          useAlbertaHealthCard: form.useAlbertaHealthCard || undefined,
          albertaHealthCardNumber: form.albertaHealthCardNumber?.trim() || undefined,
          emergencyContact: form.emergencyContact || undefined,
          medications: form.medications?.length ? form.medications : undefined,
          currentPrescriptions: form.currentPrescriptions?.length ? form.currentPrescriptions : undefined,
          medicalHistory: form.medicalHistory?.length ? form.medicalHistory : undefined,
          pastMedicalHistory: form.pastMedicalHistory?.length ? form.pastMedicalHistory : undefined,
          notes: form.notes?.length ? form.notes : undefined,
        })
        setPendingWriteNfcId(created.nfcId)
        setWriteToTagDone(false)
      }
      setSaveSuccess(true)
      if (!loadedPatient) setLoadedPatient(null)
    } catch (err) {
      setLoadError(err instanceof Error ? err.message : "Save failed.")
    } finally {
      setSaving(false)
    }
  }, [form, loadedPatient, nfcIdInput, generateRandomNfcId])

  const ec = form.emergencyContact || { name: "", relationship: "", phone: "" }
  const allergyOptions = mergeOptions(ALLERGY_OPTIONS, form.allergies)
  const prescriptionOptions = mergeOptions(
    CURRENT_PRESCRIPTION_OPTIONS,
    form.currentPrescriptions
  )
  const medicalHistoryOptions = mergeOptions(MEDICAL_HISTORY_OPTIONS, form.medicalHistory)
  const pastMedicalHistoryOptions = mergeOptions(
    PAST_MEDICAL_HISTORY_OPTIONS,
    form.pastMedicalHistory
  )

  return (
    <DashboardShell>
      <div className="mx-auto max-w-3xl space-y-8 p-6">
        <div className="flex items-center gap-4">
          <Button variant="ghost" size="sm" className="gap-2" asChild>
            <Link href="/dashboard">
              <ArrowLeft className="h-4 w-4" />
              Back
            </Link>
          </Button>
        </div>

        <div className="rounded-xl border border-border bg-card p-6">
          <h1 className="mb-4 text-xl font-bold font-[family-name:var(--font-heading)] text-foreground">
            Add / Edit patient by NFC
          </h1>
          <p className="mb-4 text-sm text-muted-foreground">
            Scan a tag or enter the NFC card ID, then load or add patient and edit full info.
          </p>

          <div className="flex flex-wrap items-end gap-3">
            <div className="min-w-[200px] flex-1">
              <Label htmlFor="nfc-id">NFC card ID</Label>
              <Input
                id="nfc-id"
                value={nfcIdInput}
                onChange={(e) => setNfcIdInput(e.target.value)}
                placeholder="Scan or type ID"
                className="mt-1 font-mono"
              />
            </div>
            <Button variant="outline" onClick={handleLoadByNfcId} disabled={!nfcIdInput.trim()}>
              Load patient
            </Button>
            {serialSupported && (
              <Button
                variant="outline"
                onClick={serialConnected ? undefined : serialConnect}
                className="gap-2"
                disabled={serialConnected || serialReconnecting}
              >
                <Usb className="h-4 w-4" />
                {serialReconnecting ? "Connecting to saved reader…" : serialConnected ? "Reader connected" : "Connect reader"}
              </Button>
            )}
          </div>
          {loadedPatient && (
            <p className="mt-2 text-sm text-primary">Editing: {loadedPatient.firstName} {loadedPatient.lastName}</p>
          )}
          {!loadedPatient && nfcIdInput.trim() && (
            <p className="mt-2 text-sm text-muted-foreground">No patient for this ID — fill form to add.</p>
          )}
          {loadError && <p className="mt-2 text-sm text-destructive">{loadError}</p>}
          {saveSuccess && !pendingWriteNfcId && !writeToTagDone && <p className="mt-2 text-sm text-primary">Saved successfully.</p>}
          {saveSuccess && pendingWriteNfcId && (
            <div className="mt-4 rounded-lg border border-primary/30 bg-primary/5 p-4">
              <p className="font-medium text-primary">Patient created. Scan a tag to attach this patient&apos;s ID to the wristband.</p>
              <p className="mt-1 text-sm text-muted-foreground">Hold the wristband to the reader; the ID will be written automatically.</p>
              <div className="mt-3 flex gap-2">
                <Button variant="outline" size="sm" onClick={() => { setPendingWriteNfcId(null); setWriteToTagDone(false) }}>
                  Skip
                </Button>
              </div>
            </div>
          )}
          {writeToTagDone && <p className="mt-2 text-sm text-primary">ID written to tag. The wristband is now linked to this patient.</p>}
        </div>

        <div className="space-y-6 rounded-xl border border-border bg-card p-6">
          <h2 className="text-lg font-semibold font-[family-name:var(--font-heading)] text-foreground">
            Patient information
          </h2>

          <div className="grid gap-4 sm:grid-cols-2">
            <div>
              <Label htmlFor="first">First name</Label>
              <Input
                id="first"
                value={form.firstName ?? ""}
                onChange={(e) => updateField("firstName", e.target.value)}
                placeholder="First name"
              />
            </div>
            <div>
              <Label htmlFor="last">Last name</Label>
              <Input
                id="last"
                value={form.lastName ?? ""}
                onChange={(e) => updateField("lastName", e.target.value)}
                placeholder="Last name"
              />
            </div>
            <div>
              <Label htmlFor="dob">Date of birth</Label>
              <DatePicker
                id="dob"
                value={form.dateOfBirth ?? ""}
                onChange={(v) => updateField("dateOfBirth", v)}
                placeholder="Pick date of birth"
                yearPicker
                fromYear={1900}
                toYear={new Date().getFullYear()}
              />
            </div>
            <div>
              <Label htmlFor="gender">Gender</Label>
              <Input
                id="gender"
                value={form.gender ?? ""}
                onChange={(e) => updateField("gender", e.target.value)}
                placeholder="Gender"
              />
            </div>
            <div>
              <Label htmlFor="blood">Blood type</Label>
              <Input
                id="blood"
                value={form.bloodType ?? ""}
                onChange={(e) => updateField("bloodType", e.target.value)}
                placeholder="e.g. O+"
              />
            </div>
            <div>
              <Label htmlFor="status">Status</Label>
              <select
                id="status"
                value={form.status ?? "active"}
                onChange={(e) => updateField("status", e.target.value as Patient["status"])}
                className="flex h-9 w-full rounded-md border border-input bg-background px-3 py-1 text-sm"
              >
                <option value="active">Active</option>
                <option value="critical">Critical</option>
                <option value="discharged">Discharged</option>
              </select>
            </div>
            <div>
              <Label htmlFor="admission">Admission date</Label>
              <DatePicker
                id="admission"
                value={form.admissionDate ?? ""}
                onChange={(v) => updateField("admissionDate", v)}
                placeholder="Pick admission date"
              />
            </div>
          </div>

          {/* Allergies (optional) */}
          <div>
            <Label className="text-muted-foreground">Allergies (optional)</Label>
            <div className="mt-2 grid gap-2 sm:grid-cols-2">
              {allergyOptions.map((option) => (
                <label
                  key={option}
                  className="flex cursor-pointer items-center gap-2 rounded-md border border-input px-3 py-2"
                >
                  <input
                    type="checkbox"
                    checked={(form.allergies ?? []).includes(option)}
                    onChange={(e) =>
                      updateField(
                        "allergies",
                        toggleListValue(form.allergies, option, e.target.checked)
                      )
                    }
                    className="h-4 w-4 rounded border-input"
                  />
                  <span className="text-sm">{option}</span>
                </label>
              ))}
            </div>
          </div>

          {/* Current prescriptions (optional) */}
          <div>
            <Label className="text-muted-foreground">Current prescriptions (optional)</Label>
            <div className="mt-2 grid gap-2 sm:grid-cols-2">
              {prescriptionOptions.map((option) => (
                <label
                  key={option}
                  className="flex cursor-pointer items-center gap-2 rounded-md border border-input px-3 py-2"
                >
                  <input
                    type="checkbox"
                    checked={(form.currentPrescriptions ?? []).includes(option)}
                    onChange={(e) =>
                      updateField(
                        "currentPrescriptions",
                        toggleListValue(form.currentPrescriptions, option, e.target.checked)
                      )
                    }
                    className="h-4 w-4 rounded border-input"
                  />
                  <span className="text-sm">{option}</span>
                </label>
              ))}
            </div>
          </div>

          {/* Medical history */}
          <div>
            <Label>Medical history</Label>
            <div className="mt-2 grid gap-2 sm:grid-cols-2">
              {medicalHistoryOptions.map((option) => (
                <label
                  key={option}
                  className="flex cursor-pointer items-center gap-2 rounded-md border border-input px-3 py-2"
                >
                  <input
                    type="checkbox"
                    checked={(form.medicalHistory ?? []).includes(option)}
                    onChange={(e) =>
                      updateField(
                        "medicalHistory",
                        toggleListValue(form.medicalHistory, option, e.target.checked)
                      )
                    }
                    className="h-4 w-4 rounded border-input"
                  />
                  <span className="text-sm">{option}</span>
                </label>
              ))}
            </div>
          </div>

          {/* Past medical history */}
          <div>
            <Label>Past medical history</Label>
            <div className="mt-2 grid gap-2 sm:grid-cols-2">
              {pastMedicalHistoryOptions.map((option) => (
                <label
                  key={option}
                  className="flex cursor-pointer items-center gap-2 rounded-md border border-input px-3 py-2"
                >
                  <input
                    type="checkbox"
                    checked={(form.pastMedicalHistory ?? []).includes(option)}
                    onChange={(e) =>
                      updateField(
                        "pastMedicalHistory",
                        toggleListValue(form.pastMedicalHistory, option, e.target.checked)
                      )
                    }
                    className="h-4 w-4 rounded border-input"
                  />
                  <span className="text-sm">{option}</span>
                </label>
              ))}
            </div>
          </div>

          <div>
            <Label htmlFor="notes">Notes (one per line)</Label>
            <textarea
              id="notes"
              value={(form.notes ?? []).join("\n")}
              onChange={(e) => updateField("notes", e.target.value.split("\n").map((s) => s.trim()).filter(Boolean))}
              placeholder="One per line"
              rows={2}
              className="mt-1 w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
            />
          </div>

          <div className="border-t border-border pt-6">
            <h3 className="mb-3 text-sm font-semibold text-muted-foreground">Insurance (optional)</h3>
            <div className="flex flex-col gap-3">
              <label className="flex cursor-pointer items-center gap-2">
                <input
                  type="checkbox"
                  checked={form.useAlbertaHealthCard ?? false}
                  onChange={(e) => updateField("useAlbertaHealthCard", e.target.checked)}
                  className="h-4 w-4 rounded border-input"
                />
                <span className="text-sm">Alberta Health Card (no other insurance)</span>
              </label>
              {(form.useAlbertaHealthCard ?? false) && (
                <div>
                  <Label htmlFor="alberta-health-number">Alberta Health Card number</Label>
                  <Input
                    id="alberta-health-number"
                    value={form.albertaHealthCardNumber ?? ""}
                    onChange={(e) => updateField("albertaHealthCardNumber", e.target.value)}
                    placeholder="e.g. 1234 567 890"
                    className="mt-1 max-w-xs"
                  />
                </div>
              )}
              {!(form.useAlbertaHealthCard ?? false) && (
                <div className="grid gap-4 sm:grid-cols-2">
                  <div>
                    <Label htmlFor="insurance-provider">Insurance provider</Label>
                    <Input
                      id="insurance-provider"
                      value={form.insuranceProvider ?? ""}
                      onChange={(e) => updateField("insuranceProvider", e.target.value)}
                      placeholder="Provider"
                    />
                  </div>
                  <div>
                    <Label htmlFor="insurance-id">Insurance ID</Label>
                    <Input
                      id="insurance-id"
                      value={form.insuranceId ?? ""}
                      onChange={(e) => updateField("insuranceId", e.target.value)}
                      placeholder="ID"
                    />
                  </div>
                </div>
              )}
            </div>
          </div>

          <div className="grid gap-4 sm:grid-cols-3">
            <div>
              <Label htmlFor="ec-name">Emergency contact name</Label>
              <Input
                id="ec-name"
                value={ec.name ?? ""}
                onChange={(e) => updateField("emergencyContact", { ...ec, name: e.target.value })}
                placeholder="Name"
              />
            </div>
            <div>
              <Label htmlFor="ec-relation">Relationship</Label>
              <Input
                id="ec-relation"
                value={ec.relationship ?? ""}
                onChange={(e) => updateField("emergencyContact", { ...ec, relationship: e.target.value })}
                placeholder="Relationship"
              />
            </div>
            <div>
              <Label htmlFor="ec-phone">Phone</Label>
              <Input
                id="ec-phone"
                value={ec.phone ?? ""}
                onChange={(e) => updateField("emergencyContact", { ...ec, phone: e.target.value })}
                placeholder="Phone"
              />
            </div>
          </div>

          <div className="flex gap-3 pt-4">
            <Button onClick={handleSave} disabled={saving || !(form.nfcId || nfcIdInput).trim() || !form.firstName?.trim() || !form.lastName?.trim()} className="gap-2">
              {saving && <Loader2 className="h-4 w-4 animate-spin" />}
              {saving ? "Saving..." : loadedPatient ? "Update patient" : "Add patient"}
            </Button>
          </div>
        </div>
      </div>
    </DashboardShell>
  )
}
