import logging
from fastapi import APIRouter, Depends, HTTPException, Request

from antigravity_tool.server.api_schemas import SyncAuthRequest, SyncRevertRequest
from antigravity_tool.schemas.sync import SyncStatus, RevisionHistory
from antigravity_tool.errors import ConflictError
from typing import List

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/sync", tags=["Sync"])

def get_cloud_sync_service(request: Request):
    """Dependency injection to get CloudSyncService."""
    # This assumes CloudSyncService will be added to app.state in lifespan
    sync_service = getattr(request.app.state, "cloud_sync_service", None)
    if not sync_service:
        raise HTTPException(status_code=503, detail="Cloud Sync Service is not available.")
    return sync_service

def get_uow_factory(request: Request):
    """Dependency injection to get a UnitOfWork factory for revert operations."""
    factory = getattr(request.app.state, "uow_factory", None)
    if not factory:
        raise HTTPException(status_code=503, detail="UnitOfWork factory is not available.")
    return factory

@router.get("/status")
async def get_sync_status(sync_service = Depends(get_cloud_sync_service)) -> dict:
    """Returns the current status of the cloud sync service."""
    return {"status": sync_service.status.value}

@router.get("/auth-url")
async def get_auth_url(sync_service = Depends(get_cloud_sync_service)):
    """Generates the Google OAuth authorization URL."""
    from google_auth_oauthlib.flow import Flow
    # Scopes required
    SCOPES = ['https://www.googleapis.com/auth/drive.file']
    redirect_uri = "http://localhost:3000/auth/callback"
    
    flow = Flow.from_client_secrets_file(
        sync_service.adapter.credentials_path,
        scopes=SCOPES,
        redirect_uri=redirect_uri
    )
    
    auth_url, _ = flow.authorization_url(
        access_type='offline',
        include_granted_scopes='true',
        prompt='consent'
    )
    return {"url": auth_url}

@router.post("/auth")
async def authenticate_sync(request: SyncAuthRequest, sync_service = Depends(get_cloud_sync_service)):
    """Handles OAuth2 code exchange for Google Drive."""
    # The frontend is running at localhost:3000/auth/callback
    redirect_uri = "http://localhost:3000/auth/callback"
    success = await sync_service.adapter.exchange_auth_code(request.auth_code, redirect_uri)
    
    if success:
        # Update the sync service status now that it has credentials
        sync_service.status = SyncStatus.IDLE
        return {"success": True, "message": "Successfully authenticated with Google Drive."}
    else:
        raise HTTPException(status_code=400, detail="Failed to exchange authorization code.")

@router.post("/disconnect")
async def disconnect_sync(sync_service = Depends(get_cloud_sync_service)):
    """Disconnects Google Drive: revokes tokens, stops worker, resets status."""
    try:
        sync_service.disconnect()
        return {"success": True, "message": "Google Drive disconnected successfully."}
    except Exception as e:
        logger.error(f"Error disconnecting: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to disconnect: {e}")

@router.get("/revisions")
async def get_revisions(yaml_path: str, sync_service = Depends(get_cloud_sync_service)) -> List[RevisionHistory]:
    """Returns revision history for a specific YAML file."""
    try:
        drive_file_id = sync_service._drive_id_map.get(yaml_path)
        if not drive_file_id:
            logger.warning(f"No Drive file tracked for {yaml_path}")
            return []

        revisions = await sync_service.adapter.list_revisions(drive_file_id)
        return revisions
    except Exception as e:
        logger.error(f"Error listing revisions for {yaml_path}: {e}")
        raise HTTPException(status_code=500, detail="Failed to list revisions from Google Drive.")

@router.post("/revert")
async def revert_file(
    request: SyncRevertRequest,
    sync_service = Depends(get_cloud_sync_service),
    uow_factory = Depends(get_uow_factory),
):
    """Reverts a file to a specific Drive revision via UnitOfWork."""
    try:
        content = await sync_service.revert_file(
            request.yaml_path,
            request.revision_id,
            uow_factory=uow_factory,
        )
        return {"success": True, "message": f"Successfully reverted {request.yaml_path}"}
    except ConflictError as e:
        raise HTTPException(
            status_code=409,
            detail={
                "error": "conflict",
                "message": str(e),
                "entity_id": e.entity_id,
                "expected_hash": e.expected_hash,
                "actual_hash": e.actual_hash,
            },
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Error reverting {request.yaml_path}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to revert file: {e}")
