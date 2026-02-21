"use client"

import { useState, useCallback, useEffect } from "react"
import Link from "next/link"
import { DashboardShell } from "@/components/dashboard/dashboard-shell"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Usb, ArrowLeft, Loader2 } from "lucide-react"
import type { Patient } from "@/lib/api"
import {
  getPatientByNfcId,
  createPatient,
  updatePatient,
} from "@/lib/api"
import { useSerial } from "@/hooks/use-serial"

const emptyForm = (nfcId: string): Partial<Patient> => ({
  id: nfcId,
  nfcId,
  firstName: "",
  lastName: "",
  dateOfBirth: "",
  gender: "",
  bloodType: "",
  status: "active",
  room: "",
  admissionDate: "",
  allergies: [],
  primaryDiagnosis: "",
  insuranceProvider: "",
  insuranceId: "",
  emergencyContact: { name: "", relationship: "", phone: "" },
  medications: [],
  vitalSigns: {
    heartRate: 0,
    bloodPressure: "",
    temperature: 0,
    oxygenSaturation: 0,
  },
  medicalHistory: [],
  notes: [],
})

function patientToForm(p: Patient): Partial<Patient> {
  return {
    ...p,
    emergencyContact: p.emergencyContact || { name: "", relationship: "", phone: "" },
    vitalSigns: p.vitalSigns || { heartRate: 0, bloodPressure: "", temperature: 0, oxygenSaturation: 0 },
    allergies: p.allergies || [],
    medications: p.medications || [],
    medicalHistory: p.medicalHistory || [],
    notes: p.notes || [],
  }
}

