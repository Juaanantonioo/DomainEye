from pathlib import Path
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel

# ---------- Paths ----------

BASE_DIR = Path(__file__).resolve().parent          # project/
WEB_DIR = BASE_DIR / "web"                          # project/web
INDEX_FILE = WEB_DIR / "index.html"                 # project/web/index.html

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


# ---------- Your Python logic ----------

def run_python_logic(domain: str) -> DomainResponse:
    """
    Replace this with your real logic:
    - call your LLM
    - do DNS / WHOIS lookups
    - run brand protection checks
    - whatever you need.
    """
    is_likely_valid = "." in domain and " " not in domain

    if not is_likely_valid:
        return DomainResponse(
            domain=domain,
            status="error",
            detail="The provided string does not look like a valid domain.",
        )

    return DomainResponse(
        domain=domain,
        status="ok",
        detail=f"Python backend processed domain '{domain}'. Plug your real logic here.",
    )


# ---------- API Routes ----------

@app.post("/api/query", response_model=DomainResponse)
async def query_domain(payload: DomainRequest):
    """
    Endpoint called from the frontend.
    """
    result = run_python_logic(payload.domain)
    print(result)
    return result


# Optional healthcheck
@app.get("/health", include_in_schema=False)
async def health():
    return {"status": "ok"}
