"""API routes for data inspection."""

from fastapi import APIRouter, HTTPException, status
from backend.models import InspectionRequest, SchemaInfo
from backend.services.inspection_service import InspectionService

router = APIRouter(prefix="/api/inspect", tags=["inspection"])
service = InspectionService()


@router.post("/start")
async def start_inspection(request: InspectionRequest) -> dict:
    """Start an inspection session.

    Args:
        request: Inspection parameters

    Returns:
        Session ID for tracking progress
    """
    try:
        session_id = await service.start_inspection(request)
        return {"session_id": session_id, "status": "started"}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{session_id}/status")
async def get_inspection_status(session_id: str) -> dict:
    """Get inspection status.

    Args:
        session_id: Session ID

    Returns:
        Current status and progress
    """
    try:
        status = await service.get_status(session_id)
        if not status:
            raise HTTPException(status_code=404, detail="Session not found")
        return status
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{session_id}/schema")
async def get_schema(session_id: str) -> dict:
    """Get discovered schema.

    Args:
        session_id: Session ID

    Returns:
        Schema information
    """
    try:
        schema = await service.get_schema(session_id)
        if not schema:
            raise HTTPException(status_code=404, detail="Session not found or no schema available")
        return schema
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{session_id}/profile")
async def get_profile(session_id: str) -> dict:
    """Get data profile with statistics.

    Args:
        session_id: Session ID

    Returns:
        Profile statistics
    """
    try:
        profile = await service.get_profile(session_id)
        if not profile:
            raise HTTPException(status_code=404, detail="Session not found or no profile available")
        return profile
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{session_id}/samples")
async def get_samples(session_id: str, limit: int = 100) -> dict:
    """Get sample rows.

    Args:
        session_id: Session ID
        limit: Maximum rows to return

    Returns:
        Sample data
    """
    try:
        samples = await service.get_samples(session_id, limit)
        if not samples:
            raise HTTPException(status_code=404, detail="Session not found")
        return samples
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
