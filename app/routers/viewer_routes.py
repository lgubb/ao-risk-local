from fastapi import APIRouter, Query
from starlette.responses import HTMLResponse, FileResponse
import os, json

router = APIRouter()

TEMPLATE = """
<!doctype html>
<html lang="fr">
  <head>
    <meta charset="utf-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1" />
    <title>AO Risk — Viewer</title>
    <style>
      :root{ --bg:#0b0c10; --text:#d1d5db; --panel:#161b22; --border:#30363d }
      html,body{height:100%}
      body{margin:0;font-family:ui-sans-serif,system-ui,-apple-system,Segoe UI,Roboto,Ubuntu,Cantarell,Noto Sans,Helvetica Neue,Arial;background:var(--bg);color:var(--text)}
      .container{max-width:960px;margin:0 auto;padding:16px}
      .card{background:var(--panel);border:1px solid var(--border);border-radius:12px;padding:16px}
      .page{border:1px solid var(--border);border-radius:10px;padding:12px;margin:12px 0;background:#0f141a}
      .muted{color:#9aa0a6}
      .anchor{color:#9aa0a6;text-decoration:none}
      .anchor:hover{color:#66fcf1}
      .badge{display:inline-block;padding:4px 8px;border:1px solid var(--border);border-radius:999px;font-size:12px;color:#aab1ba}
    </style>
  </head>
  <body>
    <div class="container">
      <div class="card">
        <h2>Document {doc_id}</h2>
        <p class="muted">Pages extraites (texte).</p>
        {content}
      </div>
    </div>
    <script>
      const hash = new URLSearchParams(window.location.search).get('page');
      if (hash) {
        const el = document.getElementById('page-' + hash);
        if (el) el.scrollIntoView({ behavior: 'smooth', block: 'start' });
      }
    </script>
  </body>
  </html>
"""

@router.get("/viewer/{document_id}", response_class=HTMLResponse)
def view_document(document_id: str, page: int | None = Query(default=None)):
    pages_path = os.path.join("storage", f"{document_id}_pages.json")
    if not os.path.exists(pages_path):
        return HTMLResponse(
            content=f"<html><body style='background:#0b0c10;color:#d1d5db;font-family:sans-serif;padding:20px'>Aucune page trouvée pour {document_id}</body></html>",
            status_code=404,
        )

    with open(pages_path, "r", encoding="utf-8") as f:
        pages = json.load(f)

    sections = []
    for p in pages:
        num = p.get("page")
        text = p.get("text", "")
        sections.append(
            f"<div id='page-{num}' class='page'><div class='badge'>p.{num}</div><pre style='white-space:pre-wrap'>{text}</pre><a class='anchor' href='#top'>↑ Haut</a></div>"
        )

    html = TEMPLATE.replace("{doc_id}", document_id).replace("{content}", "\n".join(sections))
    return HTMLResponse(content=html)


@router.get("/files/{document_id}.pdf")
def get_pdf(document_id: str):
    path = os.path.join("storage", f"{document_id}.pdf")
    if not os.path.exists(path):
        return HTMLResponse(
            content=f"<html><body style='background:#0b0c10;color:#d1d5db;font-family:sans-serif;padding:20px'>PDF introuvable pour {document_id} — réuploadez ce document.</body></html>",
            status_code=404,
        )
    return FileResponse(path, media_type="application/pdf")
