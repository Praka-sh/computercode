'use client'

import { useState, useEffect } from 'react'
import { api } from '@/lib/api'
import { Source, SourceStatus } from '@/types'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Upload, FileText, Loader2, AlertCircle, CheckCircle } from 'lucide-react'

interface SourceWithJob extends Source {
  job_id?: string
  deduplicated?: boolean
}

export default function SourcesPage() {
  const [sources, setSources] = useState<SourceWithJob[]>([])
  const [loading, setLoading] = useState(true)
  const [uploading, setUploading] = useState(false)
  const [dragActive, setDragActive] = useState(false)
  const [selectedFile, setSelectedFile] = useState<File | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [success, setSuccess] = useState<string | null>(null)

  useEffect(() => {
    fetchSources()
  }, [])

  const fetchSources = async () => {
    try {
      setLoading(true)
      const response = await api.get('/sources/')
      setSources(response.data)
      setLoading(false)
    } catch (err) {
      console.error('Failed to fetch sources:', err)
      setLoading(false)
    }
  }

  const handleDrag = (e: React.DragEvent) => {
    e.preventDefault()
    e.stopPropagation()
    if (e.type === 'dragenter' || e.type === 'dragover') {
      setDragActive(true)
    } else if (e.type === 'dragleave') {
      setDragActive(false)
    }
  }

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault()
    e.stopPropagation()
    setDragActive(false)

    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      setSelectedFile(e.dataTransfer.files[0])
    }
  }

  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      setSelectedFile(e.target.files[0])
    }
  }

  const validateFile = (file: File): string | null => {
    const allowedTypes = [
      'application/pdf',
      'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
      'text/plain',
      'text/markdown',
    ]
    const maxSize = 50 * 1024 * 1024 // 50MB

    if (!allowedTypes.includes(file.type)) {
      return `Unsupported file type: ${file.type}. Allowed: PDF, DOCX, TXT, MD`
    }

    if (file.size > maxSize) {
      return `File size exceeds maximum of 50MB`
    }

    if (file.size === 0) {
      return 'Empty file not allowed'
    }

    return null
  }

  const handleUpload = async () => {
    if (!selectedFile) return

    const validationError = validateFile(selectedFile)
    if (validationError) {
      setError(validationError)
      return
    }

    setUploading(true)
    setError(null)
    setSuccess(null)

    try {
      const formData = new FormData()
      formData.append('file', selectedFile)
      formData.append('kind', 'file')

      const response = await api.post('/sources/upload', formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
      })

      setSuccess(`Upload successful! ${response.data.deduplicated ? 'File was deduplicated.' : `Job ID: ${response.data.job_id}`}`)
      setSelectedFile(null)
      fetchSources() // Refresh list
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Upload failed')
    } finally {
      setUploading(false)
    }
  }

  const getStatusBadge = (status: SourceStatus) => {
    switch (status) {
      case 'active':
        return <Badge variant="success">Active</Badge>
      case 'syncing':
        return <Badge variant="warning"><Loader2 className="mr-1 h-3 w-3 animate-spin" /> Syncing</Badge>
      case 'error':
        return <Badge variant="destructive"><AlertCircle className="mr-1 h-3 w-3" /> Error</Badge>
      case 'archived':
        return <Badge variant="secondary">Archived</Badge>
      default:
        return <Badge variant="outline">{status}</Badge>
    }
  }

  return (
    <div className="container mx-auto px-4 py-8">
      <div className="mb-8">
        <h1 className="text-3xl font-bold">Sources</h1>
        <p className="text-muted-foreground">Upload and manage policy documents</p>
      </div>

      {/* Upload Zone */}
      <Card className="mb-8">
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Upload className="h-5 w-5" />
            Upload Document
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div
            className={`border-2 border-dashed rounded-lg p-8 text-center transition-colors ${
              dragActive ? 'border-primary bg-primary/5' : 'border-border'
            }`}
            onDragEnter={handleDrag}
            onDragLeave={handleDrag}
            onDragOver={handleDrag}
            onDrop={handleDrop}
          >
            <input
              type="file"
              id="file-upload"
              accept=".pdf,.docx,.txt,.md"
              onChange={handleFileSelect}
              className="hidden"
              disabled={uploading}
            />
            <label
              htmlFor="file-upload"
              className="cursor-pointer"
            >
              <Upload className="h-12 w-12 mx-auto text-muted-foreground mb-4" />
              <p className="text-lg font-medium mb-2">
                Drag & drop a file here, or click to browse
              </p>
              <p className="text-sm text-muted-foreground">
                PDF, DOCX, TXT, MD · Max 50MB
              </p>
            </label>

            {selectedFile && (
              <div className="mt-4 p-4 bg-card border rounded-lg text-left">
                <div className="flex items-center gap-3">
                  <FileText className="h-6 w-6 text-primary" />
                  <div className="flex-1">
                    <p className="font-medium">{selectedFile.name}</p>
                    <p className="text-sm text-muted-foreground">
                      {(selectedFile.size / 1024 / 1024).toFixed(2)} MB · {selectedFile.type}
                    </p>
                  </div>
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => setSelectedFile(null)}
                  >
                    Remove
                  </Button>
                </div>
              </div>
            )}
          </div>

          {error && (
            <div className="mt-4 p-4 bg-red-50 border border-red-200 rounded-lg text-red-800">
              {error}
            </div>
          )}

          {success && (
            <div className="mt-4 p-4 bg-green-50 border border-green-200 rounded-lg text-green-800">
              <CheckCircle className="h-5 w-5 inline mr-2" />
              {success}
            </div>
          )}

          <div className="mt-4 flex justify-center">
            <Button
              onClick={handleUpload}
              disabled={!selectedFile || uploading}
              size="lg"
            >
              {uploading ? (
                <>
                  <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                  Uploading...
                </>
              ) : (
                'Upload Document'
              )}
            </Button>
          </div>
        </CardContent>
      </Card>

      {/* Sources List */}
      <Card>
        <CardHeader>
          <CardTitle>Documents</CardTitle>
        </CardHeader>
        <CardContent>
          {loading ? (
            <div className="flex justify-center py-8">
              <Loader2 className="h-8 w-8 animate-spin text-primary" />
            </div>
          ) : sources.length === 0 ? (
            <div className="text-center py-8 text-muted-foreground">
              <FileText className="h-12 w-12 mx-auto mb-4 opacity-50" />
              <p>No documents uploaded yet</p>
              <p className="text-sm">Upload your first policy document to get started</p>
            </div>
          ) : (
            <div className="space-y-4">
              {sources.map((source) => (
                <div
                  key={source.id}
                  className="flex items-center justify-between p-4 border rounded-lg hover:bg-accent/50 transition-colors"
                >
                  <div className="flex items-center gap-4">
                    <FileText className="h-8 w-8 text-primary" />
                    <div>
                      <p className="font-medium">{source.external_key || `Source ${source.id.slice(0, 8)}`}</p>
                      <p className="text-sm text-muted-foreground">
                        {source.kind} · {new Date(source.created_at).toLocaleDateString()}
                      </p>
                    </div>
                  </div>
                  <div className="flex items-center gap-3">
                    {getStatusBadge(source.status)}
                    {source.deduplicated && (
                      <Badge variant="info">Deduplicated</Badge>
                    )}
                  </div>
                </div>
              ))}
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  )
}