import { DashboardShell } from "@/components/dashboard/dashboard-shell"
import { NfcScanView } from "@/components/dashboard/nfc-scan-view"

export default function DashboardPage() {
  return (
    <DashboardShell>
      <NfcScanView />
    </DashboardShell>
  )
}
