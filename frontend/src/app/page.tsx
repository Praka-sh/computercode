import Link from 'next/link'

export default function Home() {
  return (
    <main className="min-h-screen bg-background">
      <div className="container mx-auto px-4 py-16">
        <div className="max-w-3xl mx-auto text-center">
          <h1 className="text-4xl font-bold tracking-tight text-foreground mb-6">
            Company Brain MVP
          </h1>
          <p className="text-xl text-muted-foreground mb-8">
            Turn fragmented company knowledge into verified, versioned, executable AI workflows.
          </p>
          <div className="flex flex-col sm:flex-row gap-4 justify-center">
            <Link
              href="/dashboard"
              className="inline-flex items-center justify-center rounded-md bg-primary px-6 py-3 text-sm font-medium text-primary-foreground hover:bg-primary/90 transition-colors"
            >
              Go to Dashboard
            </Link>
            <Link
              href="/api/docs"
              className="inline-flex items-center justify-center rounded-md border border-input bg-background px-6 py-3 text-sm font-medium text-foreground hover:bg-accent transition-colors"
            >
              API Docs
            </Link>
          </div>
          <div className="mt-12 grid gap-6 md:grid-cols-3 text-left">
            <div className="rounded-lg border bg-card p-6">
              <h3 className="text-lg font-semibold mb-2">Sources</h3>
              <p className="text-muted-foreground text-sm">
                Upload and manage policy documents with full provenance tracking.
              </p>
            </div>
            <div className="rounded-lg border bg-card p-6">
              <h3 className="text-lg font-semibold mb-2">Knowledge</h3>
              <p className="text-muted-foreground text-sm">
                Review extracted rules, resolve conflicts, and maintain evidence-backed policies.
              </p>
            </div>
            <div className="rounded-lg border bg-card p-6">
              <h3 className="text-lg font-semibold mb-2">Skills</h3>
              <p className="text-muted-foreground text-sm">
                Compile approved processes into versioned, auditable AI workflows.
              </p>
            </div>
          </div>
        </div>
      </div>
    </main>
  )
}