import BackendStatus from '../components/BackendStatus'

export default function UploadPage() {
  return (
    <section className="space-y-4">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-semibold tracking-tight">Upload a document</h1>
        <BackendStatus />
      </div>
      <p className="max-w-prose text-slate-600">
        Upload a PDF or paste text and the pipeline will extract a structured nonprofit
        profile, tracking the provenance of every field. (Slice 1)
      </p>
    </section>
  )
}
