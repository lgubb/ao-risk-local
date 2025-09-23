export type UploadedDoc = { document_id: string; filename?: string; type?: string };

const KEY = 'ao-risk:session-docs';

export function saveSessionDocs(docs: UploadedDoc[]) {
  try {
    sessionStorage.setItem(KEY, JSON.stringify(docs));
  } catch {}
}

export function getSessionDocs(): UploadedDoc[] {
  try {
    const raw = sessionStorage.getItem(KEY);
    if (!raw) return [];
    const arr = JSON.parse(raw);
    if (Array.isArray(arr)) return arr;
  } catch {}
  return [];
}

export function clearSessionDocs() {
  try { sessionStorage.removeItem(KEY); } catch {}
}

