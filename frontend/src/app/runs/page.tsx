'use client'

import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Play, Pause, CheckCircle, XCircle, AlertCircle } from 'lucide-react'

export default function RunsPage() {
  return (
    <div className="container mx-auto px-4 py-8">
      <div className="mb-8">
        <h1 className="text-3xl font-bold">Agent Workspace</h1>
        <p className="text-muted-foreground">Run approved skills against sandbox tickets with approval gates</p>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Recent Runs</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="text-center py-8 text-muted-foreground">
            <Play className="h-12 w-12 mx-auto mb-4 opacity-50" />
            <p>No runs executed yet</p>
            <p className="text-sm">Publish a skill and select a sandbox ticket to run</p>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}