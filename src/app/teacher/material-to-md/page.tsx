"use client";

import { useState } from "react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import { convertFile, type ConvertResponse } from "@/lib/materialToMdApi";

function base64ToDataUrl(contentType: string, b64: string) {
  return `data:${contentType};base64,${b64}`;
}

export default function MaterialToMdPage() {
  const [file, setFile] = useState<File | null>(null);
  const [busy, setBusy] = useState(false);
  const [result, setResult] = useState<ConvertResponse | null>(null);

  async function onConvert() {
    if (!file) return;
    setBusy(true);
    setResult(null);

    try {
      const r = await convertFile(file);
      setResult(r);
    } catch (e: any) {
      console.error(e);
      alert(e?.message ?? "Failed");
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="mx-auto max-w-6xl p-6">
      <h1 className="text-2xl font-bold">Material → Markdown</h1>
      <p className="mt-1 text-sm opacity-80">
        Upload a PPTX/DOCX/PDF and get Markdown + extracted assets immediately.
      </p>

      {/* Upload */}
      <div className="mt-6 rounded-2xl border p-4">
        <div className="text-base font-semibold">Upload & Convert (sync)</div>

        <div className="mt-3 flex flex-col gap-3 sm:flex-row sm:items-center">
          <input
            className="w-full rounded-lg border p-2 text-sm"
            type="file"
            accept=".pptx,.docx,.pdf,.txt,.html"
            onChange={(e) => setFile(e.target.files?.[0] ?? null)}
            disabled={busy}
          />
          <button
            onClick={onConvert}
            disabled={busy || !file}
            className="rounded-lg border px-4 py-2 text-sm hover:opacity-90 disabled:cursor-not-allowed disabled:opacity-50"
          >
            {busy ? "Converting…" : "Convert"}
          </button>
        </div>

        {result && (
          <div className="mt-3 text-xs opacity-80">
            Returned <b>{result.assets.length}</b> assets.
          </div>
        )}
      </div>

      {/* Preview + Assets */}
      <div className="mt-6 grid gap-4 lg:grid-cols-2">
        {/* Markdown Preview */}
        <div className="rounded-2xl border p-4">
          <div className="text-base font-semibold">Markdown Preview</div>

          {!result ? (
            <p className="mt-2 text-sm opacity-70">Upload a file and click Convert.</p>
          ) : (
            <div className="mt-3 max-h-[650px] overflow-auto rounded-xl border p-3">
              <ReactMarkdown remarkPlugins={[remarkGfm]}>
                {result.markdown || "_(empty)_"}
              </ReactMarkdown>
            </div>
          )}
        </div>

        {/* Assets */}
        <div className="rounded-2xl border p-4">
          <div className="text-base font-semibold">Extracted Assets</div>

          {!result ? (
            <p className="mt-2 text-sm opacity-70">Assets (images, etc.) will appear here.</p>
          ) : result.assets.length === 0 ? (
            <p className="mt-2 text-sm opacity-70">No assets returned.</p>
          ) : (
            <div className="mt-3 space-y-3">
              {result.assets.map((a) => {
                const url = base64ToDataUrl(a.content_type, a.data_base64);

                const isImage = a.content_type.startsWith("image/");
                return (
                  <div key={a.path} className="rounded-xl border p-3">
                    <div className="text-sm font-semibold">{a.path}</div>
                    <div className="text-xs opacity-70">{a.content_type}</div>

                    {isImage && (
                      <img
                        src={url}
                        alt={a.path}
                        className="mt-3 max-h-64 w-full rounded-lg object-contain"
                      />
                    )}

                    <a
                      href={url}
                      download={a.path.split("/").pop() ?? "asset"}
                      className="mt-3 inline-block rounded-lg border px-3 py-2 text-sm hover:opacity-90"
                    >
                      Download
                    </a>
                  </div>
                );
              })}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
