import ReactMarkdown from 'react-markdown'

// Renders assistant Markdown (bold, italics, lists, links, code). Styled via
// descendant utilities since Tailwind's preflight strips list/heading styles.
export default function Markdown({ children }: { children: string }) {
  return (
    <div className="space-y-2 [&_a]:underline [&_a]:underline-offset-2 [&_code]:rounded [&_code]:bg-black/10 [&_code]:px-1 [&_code]:py-0.5 [&_code]:text-xs [&_li]:my-0.5 [&_ol]:list-decimal [&_ol]:pl-5 [&_p]:leading-relaxed [&_strong]:font-semibold [&_ul]:list-disc [&_ul]:pl-5">
      <ReactMarkdown>{children}</ReactMarkdown>
    </div>
  )
}
