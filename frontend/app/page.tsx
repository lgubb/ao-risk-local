"use client";
import { useEffect, useRef, useState } from 'react';
import Dropzone from '@/components/Dropzone';
import Spinner from '@/components/Spinner';
import { ask, upload } from '@/lib/api';
import { clearSessionDocs, type UploadedDoc } from '@/lib/sessionDocs';

type Msg = { role: 'user' | 'assistant' | 'system'; content: string; source?: { label?: string; url?: string; page?: number | null } };

export default function Home() {
  const [docs, setDocs] = useState<UploadedDoc[]>([]);
  const [documentId, setDocumentId] = useState('');
  const [messages, setMessages] = useState<Msg[]>([{
    role: 'assistant',
    content: "Bonjour ! Que puis-je faire pour vous ?",
  }]);
  const [question, setQuestion] = useState('');
  const [loading, setLoading] = useState(false);
  const [demoLoading, setDemoLoading] = useState(false);
  const [demoLoaded, setDemoLoaded] = useState(false);
  const presetQuestions = [
    'Quels sont les délais d’intervention exigés en cas d’urgence ?',
    'Quels sont les critères d’attribution prioritaires ?',
    'Quelle est la durée du contrat ?',
    'Comment sont structurés les prix et paiements ?',
    'Quelles pénalités s’appliquent en cas de non-respect ?',
    'Quelles sont les obligations contractuelles du titulaire ?',
  ];
  const listRef = useRef<HTMLDivElement | null>(null);

  function mergeDocs(prev: UploadedDoc[], incoming: UploadedDoc[]): UploadedDoc[] {
    const map = new Map<string, UploadedDoc>();
    for (const d of prev) map.set(d.document_id, d);
    for (const d of incoming) map.set(d.document_id, d);
    return Array.from(map.values());
  }

  useEffect(() => {
    // Ne pas persister entre rafraîchissements: on purge toute ancienne session
    try { clearSessionDocs(); } catch {}
  }, []);

  useEffect(() => {
    listRef.current?.scrollTo({ top: listRef.current.scrollHeight });
  }, [messages, loading]);

  // Auto-charger un document de démonstration à chaque arrivée/refresh (sans messages dans le chat)
  useEffect(() => {
    let cancelled = false;
    (async () => {
      try {
        setDemoLoading(true);
        setDemoLoaded(false);
        const url = '/exemple-dce-maintenance-industrielle.pdf';
        const res = await fetch(url);
        if (!res.ok) return; // Fichier absent: on ignore
        const blob = await res.blob();
        const file = new File([blob], 'exemple-dce-maintenance-industrielle.pdf', { type: 'application/pdf' });
        const token = typeof window !== 'undefined' ? localStorage.getItem('token') || undefined : undefined;
        const out = await upload([file], token);
        const upDocs = Array.isArray(out?.results)
          ? out.results.map((r: any) => ({ document_id: r.document_id, filename: r.filename }))
          : [];
        if (!cancelled && upDocs.length) {
          setDocs(prev => mergeDocs(prev, upDocs));
          setDocumentId(id => id || upDocs[0].document_id);
          setDemoLoaded(true);
        }
      } catch {
        // silence: en cas d'échec, on n'affiche pas de message dans le chat
      } finally {
        if (!cancelled) setDemoLoading(false);
      }
    })();
    return () => { cancelled = true; };
  }, []);

  async function sendQuestion(q: string) {
    const toSend = q.trim();
    if (!toSend) return;
    if (!documentId) {
      setMessages(m => [...m, { role: 'system', content: 'Aucun document sélectionné. Uploadez un PDF puis réessayez.' }]);
      return;
    }
    setMessages(m => [...m, { role: 'user', content: toSend }]);
    setLoading(true);
    try {
      const res = await ask(toSend, documentId);
      const answer = (res?.answer?.reponse ?? '').toString();
      const source = res?.answer?.source as { label?: string; url?: string; page?: number } | undefined;
      setMessages(m => [...m, { role: 'assistant', content: answer || '—', source }]);
    } catch (e: any) {
      setMessages(m => [...m, { role: 'system', content: e?.message || 'Erreur' }]);
    } finally {
      setLoading(false);
    }
  }

  async function onSend(e?: React.FormEvent) {
    e?.preventDefault();
    const q = question.trim();
    setQuestion('');
    await sendQuestion(q);
  }

  return (
    <div className="stack">
      <section className="hero stack">
        <h1 className="brand-title">AO Risk</h1>
        <p>Votre copilote intelligent pour analyser vos appels d’offres publics.</p>
        <Dropzone onUploaded={(d) => { setDocs(prev => mergeDocs(prev, d)); setDocumentId(d[0]?.document_id || ''); }} />
      </section>

      <section className="chat">
        <div className="row" style={{ justifyContent: 'space-between' }}>
          <div className="row">
            <h2 className="title" style={{ margin: 0 }}>Chat</h2>
            {demoLoading && (
              <span className="badge"><span className="spinner" style={{ marginRight: 6 }} />Envoi du document de démo…</span>
            )}
            {!demoLoading && demoLoaded && <span className="badge success">Document de démo chargé</span>}
          </div>
          <div className="row">
            <select className="input" value={documentId} onChange={(e) => setDocumentId(e.target.value)} style={{ maxWidth: 420 }}>
              <option value="">Sélectionner un document (session)</option>
              {docs.map((d) => (
                <option key={d.document_id} value={d.document_id}>
                  {d.filename || d.document_id}
                </option>
              ))}
            </select>
          </div>
        </div>

        <div ref={listRef} className="chat-window">
          {messages.map((m, i) => (
            <div className="chat-msg" key={i}>
              <div className="chat-avatar">{m.role === 'user' ? 'U' : m.role === 'assistant' ? 'A' : '!'}</div>
              <div className="chat-bubble">
                {m.content.split('\n').map((line, j) => (
                  <p key={j} style={{ margin: '6px 0' }}>{line}</p>
                ))}
                {m.role === 'assistant' && m.source && (m.source.label || m.source.url) && (
                  <div className="row" style={{ marginTop: 8, justifyContent: 'space-between' }}>
                    <span className="muted">Source: {m.source.label || '—'}{typeof m.source.page === 'number' ? ` (p.${m.source.page})` : ''}</span>
                    {m.source.url && (
                      <a className="pill" href={m.source.url} target="_blank" rel="noreferrer">Ouvrir la page</a>
                    )}
                  </div>
                )}
              </div>
            </div>
          ))}
          {loading && (
            <div className="chat-msg">
              <div className="chat-avatar">A</div>
              <div className="chat-bubble"><Spinner /> <span style={{ marginLeft: 8 }}>Rédaction de la réponse…</span></div>
            </div>
          )}
        </div>

        {/* Preset questions */}
        <div className="row" style={{ alignItems: 'center', gap: 8, marginTop: 12 }}>
          <span className="badge info">Questions prédéfinies · doc démo</span>
        </div>
        <div className="row" style={{ flexWrap: 'wrap', gap: 8, marginTop: 8 }}>
          {presetQuestions.map((q) => (
            <button
              key={q}
              type="button"
              className="pill"
              style={{ cursor: 'pointer' }}
              onClick={() => sendQuestion(q)}
              disabled={loading}
            >
              {q}
            </button>
          ))}
        </div>

        <form onSubmit={onSend} className="chat-input">
          <input className="input" value={question} placeholder="Posez une question…" onChange={(e) => setQuestion(e.target.value)} />
          <button className="btn secondary" type="submit" disabled={loading || !question.trim()}>Envoyer</button>
        </form>
      </section>
    </div>
  );
}
