import { notFound } from "next/navigation"
import { DashboardShell } from "@/components/dashboard/dashboard-shell"
import { PatientDetail } from "@/components/dashboard/patient-detail"
import { patients } from "@/lib/mock-data"

export default async function PatientPage({
  params,
}: {
  params: Promise<{ id: string }>
}) {
  const { id } = await params
  const patient = patients.find((p) => p.id === id)

  if (!patient) {
    notFound()
  }

  return (
    <DashboardShell>
      <PatientDetail patient={patient} />
    </DashboardShell>
  )
}
