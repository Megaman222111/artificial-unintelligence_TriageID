import { Nfc, Lock, Activity, Clock, Database, Users } from "lucide-react"

const features = [
  {
    icon: Nfc,
    title: "NFC Wristband Scanning",
    description:
      "Each patient wears a secure wristband containing an encrypted unique ID. A single tap instantly retrieves their full medical profile.",
  },
  {
    icon: Lock,
    title: "End-to-End Encryption",
    description:
      "Patient data is encrypted at rest and in transit. Only authorized healthcare providers with valid credentials can access records.",
  },
  {
    icon: Activity,
    title: "Emergency-Ready Access",
    description:
      "In critical situations, first responders can verify patient identity and retrieve vital information in under two seconds.",
  },
  {
    icon: Clock,
    title: "Real-Time Sync",
    description:
      "Patient records are synchronized in real-time across connected devices and facilities, ensuring accuracy at every point of care.",
  },
  {
    icon: Database,
    title: "Centralized Medical Records",
    description:
      "A full-stack platform securely stores comprehensive medical data -- history, medications, allergies, insurance, and more -- in one place.",
  },
  {
    icon: Users,
    title: "Role-Based Access Control",
    description:
      "Granular permissions ensure that doctors, nurses, and staff see only the data relevant to their role and authorization level.",
  },
]

export function Features() {
  return (
    <section id="features" className="border-t border-border bg-muted/30 py-24">
      <div className="mx-auto max-w-7xl px-6">
        <div className="mx-auto max-w-2xl text-center">
          <p className="text-sm font-semibold uppercase tracking-widest text-primary">
            Core Capabilities
          </p>
          <h2 className="mt-3 text-3xl font-bold tracking-tight font-[family-name:var(--font-heading)] text-foreground md:text-4xl text-balance">
            How MedLink Protects Patients and Providers
          </h2>
          <p className="mt-4 text-base leading-relaxed text-muted-foreground">
            Every part of the system is purpose-built for fast, secure, and reliable 
            patient identification in clinical environments.
          </p>
        </div>

        <div className="mt-16 grid gap-6 sm:grid-cols-2 lg:grid-cols-3">
          {features.map((feature) => (
            <div
              key={feature.title}
              className="group rounded-xl border border-border bg-card p-6 transition-all hover:border-primary/30 hover:shadow-md"
            >
              <div className="mb-4 flex h-11 w-11 items-center justify-center rounded-lg bg-primary/10 text-primary transition-colors group-hover:bg-primary group-hover:text-primary-foreground">
                <feature.icon className="h-5 w-5" />
              </div>
              <h3 className="mb-2 text-lg font-semibold text-foreground">
                {feature.title}
              </h3>
              <p className="text-sm leading-relaxed text-muted-foreground">
                {feature.description}
              </p>
            </div>
          ))}
        </div>
      </div>
    </section>
  )
}
