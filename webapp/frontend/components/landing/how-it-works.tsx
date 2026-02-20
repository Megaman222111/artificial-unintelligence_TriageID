import { Nfc, ScanLine, FileCheck, ShieldCheck } from "lucide-react"

const steps = [
  {
    icon: Nfc,
    step: "01",
    title: "Assign Wristband",
    description:
      "A secure NFC wristband is assigned to each patient at admission. The band contains a unique encrypted identifier linked to their medical record.",
  },
  {
    icon: ScanLine,
    step: "02",
    title: "Tap to Identify",
    description:
      "Healthcare providers use any NFC-enabled device to tap the wristband. The system instantly decrypts the ID and retrieves the patient profile.",
  },
  {
    icon: FileCheck,
    step: "03",
    title: "Access Records",
    description:
      "The provider sees the patient's medical history, allergies, medications, and vital notes. All data is pulled from the centralized secure platform.",
  },
  {
    icon: ShieldCheck,
    step: "04",
    title: "Verified & Secure",
    description:
      "Every access is logged and audited. The system ensures HIPAA-compliant data handling with end-to-end encryption at every step.",
  },
]

export function HowItWorks() {
  return (
    <section id="how-it-works" className="py-24">
      <div className="mx-auto max-w-7xl px-6">
        <div className="mx-auto max-w-2xl text-center">
          <p className="text-sm font-semibold uppercase tracking-widest text-primary">
            How It Works
          </p>
          <h2 className="mt-3 text-3xl font-bold tracking-tight font-[family-name:var(--font-heading)] text-foreground md:text-4xl text-balance">
            From Wristband to Verified Record in Seconds
          </h2>
          <p className="mt-4 text-base leading-relaxed text-muted-foreground">
            Four simple steps connect physical patient identification to secure digital records.
          </p>
        </div>

        <div className="mt-16 grid gap-8 md:grid-cols-2 lg:grid-cols-4">
          {steps.map((step, index) => (
            <div key={step.title} className="relative flex flex-col items-start">
              {/* Connector line */}
              {index < steps.length - 1 && (
                <div className="absolute right-0 top-10 hidden h-px w-full bg-border lg:block" style={{ left: '50%' }} />
              )}
              <div className="relative z-10 mb-4 flex h-14 w-14 items-center justify-center rounded-xl bg-primary text-primary-foreground shadow-md">
                <step.icon className="h-6 w-6" />
              </div>
              <span className="mb-1 text-xs font-semibold uppercase tracking-wider text-primary">
                Step {step.step}
              </span>
              <h3 className="mb-2 text-lg font-semibold text-foreground">
                {step.title}
              </h3>
              <p className="text-sm leading-relaxed text-muted-foreground">
                {step.description}
              </p>
            </div>
          ))}
        </div>
      </div>
    </section>
  )
}
