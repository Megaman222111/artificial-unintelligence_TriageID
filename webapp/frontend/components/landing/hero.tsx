import Link from "next/link"
import { Nfc, ShieldCheck, Zap } from "lucide-react"
import { Button } from "@/components/ui/button"

export function Hero() {
  return (
    <section className="relative overflow-hidden">
      {/* Background pattern */}
      <div className="absolute inset-0 -z-10">
        <div className="absolute top-0 right-0 h-[500px] w-[500px] rounded-full bg-primary/5 blur-3xl" />
        <div className="absolute bottom-0 left-0 h-[400px] w-[400px] rounded-full bg-accent/20 blur-3xl" />
      </div>

      <div className="mx-auto max-w-7xl px-6 pb-24 pt-20 lg:pb-32 lg:pt-28">
        <div className="grid items-center gap-12 lg:grid-cols-2 lg:gap-16">
          {/* Left content */}
          <div className="flex flex-col gap-8">
            <div className="inline-flex w-fit items-center gap-2 rounded-full border border-primary/20 bg-primary/5 px-4 py-1.5 text-sm font-medium text-primary">
              <Nfc className="h-4 w-4" />
              NFC-Powered Identification
            </div>

            <h1 className="text-4xl font-bold leading-tight tracking-tight font-[family-name:var(--font-heading)] text-foreground md:text-5xl lg:text-6xl text-balance">
              Secure Patient Identification When It Matters Most
            </h1>

            <p className="max-w-lg text-lg leading-relaxed text-muted-foreground">
              MedLink uses encrypted NFC wristbands to give healthcare providers instant, 
              verified access to patient records -- designed for emergencies where every second counts.
            </p>

            <div className="flex flex-col gap-3 sm:flex-row sm:items-center">
              <Button size="lg" asChild className="gap-2">
                <Link href="/login">
                  Provider Login
                </Link>
              </Button>
              <Button size="lg" variant="outline" asChild>
                <Link href="#how-it-works">How It Works</Link>
              </Button>
            </div>

            <div className="flex items-center gap-6 pt-2">
              <div className="flex items-center gap-2 text-sm text-muted-foreground">
                <ShieldCheck className="h-4 w-4 text-primary" />
                HIPAA Compliant
              </div>
              <div className="flex items-center gap-2 text-sm text-muted-foreground">
                <Zap className="h-4 w-4 text-primary" />
                {"< 2s Verification"}
              </div>
            </div>
          </div>

          {/* Right visual - NFC Wristband illustration */}
          <div className="relative flex items-center justify-center">
            <div className="relative w-full max-w-md">
              {/* Main card */}
              <div className="rounded-2xl border border-border bg-card p-8 shadow-lg">
                <div className="mb-6 flex items-center justify-between">
                  <div className="flex items-center gap-3">
                    <div className="flex h-12 w-12 items-center justify-center rounded-full bg-primary/10">
                      <Nfc className="h-6 w-6 text-primary" />
                    </div>
                    <div>
                      <p className="text-sm font-semibold text-foreground">NFC Wristband</p>
                      <p className="text-xs text-muted-foreground">Encrypted identifier</p>
                    </div>
                  </div>
                  <div className="flex h-3 w-3 items-center justify-center">
                    <span className="absolute h-3 w-3 animate-ping rounded-full bg-primary/40" />
                    <span className="relative h-2 w-2 rounded-full bg-primary" />
                  </div>
                </div>

                {/* Simulated patient preview */}
                <div className="space-y-4 rounded-xl border border-border bg-background p-5">
                  <div className="flex items-center gap-4">
                    <div className="flex h-14 w-14 items-center justify-center rounded-full bg-accent text-lg font-bold text-accent-foreground">
                      JD
                    </div>
                    <div>
                      <p className="text-base font-semibold text-foreground">Jane Doe</p>
                      <p className="text-sm text-muted-foreground">ID: MED-2847-NFC</p>
                    </div>
                  </div>
                  <div className="grid grid-cols-2 gap-3">
                    <div className="rounded-lg bg-muted p-3">
                      <p className="text-xs text-muted-foreground">Blood Type</p>
                      <p className="text-sm font-semibold text-foreground">O+</p>
                    </div>
                    <div className="rounded-lg bg-muted p-3">
                      <p className="text-xs text-muted-foreground">Allergies</p>
                      <p className="text-sm font-semibold text-foreground">Penicillin</p>
                    </div>
                  </div>
                  <div className="flex items-center gap-2 rounded-lg bg-primary/5 p-3">
                    <ShieldCheck className="h-4 w-4 text-primary" />
                    <p className="text-xs font-medium text-primary">Identity Verified</p>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </section>
  )
}
