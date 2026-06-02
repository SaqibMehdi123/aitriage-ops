"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { deleteKnowledge, listKnowledge, uploadKnowledgeFile, uploadKnowledgeText } from "@/lib/triage";
import type { KnowledgeDoc } from "@/lib/types";
import { Icon, Spinner } from "@/components/ui";

const STATUS_STYLES: Record<string, string> = {
  pending: "bg-surface-container-high text-on-surface-variant",
  embedding: "bg-primary-fixed text-on-primary-fixed",
  synced: "bg-tertiary-fixed text-on-tertiary-fixed",
  error: "bg-error-container text-on-error-container",
};

export default function KnowledgePage() {
  const [docs, setDocs] = useState<KnowledgeDoc[]>([]);
  const [loading, setLoading] = useState(true);
  const [title, setTitle] = useState("");
  const [content, setContent] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [dragOver, setDragOver] = useState(false);
  const [fileBusy, setFileBusy] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);

  async function handleFiles(files: FileList | null) {
    if (!files || files.length === 0) return;
    setFileBusy(true);
    setError(null);
    try {
      for (const file of Array.from(files)) {
        await uploadKnowledgeFile(file);
      }
      setTimeout(load, 1500);
    } catch (e) {
      setError(e instanceof Error ? e.message : "File upload failed");
    } finally {
      setFileBusy(false);
      if (fileInputRef.current) fileInputRef.current.value = "";
    }
  }

  const load = useCallback(async () => {
    setLoading(true);
    try {
      setDocs(await listKnowledge());
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to load");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    load();
  }, [load]);

  async function upload() {
    if (!title.trim() || !content.trim()) return;
    setBusy(true);
    setError(null);
    try {
      await uploadKnowledgeText(title.trim(), content.trim());
      setTitle("");
      setContent("");
      setTimeout(load, 1500); // let the embed worker run, then refresh status
    } catch (e) {
      setError(e instanceof Error ? e.message : "Upload failed");
    } finally {
      setBusy(false);
    }
  }

  async function remove(docId: string) {
    await deleteKnowledge(docId).catch(() => {});
    setDocs((d) => d.filter((x) => x.id !== docId));
  }

  return (
    <div className="p-margin-desktop max-w-container-max">
      <header className="mb-lg">
        <h1 className="text-display-lg">Knowledge Base</h1>
        <p className="text-body-md text-on-surface-variant">
          Upload documents to ground AI replies in your own answers.
        </p>
      </header>

      {error && (
        <div className="mb-md rounded-lg border border-error-container bg-error-container text-on-error-container px-md py-sm text-body-sm">
          {error}
        </div>
      )}

      <section className="rounded-xl border border-outline-variant bg-surface-container-lowest p-lg mb-lg">
        <h2 className="text-headline-sm mb-md">Add a document</h2>

        {/* File upload dropzone */}
        <div
          onClick={() => fileInputRef.current?.click()}
          onDragOver={(e) => { e.preventDefault(); setDragOver(true); }}
          onDragLeave={() => setDragOver(false)}
          onDrop={(e) => { e.preventDefault(); setDragOver(false); handleFiles(e.dataTransfer.files); }}
          className={`mb-md cursor-pointer rounded-lg border-2 border-dashed px-lg py-xl flex flex-col items-center justify-center text-center gap-xs transition-colors ${
            dragOver ? "border-primary bg-surface-container-low" : "border-outline-variant hover:bg-surface-container-low"
          }`}
        >
          <input
            ref={fileInputRef}
            type="file"
            multiple
            accept=".pdf,.doc,.docx,.txt,.md,.markdown,.text"
            className="hidden"
            onChange={(e) => handleFiles(e.target.files)}
          />
          {fileBusy ? (
            <Spinner label="Uploading & embedding…" />
          ) : (
            <>
              <span className="w-12 h-12 rounded-lg bg-surface-container-high flex items-center justify-center mb-xs">
                <Icon name="cloud_upload" className="text-[24px] text-on-surface-variant" />
              </span>
              <p className="text-body-sm text-on-surface font-medium">Click to upload or drag and drop</p>
              <p className="text-label-sm text-on-surface-variant">PDF, DOCX, TXT or Markdown</p>
            </>
          )}
        </div>

        <div className="flex items-center gap-md my-md">
          <div className="h-px bg-outline-variant flex-1" />
          <span className="text-label-sm text-on-surface-variant">or paste text</span>
          <div className="h-px bg-outline-variant flex-1" />
        </div>

        <div className="flex flex-col gap-md">
          <input
            value={title}
            onChange={(e) => setTitle(e.target.value)}
            placeholder="Title (e.g. Refund Policy)"
            className="rounded border border-outline-variant bg-surface-container-lowest px-md py-sm text-body-sm focus:outline-none focus:ring-2 focus:ring-primary"
          />
          <textarea
            value={content}
            onChange={(e) => setContent(e.target.value)}
            placeholder="Paste the document text (FAQ, policy, canned answers)…"
            rows={6}
            className="rounded border border-outline-variant bg-surface-container-lowest px-md py-sm text-body-sm resize-y focus:outline-none focus:ring-2 focus:ring-primary"
          />
          <div>
            <button
              onClick={upload}
              disabled={busy || !title.trim() || !content.trim()}
              className="rounded bg-primary text-on-primary px-md py-sm text-label-md font-medium hover:bg-primary-container transition-colors disabled:opacity-60 flex items-center gap-xs"
            >
              <Icon name="upload" className="text-[18px]" /> {busy ? "Uploading…" : "Upload & embed"}
            </button>
          </div>
        </div>
      </section>

      <section className="rounded-xl border border-outline-variant bg-surface-container-lowest overflow-hidden">
        <div className="px-lg py-md border-b border-outline-variant text-label-sm text-on-surface-variant uppercase tracking-wide">
          Uploaded sources
        </div>
        {loading ? (
          <div className="px-lg py-xl flex justify-center"><Spinner label="Loading…" /></div>
        ) : docs.length === 0 ? (
          <div className="px-lg py-xl text-center text-body-sm text-on-surface-variant">
            No documents yet. Add one above to ground your AI replies.
          </div>
        ) : (
          docs.map((d) => (
            <div key={d.id} className="px-lg py-md border-b border-surface-container-high last:border-0 flex items-center justify-between">
              <div className="flex items-center gap-sm min-w-0">
                <Icon name="description" className="text-on-surface-variant" />
                <div className="min-w-0">
                  <p className="text-body-sm text-on-surface truncate">{d.title}</p>
                  <p className="text-label-sm text-on-surface-variant truncate">{d.source}</p>
                </div>
              </div>
              <div className="flex items-center gap-md">
                <span className={`rounded-full px-sm py-unit text-label-sm font-medium capitalize ${STATUS_STYLES[d.status] ?? STATUS_STYLES.pending}`}>
                  {d.status}
                </span>
                <button onClick={() => remove(d.id)} className="p-xs hover:bg-surface-container rounded text-on-surface-variant">
                  <Icon name="delete" className="text-[20px]" />
                </button>
              </div>
            </div>
          ))
        )}
      </section>
    </div>
  );
}
