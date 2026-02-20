const stats = [
  { value: "< 2s", label: "Average Verification Time" },
  { value: "256-bit", label: "AES Encryption" },
  { value: "HIPAA", label: "Fully Compliant" },
  { value: "24/7", label: "System Availability" },
]

export function Stats() {
  return (
    <section className="border-y border-border bg-primary/5 py-16">
      <div className="mx-auto max-w-7xl px-6">
        <div className="grid grid-cols-2 gap-8 lg:grid-cols-4">
          {stats.map((stat) => (
            <div key={stat.label} className="text-center">
              <p className="text-3xl font-bold tracking-tight font-[family-name:var(--font-heading)] text-foreground md:text-4xl">
                {stat.value}
              </p>
              <p className="mt-2 text-sm text-muted-foreground">{stat.label}</p>
            </div>
          ))}
        </div>
      </div>
    </section>
  )
}
