// API base configurable for dev/prod via NEXT_PUBLIC_API_BASE.
// Defaults to direct FastAPI in dev to avoid Next proxy hangups.

const API_BASE = process.env.NEXT_PUBLIC_API_BASE || (process.env.NODE_ENV === 'development' ? 'http://localhost:8000' : '/api');

export async function login(username: string, password: string) {
  const body = new URLSearchParams({ username, password });
  const res = await fetch(`${API_BASE}/login`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
    body,
  });
  if (!res.ok) throw new Error('Login échoué');
  return res.json() as Promise<{ access_token: string; token_type: string }>;
}

export async function upload(files: File[], token?: string) {
  const form = new FormData();
  files.forEach((f) => form.append('files', f));
  const headers: Record<string, string> = {};
  if (token) headers['Authorization'] = `Bearer ${token}`;
  const res = await fetch(`${API_BASE}/upload-index`, { method: 'POST', headers, body: form });
  if (!res.ok) {
    try {
      const data = await res.json();
      const msg = (data && (data.detail || data.message)) || `Upload échoué (${res.status})`;
      throw new Error(msg);
    } catch {
      throw new Error(`Upload échoué (${res.status})`);
    }
  }
  return res.json();
}

export async function ask(question: string, documentId: string) {
  const res = await fetch(`${API_BASE}/query`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ question, document_id: documentId }),
  });
  if (!res.ok) throw new Error('Requête échouée');
  return res.json() as Promise<{
    question: string;
    answer: any;
    sources: Array<{
      id: string;
      filename: string;
      document_id: string;
      chunk_index?: number;
      doc_type?: string;
    }>;
  }>;
}
