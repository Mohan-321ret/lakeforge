"""API routes for Q&A operations."""

from fastapi import APIRouter, HTTPException
from backend.models import QARequest, QAResponse
from backend.services.qa_service import QAService
from backend.services.source_service import SourceService

router = APIRouter(prefix="/api/qa", tags=["qa"])

# Lazy-load services to avoid import-time issues
def get_qa_service():
    """Get QA service instance."""
    return QAService()

def get_source_service():
    """Get source service instance."""
    return SourceService()


@router.post("", response_model=QAResponse)
async def ask_question(request: QARequest) -> QAResponse:
    """Ask a natural language question about a data source.

    Args:
        request: Q&A request with source_id and question

    Returns:
        QAResponse with generated SQL, results, and metadata
    """
    try:
        qa_service = get_qa_service()
        source_service = get_source_service()
        
        # Get source to retrieve URI
        source = await source_service.get_source(request.source_id)
        if not source:
            raise HTTPException(status_code=404, detail="Source not found")

        # Ask question
        result = await qa_service.ask_question(
            source_uri=source.uri,
            question=request.question,
            session_id=request.session_id,
            timeout_seconds=30,
        )

        # Convert result to response model
        return QAResponse(
            question=result["question"],
            generated_sql=result.get("generated_sql"),
            execution_status=result.get("execution_status", "error"),
            results=result.get("results"),
            error_message=result.get("error_message"),
            execution_time_ms=result.get("execution_time_ms", 0),
            session_id=result.get("session_id"),
            attempts=result.get("attempts", 1),
            self_corrected=result.get("self_corrected", False),
            corrections=result.get("corrections", []),
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{session_id}/history")
async def get_qa_history(session_id: str) -> dict:
    """Get Q&A history for a session.

    Args:
        session_id: Session ID

    Returns:
        List of previous Q&A exchanges in this session
    """
    qa_service = get_qa_service()
    history = qa_service.get_history(session_id)
    return {
        "session_id": session_id,
        "history": history,
        "turns_count": len(history),
    }
