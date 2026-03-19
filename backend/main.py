from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

app = FastAPI(title="Gemini Drone Commander", version="0.1.0")

FRONTEND_DIR = Path(__file__).resolve().parent.parent / "frontend" / "dist"


@app.get("/api/health")
async def health() -> dict:
    return {"status": "ok", "version": app.version}


# Serve frontend static files if the build directory exists.
# In development the React dev server is used instead.
if FRONTEND_DIR.is_dir():
    app.mount("/assets", StaticFiles(directory=FRONTEND_DIR / "assets"), name="assets")

    @app.get("/{full_path:path}")
    async def serve_spa(full_path: str) -> FileResponse:
        file = FRONTEND_DIR / full_path
        if file.is_file():
            return FileResponse(file)
        return FileResponse(FRONTEND_DIR / "index.html")
