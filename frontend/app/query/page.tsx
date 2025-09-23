'use client';
import { useEffect, useState } from 'react';
import { ask } from '@/lib/api';
import Spinner from '@/components/Spinner';
import { getSessionDocs, type UploadedDoc } from '@/lib/sessionDocs';

type QueryResponse = {
  question: string;
  answer?: { reponse?: string; used_chunks?: number; [k: string]: any };
  sources?: Array<{ id: string; filename: string; document_id: string; chunk_index?: number; doc_type?: string }>;
};

export default function QueryPage() {
  const [question, setQuestion] = useState('');
  const [documentId, setDocumentId] = useState('');
  const [docs, setDocs] = useState<UploadedDoc[]>([]);
  const [data, setData] = useState<QueryResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    const d = getSessionDocs();
    setDocs(d);
    if (d.length && !documentId) setDocumentId(d[0].document_id);
  }, []);

  async function onAsk(e?: React.FormEvent) {
    e?.preventDefault();
    setError(null);
    setLoading(true);
    setData(null);
    try {
      if (!documentId) throw new Error('Aucun document sélectionné. Uploade un PDF dans Upload.');
      const res = await ask(question, documentId);
      setData(res);
    } catch (e: any) {
      setError(e.message || 'Erreur');
    } finally {
      setLoading(false);
    }
  }

  const answerText = data?.answer?.reponse || '';

  return (
    <div className="stack">
      <div className="card stack">
        <h2 className="title">Poser une question</h2>
        <p className="subtitle">Interrogez vos documents indexés. Optionnel: préciser un document_id pour cibler un fichier.</p>
        <form onSubmit={onAsk} className="stack">
          <input className="input" placeholder="Votre question..." value={question} onChange={(e) => setQuestion(e.target.value)} />
          <div className="row">
            <select className="input" value={documentId} onChange={(e) => setDocumentId(e.target.value)} style={{ maxWidth: 500 }}>
              <option value="">Sélectionner un document (session)</option>
              {docs.map((d) => (
                <option key={d.document_id} value={d.document_id}>
                  {d.filename || d.document_id}
                </option>
              ))}
            </select>
            {!docs.length && (
              <span className="muted">Aucun document en session. Va sur <a href="/upload">Upload</a>.</span>
            )}
          </div>
          <div className="row">
            <button className="btn secondary" type="submit" disabled={loading || !question.trim()}>
              {loading ? (<><Spinner /> <span style={{ marginLeft: 8 }}>Envoi…</span></>) : 'Envoyer'}
            </button>
            {data?.answer?.used_chunks != null && (
              <span className="badge">chunks utilisés: {data.answer.used_chunks}</span>
            )}
          </div>
        </form>
      </div>

      {loading && (
        <div className="card row" style={{ justifyContent: 'center' }}>
          <Spinner size={18} />
          <span>Génération de la réponse…</span>
        </div>
      )}

      {error && (
        <div className="card" style={{ borderColor: '#512', background: '#180f12' }}>
          <strong style={{ color: 'var(--danger)' }}>Erreur:</strong> <span className="muted">{error}</span>
        </div>
      )}

      {answerText && (
        <div className="card stack">
          <h3 className="title" style={{ fontSize: 18 }}>Réponse</h3>
          <div className="answer">
            {answerText.split('\n').map((line, i) => (
              <p key={i}>{line}</p>
            ))}
          </div>
        </div>
      )}

      {!!(data?.sources && data.sources.length) && (
        <div className="card stack">
          <h3 className="title" style={{ fontSize: 18 }}>Sources</h3>
          <div className="grid">
            {data!.sources!.map((s) => (
              <div key={s.id} className="card">
                <div className="stack">
                  <div className="row" style={{ justifyContent: 'space-between' }}>
                    <strong>{s.filename}</strong>
                    {s.doc_type && <span className="badge">{s.doc_type}</span>}
                  </div>
                  <span className="muted">document_id: {s.document_id}</span>
                  {typeof s.chunk_index === 'number' && (
                    <span className="muted">chunk: {s.chunk_index}</span>
                  )}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
