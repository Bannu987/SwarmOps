"use client"

import ReactMarkdown from "react-markdown"
import remarkGfm from "remark-gfm"
import rehypeRaw from "rehype-raw"
import type { Components } from "react-markdown"

const components: Components = {
  a: ({ ...props }) => (
    <a
      {...props}
      target="_blank"
      rel="noopener noreferrer"
      className="text-primary hover:underline"
    />
  ),
  // @ts-expect-error inline prop added by react-markdown
  code: ({ inline, children, ...props }) =>
    inline ? (
      <code className="bg-muted px-1.5 py-0.5 rounded text-sm font-mono" {...props}>
        {children}
      </code>
    ) : (
      <pre className="bg-muted border border-border rounded-lg p-3 my-3 overflow-x-auto">
        <code className="text-sm font-mono" {...props}>
          {children}
        </code>
      </pre>
    ),
}

export function Markdown({ content }: { content: string }) {
  return (
    <div className="prose-swarm text-sm">
      <ReactMarkdown
        remarkPlugins={[remarkGfm]}
        rehypePlugins={[rehypeRaw]}
        components={components}
      >
        {content}
      </ReactMarkdown>
    </div>
  )
}
