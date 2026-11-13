'use client'

import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Settings, Download } from 'lucide-react'

export default function SkillsPage() {
  return (
    <div className="container mx-auto px-4 py-8">
      <div className="mb-8">
        <h1 className="text-3xl font-bold">Skills Studio</h1>
        <p className="text-muted-foreground">Compile approved processes into versioned, auditable AI workflows</p>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Published Skills</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="text-center py-8 text-muted-foreground">
            <Settings className="h-12 w-12 mx-auto mb-4 opacity-50" />
            <p>No skills published yet</p>
            <p className="text-sm">Approve knowledge units and compile them into skills</p>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}