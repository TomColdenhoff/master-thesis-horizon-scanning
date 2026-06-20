"""FastAPI application — human review UI backend (task 29)."""

from fastapi import FastAPI
from fastapi.responses import HTMLResponse, Response

from api.routers import documents, signals, viewer
from ui.review import html as review_html

app = FastAPI(title="Horizon Scanning — Signal Review")
app.include_router(signals.router)
app.include_router(documents.router)
app.include_router(viewer.router)


@app.get("/", response_class=HTMLResponse, include_in_schema=False)
def review_ui() -> str:
    """Serve the signal review UI."""
    return review_html()


@app.get("/favicon.ico", include_in_schema=False)
def favicon() -> Response:
    return Response(status_code=204)
