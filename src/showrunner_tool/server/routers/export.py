"""Export router — File download endpoints for manuscript, bundle, and screenplay."""

from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse, Response

from showrunner_tool.services.export_service import ExportService
from showrunner_tool.server.deps import get_export_service

router = APIRouter(prefix="/api/v1/export", tags=["export"])


@router.post("/manuscript")
async def export_manuscript(
    svc: ExportService = Depends(get_export_service),
):
    """Export the full manuscript as a Markdown file download."""
    content = svc.export_markdown()
    return Response(
        content=content,
        media_type="text/markdown",
        headers={
            "Content-Disposition": 'attachment; filename="manuscript.md"',
        },
    )


@router.post("/bundle")
async def export_bundle(
    svc: ExportService = Depends(get_export_service),
):
    """Export the full project state as a JSON bundle."""
    bundle = svc.export_json_bundle()
    return JSONResponse(content=bundle)


@router.post("/screenplay")
async def export_screenplay(
    svc: ExportService = Depends(get_export_service),
):
    """Export the manuscript in Fountain screenplay format."""
    content = svc.export_fountain()
    return Response(
        content=content,
        media_type="text/plain",
        headers={
            "Content-Disposition": 'attachment; filename="screenplay.fountain"',
        },
    )


@router.post("/html")
async def export_html(
    svc: ExportService = Depends(get_export_service),
):
    """Export the manuscript as a styled HTML document (print to PDF from browser)."""
    content = svc.export_html()
    return Response(
        content=content,
        media_type="text/html",
        headers={
            "Content-Disposition": 'attachment; filename="manuscript.html"',
        },
    )


@router.post("/preview")
async def export_preview(
    svc: ExportService = Depends(get_export_service),
):
    """Return styled HTML manuscript for inline preview (no download header)."""
    content = svc.export_html()
    return Response(content=content, media_type="text/html")
