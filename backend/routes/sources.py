"""API routes for source management."""

from typing import List
from fastapi import APIRouter, HTTPException, status
from backend.models import SourceCreate, SourceResponse
from backend.services.source_service import SourceService

router = APIRouter(prefix="/api/sources", tags=["sources"])
service = SourceService()


@router.post("", response_model=SourceResponse, status_code=status.HTTP_201_CREATED)
async def create_source(source: SourceCreate) -> SourceResponse:
    """Create a new data source connection.

    Args:
        source: Source connection details

    Returns:
        Created source with ID
    """
    try:
        result = await service.create_source(source)
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("", response_model=List[SourceResponse])
async def list_sources() -> List[SourceResponse]:
    """List all saved data sources.

    Returns:
        List of sources
    """
    try:
        sources = await service.list_sources()
        return sources
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{source_id}", response_model=SourceResponse)
async def get_source(source_id: str) -> SourceResponse:
    """Get details of a specific source.

    Args:
        source_id: ID of the source

    Returns:
        Source details
    """
    try:
        source = await service.get_source(source_id)
        if not source:
            raise HTTPException(status_code=404, detail="Source not found")
        return source
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{source_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_source(source_id: str) -> None:
    """Delete a data source.

    Args:
        source_id: ID of the source to delete
    """
    try:
        success = await service.delete_source(source_id)
        if not success:
            raise HTTPException(status_code=404, detail="Source not found")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{source_id}/test", status_code=status.HTTP_200_OK)
async def test_connection(source_id: str) -> dict:
    """Test a data source connection.

    Args:
        source_id: ID of the source to test

    Returns:
        Test result with status
    """
    try:
        result = await service.test_connection(source_id)
        return result
    except Exception as e:
        return {"status": "error", "message": str(e)}
