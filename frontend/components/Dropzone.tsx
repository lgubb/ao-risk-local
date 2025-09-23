"use client";
import { useState, useRef, useCallback } from "react";
import { upload } from "@/lib/api";

type UploadedDoc = { document_id: string; filename?: string };

type Props = {
  onUploaded?: (docs: UploadedDoc[]) => void;
};

export default function Dropzone({ onUploaded }: Props) {
  const [dragover, setDragover] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [okMsg, setOkMsg] = useState<string | null>(null);
  const inputRef = useRef<HTMLInputElement | null>(null);

  const token = typeof window !== 'undefined' ? localStorage.getItem('token') : null;

  const handleFiles = useCallback(async (fileList: FileList | null) => {
    if (!fileList || fileList.length === 0) return;
    setError(null); setOkMsg(null); setLoading(true);
    try {
      const files = Array.from(fileList).filter(f => f.type === 'application/pdf' || f.name.endsWith('.pdf'));
      if (!files.length) { setError('Fichier PDF requis'); return; }
      const res = await upload(files, token || undefined);
      const docs: UploadedDoc[] = Array.isArray(res?.results)
        ? res.results.map((r: any) => ({ document_id: r.document_id as string, filename: r.filename as string | undefined }))
        : [];
      if (docs.length) {
        onUploaded?.(docs);
        const names = docs.map((d: UploadedDoc) => d.filename || d.document_id).join(', ');
        setOkMsg(`Import réussi: ${names}`);
      }
    } catch (e: any) {
      setError(e.message || 'Erreur upload');
    } finally {
      setLoading(false);
    }
  }, [token, onUploaded]);

  return (
    <div>
      <div
        className={`dropzone ${dragover ? 'dragover' : ''}`}
        onDragOver={(e) => { e.preventDefault(); setDragover(true); }}
        onDragLeave={() => setDragover(false)}
        onDrop={(e) => { e.preventDefault(); setDragover(false); handleFiles(e.dataTransfer.files); }}
        onClick={() => inputRef.current?.click()}
      >
        <div>
          <div className="muted">Cliquez ou déposez votre PDF ici</div>
          <div className="cta" style={{ display: 'inline-flex', gap: 8, alignItems: 'center' }}>
            <button className="btn secondary" disabled={loading}>{loading ? 'Envoi…' : 'Uploader un PDF'}</button>
          </div>
          <input
            ref={inputRef}
            type="file"
            accept="application/pdf"
            multiple
            style={{ display: 'none' }}
            onChange={(e) => handleFiles(e.target.files)}
          />
        </div>
      </div>
      {error && <p className="muted" style={{ marginTop: 8 }}>{error}</p>}
      {okMsg && <p className="muted" style={{ marginTop: 8 }}>{okMsg}</p>}
    </div>
  );
}
