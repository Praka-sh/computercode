'use client'

import { useState, useEffect } from 'react'
import Link from 'next/link'
import { api } from '@/lib/api'
import { Upload, FileText, Settings, Play, Search, AlertTriangle } from 'lucide-react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'

export default function Dashboard() {
  const [health, setHealth] = useState<{ status: string } | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    api.get('/health')
      .then(res => {
        setHealth(res.data)
        setLoading(false)
      })
      .catch(() => {
        setHealth({ status: 'disconnected' })
        setLoading(false)
      })
  }, [])

  return (
    <div className="min-h-screen bg-background">
      <header className="border-b bg-card/50 backdrop-blur sticky top-0 z-50">
        <div className="container mx-auto px-4 h-16 flex items-center justify-between">
          <h1 className="text-xl font-bold">Company Brain</h1>
          <nav className="flex items-center gap-4 text-sm">
            <Link href="/sources" className="text-muted-foreground hover:text-foreground">
              Sources
            </Link>
            <span className={`px-2 py-1 rounded-full text-xs ${
              health?.status === 'healthy' ? 'bg-green-100 text-green-800' :
              health?.status === 'disconnected' ? 'bg-red-100 text-red-800' :
              'bg-yellow-100 text-yellow-800'
            }`}>
              {loading ? 'Connecting...' : health?.status || 'Unknown'}
            </span>
          </nav>
        </div>
      </header>

      <main className="container mx-auto px-4 py-8">
        <div className="mb-8">
          <h2 className="text-2xl font-bold mb-2">Dashboard</h2>
          <p className="text-muted-foreground">Overview of your Company Brain workspace</p>
        </div>

        <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-4">
          <StatCard title="Sources" value="0" description="Documents uploaded" icon={<FileText className="h-6 w-6" />} />
          <StatCard title="Knowledge Units" value="0" description="Extracted rules & policies" icon={<Search className="h-6 w-6" />} />
          <StatCard title="Conflicts" value="0" description="Awaiting review" icon={<AlertTriangle className="h-6 w-6" />} />
          <StatCard title="Skills" value="0" description="Published workflows" icon={<Play className="h-6 w-6" />} />
        </div>

        <div className="mt-10 grid gap-6 md:grid-cols-2">
          <section className="rounded-lg border bg-card p-6">
            <h3 className="text-lg font-semibold mb-4">Quick Actions</h3>
            <div className="space-y-3">
              <Link
                href="/sources"
                className="w-full text-left p-4 rounded-lg border hover:bg-accent transition-colors flex items-center gap-3"
              >
                <Upload className="h-5 w-5 text-primary" />
                <div>
                  <div className="font-medium">Upload Policy Document</div>
                  <div className="text-sm text-muted-foreground">Add a new source for knowledge extraction</div>
                </div>
              </Link>
              <Link
                href="/knowledge"
                className="w-full text-left p-4 rounded-lg border hover:bg-accent transition-colors flex items-center gap-3"
              >
                <FileText className="h-5 w-5 text-primary" />
                <div>
                  <div className="font-medium">Review Knowledge</div>
                  <div className="text-sm text-muted-foreground">Approve or resolve extracted rules</div>
                </div>
              </Link>
              <Link
                href="/skills"
                className="w-full text-left p-4 rounded-lg border hover:bg-accent transition-colors flex items-center gap-3"
              >
                <Settings className="h-5 w-5 text-primary" />
                <div>
                  <div className="font-medium">Create Skill</div>
                  <div className="text-sm text-muted-foreground">Compile approved processes into workflows</div>
                </div>
              </Link>
              <Link
                href="/runs"
                className="w-full text-left p-4 rounded-lg border hover:bg-accent transition-colors flex items-center gap-3"
              >
                <Play className="h-5 w-5 text-primary" />
                <div>
                  <div className="font-medium">Run Sandbox Agent</div>
                  <div className="text-sm text-muted-foreground">Test a skill against a synthetic ticket</div>
                </div>
              </Link>
            </div>
          </section>

          <section className="rounded-lg border bg-card p-6">
            <h3 className="text-lg font-semibold mb-4">System Status</h3>
            <div className="space-y-3 text-sm">
              <div className="flex justify-between">
                <span>API</span>
                <span className={health?.status === 'healthy' ? 'text-green-600' : 'text-red-600'}>
                  {health?.status || 'Unknown'}
                </span>
              </div>
              <div className="flex justify-between">
                <span>Database</span>
                <span className="text-green-600">Connected</span>
              </div>
              <div className="flex justify-between">
                <span>Object Storage</span>
                <span className="text-green-600">Connected</span>
              </div>
              <div className="flex justify-between">
                <span>Task Queue</span>
                <span className="text-green-600">Running</span>
              </div>
            </div>
          </section>
        </div>
      </main>
    </div>
  )
}

function StatCard({ title, value, description, icon }: { title: string; value: string | number; description: string; icon: React.ReactNode }) {
  return (
    <Card>
      <CardContent className="pt-6">
        <div className="flex items-center justify-between">
          <div>
            <p className="text-sm font-medium text-muted-foreground">{title}</p>
            <p className="text-3xl font-bold mt-1">{value}</p>
            <p className="text-sm text-muted-foreground mt-1">{description}</p>
          </div>
          <div className="p-3 bg-primary/10 rounded-lg text-primary">
            {icon}
          </div>
        </div>
      </CardContent>
    </Card>
  )
}