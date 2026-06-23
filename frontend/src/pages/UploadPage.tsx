import { useState } from 'react'
import { FileText, Loader2, Upload } from 'lucide-react'
import { useNavigate } from 'react-router-dom'
import { ingestFile, ingestText } from '@/api/client'
import { Alert, AlertDescription } from '@/components/ui/alert'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { Textarea } from '@/components/ui/textarea'

export default function UploadPage() {
  const navigate = useNavigate()
  const [text, setText] = useState('')
  const [file, setFile] = useState<File | null>(null)
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState<string | null>(null)

  async function run(kind: 'text' | 'file') {
    setBusy(true)
    setError(null)
    try {
      const detail = kind === 'text' ? await ingestText(text) : await ingestFile(file as File)
      navigate(`/profiles/${detail.id}`)
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Ingestion failed.')
    } finally {
      setBusy(false)
    }
  }

  return (
    <section className="space-y-6">
      <div>
        <h1 className="text-2xl font-semibold tracking-tight">New profile</h1>
        <p className="mt-1 max-w-prose text-muted-foreground">
          Upload a PDF or paste text. The pipeline extracts a structured nonprofit profile and
          tracks the provenance of every field.
        </p>
      </div>

      {error && (
        <Alert variant="destructive">
          <AlertDescription>{error}</AlertDescription>
        </Alert>
      )}

      <Card>
        <CardHeader>
          <CardTitle>Ingest a document</CardTitle>
          <CardDescription>Choose how you'd like to provide the source material.</CardDescription>
        </CardHeader>
        <CardContent>
          <Tabs defaultValue="text">
            <TabsList className="w-full">
              <TabsTrigger value="text">Paste text</TabsTrigger>
              <TabsTrigger value="file">Upload PDF</TabsTrigger>
            </TabsList>

            <TabsContent value="text" className="space-y-4 pt-4">
              <Textarea
                value={text}
                onChange={(e) => setText(e.target.value)}
                placeholder="Paste a nonprofit's about page, annual report text, grant narrative…"
                className="min-h-64 font-mono text-xs"
              />
              <Button onClick={() => run('text')} disabled={busy || !text.trim()}>
                {busy ? (
                  <>
                    <Loader2 className="animate-spin" /> Extracting…
                  </>
                ) : (
                  'Extract profile'
                )}
              </Button>
            </TabsContent>

            <TabsContent value="file" className="space-y-4 pt-4">
              <label className="flex cursor-pointer flex-col items-center justify-center gap-2 rounded-lg border-2 border-dashed py-12 text-sm text-muted-foreground transition-colors hover:bg-muted/50">
                <input
                  type="file"
                  accept="application/pdf,.pdf"
                  className="hidden"
                  onChange={(e) => setFile(e.target.files?.[0] ?? null)}
                />
                {file ? <FileText className="size-5" /> : <Upload className="size-5" />}
                {file ? file.name : 'Choose a PDF…'}
              </label>
              <Button onClick={() => run('file')} disabled={busy || !file}>
                {busy ? (
                  <>
                    <Loader2 className="animate-spin" /> Extracting…
                  </>
                ) : (
                  'Extract profile'
                )}
              </Button>
            </TabsContent>
          </Tabs>
        </CardContent>
      </Card>
    </section>
  )
}
