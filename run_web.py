import asyncio
from pathlib import Path
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
import re
from datetime import datetime
from report_generator import build_domain_report_html
from generar_informe import generar_informe_score
from generar_recomendaciones_personalizadas import generar_recomendaciones_html, RecomendacionesParams

# ---------- Paths ----------

BASE_DIR = Path(__file__).resolve().parent          # project/
WEB_DIR = BASE_DIR / "web"                          # project/web
INDEX_FILE = WEB_DIR / "index.html"                 # project/web/index.html
REPORTS_DIR = WEB_DIR / "reports"                   # project/web/reports
REPORTS_DIR.mkdir(parents=True, exist_ok=True)      # ensure exists

# ---------- App ----------

app = FastAPI(title="DominAI Backend")

# CORS (relaxed for development; tighten in production)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],        # e.g. ["http://localhost:8000"]
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Serve the whole "web" folder (css, js, images, etc.) at /web/...
app.mount("/web", StaticFiles(directory=WEB_DIR), name="web")


# ---------- Frontend route ----------

@app.get("/", include_in_schema=False)
async def serve_index():
    """
    Serve the main index.html (your existing frontend).
    """
    return FileResponse(INDEX_FILE)


# ---------- Models ----------

class DomainRequest(BaseModel):
    domain: str


class DomainResponse(BaseModel):
    domain: str
    status: str
    detail: str
    report_url : str

# ---------- Helpers ----------

def _slugify_domain(domain: str) -> str:
    """
    Turn the domain into a safe-ish filename base.
    """
    # keep letters, numbers, dot and dash; replace others with '_'
    base = re.sub(r"[^a-zA-Z0-9\.\-]", "_", domain)
    if not base:
        base = "report"
    return base

# ---------- Your Python logic ----------


async def run_python_logic(domain: str) -> DomainResponse:
    is_likely_valid = "." in domain and " " not in domain

    if not is_likely_valid:
        return DomainResponse(
            domain=domain,
            status="error",
            detail="The provided string does not look like a valid domain.",
            report_url=None,
        )

    # 1) Llamada async (tu función ya es async)
    tablas, rec_params = await generar_informe_score(domain)

    # Armamos el HTML final
    html_content = build_domain_report_html(
        domain,
        tablas,
        111,
        "RECOMENDACIONES_DIV_AQUI"
    )

    # 2) Filename único
    slug = _slugify_domain(domain)
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    filename = f"{slug}_{timestamp}.html"
    file_path = REPORTS_DIR / filename

    # 3) Escritura async del archivo (sin bloquear)
    await asyncio.to_thread(
        file_path.write_text,
        html_content,
        "utf-8"
    )

    # 4) URL pública
    report_url = f"/web/reports/{filename}"

    return DomainResponse(
        domain=domain,
        status="ok",
        detail=f"Report generated for domain '{domain}'.",
        report_url=report_url,
    )

# ---------- API Routes ----------

@app.post("/api/query", response_model=DomainResponse)
async def query_domain(payload: DomainRequest):
    """
    Endpoint called from the frontend.
    """
    result = await run_python_logic(payload.domain)
    print(result)
    return result


# Optional healthcheck
@app.get("/health", include_in_schema=False)
async def health():
    return {"status": "ok"}