export default function PatientEditPage() {
  const [nfcIdInput, setNfcIdInput] = useState("")
  const [loadedPatient, setLoadedPatient] = useState<Patient | null>(null)
  const [form, setForm] = useState<Partial<Patient>>(emptyForm(""))
  const [loadError, setLoadError] = useState<string | null>(null)
  const [saving, setSaving] = useState(false)
  const [saveSuccess, setSaveSuccess] = useState(false)

  const generateRandomNfcId = useCallback(() => {
    const chars = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"
    let id = "TI-"
    for (let i = 0; i < 8; i++) id += chars[Math.floor(Math.random() * chars.length)]
    return id
  }, [])

  const handleTagRead = useCallback(async (tagId: string) => {
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
    if (isEmptyCard) setLoadError("Card had no ID. A new ID was generated. Use \"Assign ID to empty tag\" to write it to the card.")
  }, [generateRandomNfcId])

  const { isSupported: serialSupported, isConnected: serialConnected, connect: serialConnect, send: serialSend } = useSerial(handleTagRead)

  const handleWriteToTag = useCallback(() => {
    if (!serialSend) return
    let id = nfcIdInput.trim()
    if (!id) {
      id = generateRandomNfcId()
      setNfcIdInput(id)
      setForm((f) => ({ ...f, nfcId: id, id }))
    }
    serialSend(`WRITE|${id}`)
  }, [nfcIdInput, serialSend, generateRandomNfcId])

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
    const nfcId = (form.nfcId || nfcIdInput).trim()
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
          room: form.room ?? "",
          admissionDate: form.admissionDate ?? "",
          allergies: form.allergies ?? [],
          primaryDiagnosis: form.primaryDiagnosis ?? "",
          insuranceProvider: form.insuranceProvider ?? "",
          insuranceId: form.insuranceId ?? "",
          emergencyContact: form.emergencyContact ?? {},
          medications: form.medications ?? [],
          vitalSigns: form.vitalSigns ?? {},
          medicalHistory: form.medicalHistory ?? [],
          notes: form.notes ?? [],
        })
      } else {
        await createPatient({
          nfcId,
          firstName,
          lastName,
          room: form.room || undefined,
          dateOfBirth: form.dateOfBirth || undefined,
          gender: form.gender || undefined,
          bloodType: form.bloodType || undefined,
          status: (form.status as Patient["status"]) || "active",
          admissionDate: form.admissionDate || undefined,
          allergies: form.allergies?.length ? form.allergies : undefined,
          primaryDiagnosis: form.primaryDiagnosis || undefined,
          insuranceProvider: form.insuranceProvider || undefined,
          insuranceId: form.insuranceId || undefined,
          emergencyContact: form.emergencyContact || undefined,
          medications: form.medications?.length ? form.medications : undefined,
          vitalSigns: form.vitalSigns || undefined,
          medicalHistory: form.medicalHistory?.length ? form.medicalHistory : undefined,
          notes: form.notes?.length ? form.notes : undefined,
        })
      }
      setSaveSuccess(true)
      if (!loadedPatient) setLoadedPatient(null)
    } catch (err) {
      setLoadError(err instanceof Error ? err.message : "Save failed.")
    } finally {
      setSaving(false)
    }
  }, [form, loadedPatient, nfcIdInput])

  const ec = form.emergencyContact || { name: "", relationship: "", phone: "" }

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
              <>
                <Button
                  variant="outline"
                  onClick={serialConnected ? undefined : serialConnect}
                  className="gap-2"
                  disabled={serialConnected}
                >
                  <Usb className="h-4 w-4" />
                  {serialConnected ? "Reader connected" : "Connect reader"}
                </Button>
                <Button
                  variant="outline"
                  onClick={handleWriteToTag}
                  className="gap-2 border-primary/40 bg-primary/5 text-primary hover:bg-primary/10"
                  disabled={!serialConnected}
                  title={nfcIdInput.trim() ? "Write this ID to tag (overwrites if tag already has an ID)" : "Assign a random ID to empty tag, then write it"}
                >
                  {nfcIdInput.trim() ? "Write ID to tag" : "Assign ID to empty tag"}
                </Button>
              </>
            )}
          </div>
          {loadedPatient && (
            <p className="mt-2 text-sm text-primary">Editing: {loadedPatient.firstName} {loadedPatient.lastName}</p>
          )}
          {!loadedPatient && nfcIdInput.trim() && (
            <p className="mt-2 text-sm text-muted-foreground">No patient for this ID — fill form to add.</p>
          )}
          {loadError && <p className="mt-2 text-sm text-destructive">{loadError}</p>}
          {saveSuccess && <p className="mt-2 text-sm text-primary">Saved successfully.</p>}
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
              <Input
                id="dob"
                value={form.dateOfBirth ?? ""}
                onChange={(e) => updateField("dateOfBirth", e.target.value)}
                placeholder="YYYY-MM-DD"
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
              <Label htmlFor="room">Room</Label>
              <Input
                id="room"
                value={form.room ?? ""}
                onChange={(e) => updateField("room", e.target.value)}
                placeholder="Room"
              />
            </div>
            <div>
              <Label htmlFor="admission">Admission date</Label>
              <Input
                id="admission"
                value={form.admissionDate ?? ""}
                onChange={(e) => updateField("admissionDate", e.target.value)}
                placeholder="YYYY-MM-DD"
              />
            </div>
          </div>

          <div>
            <Label htmlFor="diagnosis">Primary diagnosis</Label>
            <Input
              id="diagnosis"
              value={form.primaryDiagnosis ?? ""}
              onChange={(e) => updateField("primaryDiagnosis", e.target.value)}
              placeholder="Primary diagnosis"
            />
          </div>

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

          <div>
            <Label htmlFor="allergies">Allergies (one per line)</Label>
            <textarea
              id="allergies"
              value={(form.allergies ?? []).join("\n")}
              onChange={(e) => updateField("allergies", e.target.value.split("\n").map((s) => s.trim()).filter(Boolean))}
              placeholder="One per line"
              rows={2}
              className="mt-1 w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
            />
          </div>

          <div>
            <Label htmlFor="vitals">Vital signs (e.g. HR: 72, BP: 120/80, Temp: 98.6, O2: 98)</Label>
            <Input
              id="vitals"
              value={form.vitalSigns ? [
                form.vitalSigns.heartRate ? `HR: ${form.vitalSigns.heartRate}` : "",
                form.vitalSigns.bloodPressure ? `BP: ${form.vitalSigns.bloodPressure}` : "",
                form.vitalSigns.temperature ? `Temp: ${form.vitalSigns.temperature}` : "",
                form.vitalSigns.oxygenSaturation ? `O2: ${form.vitalSigns.oxygenSaturation}` : "",
              ].filter(Boolean).join(", ") : ""}
              onChange={(e) => {
                const s = e.target.value
                const hr = /HR:\s*(\d+)/i.exec(s)?.[1]
                const bp = /BP:\s*([\d/]+)/i.exec(s)?.[1]
                const temp = /Temp:\s*([\d.]+)/i.exec(s)?.[1]
                const o2 = /O2:\s*(\d+)/i.exec(s)?.[1]
                updateField("vitalSigns", {
                  heartRate: hr ? parseInt(hr, 10) : 0,
                  bloodPressure: bp ?? "",
                  temperature: temp ? parseFloat(temp) : 0,
                  oxygenSaturation: o2 ? parseInt(o2, 10) : 0,
                })
              }}
              placeholder="HR: 72, BP: 120/80, Temp: 98.6, O2: 98"
            />
          </div>

          <div>
            <Label htmlFor="med-history">Medical history (one per line)</Label>
            <textarea
              id="med-history"
              value={(form.medicalHistory ?? []).join("\n")}
              onChange={(e) => updateField("medicalHistory", e.target.value.split("\n").map((s) => s.trim()).filter(Boolean))}
              placeholder="One per line"
              rows={2}
              className="mt-1 w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
            />
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
