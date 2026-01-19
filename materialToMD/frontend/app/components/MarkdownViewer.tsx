'use client';

import ReactMarkdown from 'react-markdown';

interface Props {
  content: string;
}

export default function MarkdownViewer({ content }: Props) {
  // If no content, render nothing (so the test waits)
  if (!content) return null;

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 gap-8 mt-8 border-t pt-8">
      
      {/* LEFT COLUMN: Raw Markdown (What the test is looking for) */}
      <div className="flex flex-col">
        <h3 className="font-semibold mb-2 text-gray-700">Raw Markdown</h3>
        <textarea
          readOnly
          value={content}
          className="w-full flex-1 min-h-[500px] p-4 border rounded font-mono text-sm bg-gray-50 focus:outline-none focus:ring-2 focus:ring-blue-500"
        />
      </div>

      {/* RIGHT COLUMN: Preview */}
      <div className="flex flex-col">
        <h3 className="font-semibold mb-2 text-gray-700">Preview</h3>
        <div className="w-full flex-1 min-h-[500px] p-6 border rounded overflow-y-auto prose prose-blue bg-white shadow-inner">
          <ReactMarkdown>{content}</ReactMarkdown>
        </div>
      </div>
      
    </div>
  );
}