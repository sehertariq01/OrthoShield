"""
OrthoShield — custom Swagger UI wiring.

Save as: backend/custom_docs.py
Put swagger-theme.css at: backend/static/swagger-theme.css

Then in main.py:

    from fastapi import FastAPI
    from custom_docs import mount_custom_docs

    app = FastAPI(
        title="OrthoShield",
        description="Secure DICOM Medical Imaging Security Platform",
        version="1.0.0",
        docs_url=None,      # required — we serve our own /docs
        redoc_url=None,
    )
    mount_custom_docs(app)

Everything else in main.py stays exactly as it is.
"""

import os

from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
STATIC_DIR = os.path.join(BASE_DIR, "static")


def mount_custom_docs(app: FastAPI, docs_url: str = "/docs") -> None:
    """Serve a themed Swagger UI at `docs_url` and mount /static."""

    os.makedirs(STATIC_DIR, exist_ok=True)
    app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

    @app.get(docs_url, include_in_schema=False)
    async def custom_swagger_ui() -> HTMLResponse:
        return HTMLResponse(
            f"""<!DOCTYPE html>
<html lang="en" data-theme="orthoshield">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{app.title} — API</title>
  <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/swagger-ui-dist@5/swagger-ui.css">
  <link rel="stylesheet" href="/static/swagger-theme.css">
  <style>
    html, body {{ margin: 0; background: #0B121A; }}
    /* Masthead: states what the gateway does before the endpoint list. */
    .os-masthead {{
      background: #0B121A;
      border-bottom: 1px solid #24333F;
      color: #D8E2EA;
      font-family: 'Inter', system-ui, sans-serif;
      padding: 2.5rem 2rem 2rem;
    }}
    .os-masthead__inner {{ margin: 0 auto; max-width: 1160px; }}
    .os-eyebrow {{
      color: #45C8B8;
      font-family: 'IBM Plex Mono', monospace;
      font-size: .7rem;
      letter-spacing: .22em;
      margin: 0 0 .9rem;
      text-transform: uppercase;
    }}
    .os-title {{
      font-size: clamp(2rem, 5vw, 3.1rem);
      font-weight: 700;
      letter-spacing: -.03em;
      line-height: 1;
      margin: 0;
    }}
    .os-title span {{ color: #45C8B8; }}
    .os-sub {{
      color: #7B8FA1;
      font-size: 1rem;
      margin: .85rem 0 1.6rem;
      max-width: 46ch;
    }}
    .os-stats {{ display: flex; flex-wrap: wrap; gap: 2.5rem; }}
    .os-stat__num {{
      font-family: 'IBM Plex Mono', monospace;
      font-size: 1.5rem;
      font-weight: 500;
    }}
    .os-stat__label {{
      color: #7B8FA1;
      font-size: .68rem;
      letter-spacing: .14em;
      margin-top: .3rem;
      text-transform: uppercase;
    }}
    #swagger-ui {{ margin: 0 auto; max-width: 1200px; padding: 2rem 1rem 4rem; }}
    #swagger-ui .information-container {{ display: none; }}  /* masthead replaces it */
  </style>
</head>
<body>
  <header class="os-masthead">
    <div class="os-masthead__inner">
      <p class="os-eyebrow">DICOM Security Gateway &middot; v{app.version}</p>
      <h1 class="os-title">Ortho<span>Shield</span></h1>
      <p class="os-sub">Every uploaded study passes fourteen checks before it reaches the PACS. Clean studies forward. Everything else is quarantined and alerted on.</p>
      <div class="os-stats">
        <div class="os-stat"><div class="os-stat__num">14</div><div class="os-stat__label">Security checks</div></div>
        <div class="os-stat"><div class="os-stat__num">3</div><div class="os-stat__label">Scan engines</div></div>
        <div class="os-stat"><div class="os-stat__num">25</div><div class="os-stat__label">Block threshold</div></div>
      </div>
    </div>
  </header>

  <div id="swagger-ui"></div>

  <script src="https://cdn.jsdelivr.net/npm/swagger-ui-dist@5/swagger-ui-bundle.js"></script>
  <script>
    window.ui = SwaggerUIBundle({{
      url: "{app.openapi_url}",
      dom_id: "#swagger-ui",
      deepLinking: true,
      docExpansion: "list",
      defaultModelsExpandDepth: 0,
      persistAuthorization: true,
      tryItOutEnabled: true,
      presets: [SwaggerUIBundle.presets.apis],
      layout: "BaseLayout"
    }});
  </script>
</body>
</html>"""
        )
