'use client';
import { useState } from 'react';
import { upload } from '@/lib/api';
import { saveSessionDocs } from '@/lib/sessionDocs';

export default function UploadPage() {
  const [files, setFiles] = useState<FileList | null>(null);
  const [result, setResult] = useState<any>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  async function onUpload() {
    const token = localStorage.getItem('token');
    if (!token) return setError("Connecte-toi d’abord");
    if (!files || files.length === 0) return setError('Sélectionne au moins un PDF');
    setError(null);
    setLoading(true);
    try {
      const res = await upload(Array.from(files), token);
      setResult(res);
      // Sauver les document_ids de la session pour auto-sélection sur /query
      try {
        const docs = Array.isArray(res?.results)
          ? res.results.map((r: any) => ({ document_id: r.document_id, filename: r.filename, type: r.type }))
          : [];
        if (docs.length) saveSessionDocs(docs);
      } catch {}
    } catch (e: any) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="stack">
      <div className="card stack">
        <h2 className="title">Uploader des PDF</h2>
        <p className="subtitle">Sélectionnez un ou plusieurs fichiers PDF pour les indexer.</p>
        <input type="file" accept="application/pdf" multiple onChange={(e) => setFiles(e.target.files)} />
        <div className="row">
          <button className="btn" onClick={onUpload} disabled={loading}>{loading ? 'Indexation…' : 'Indexer'}</button>
          {files && files.length > 0 && <span className="badge">{files.length} fichier(s)</span>}
        </div>
      </div>

      {result && (
        <div className="card">
          <h3 className="title" style={{ fontSize: 18 }}>Résultat</h3>
          <pre className="pre">{JSON.stringify(result, null, 2)}</pre>
          <p className="muted">Tu peux maintenant aller sur <a href="/query">Query</a>: le document sera sélectionné automatiquement pendant cette session.</p>
        </div>
      )}
      {error && (
        <div className="card" style={{ borderColor: '#512', background: '#180f12' }}>
          <strong style={{ color: 'var(--danger)' }}>Erreur:</strong> <span className="muted">{error}</span>
        </div>
      )}
    </div>
  );
}
