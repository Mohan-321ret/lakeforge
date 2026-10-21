"""Lakeforge FastAPI Backend

This module provides a REST API for the Lakeforge data inspection tool,
enabling web-based access to schema discovery, profiling, and Q&A features.
"""

import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

# Import route modules
from backend.routes import sources, inspection, dbeaver, qa

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# Lifespan context manager
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage app startup and shutdown."""
    logger.info("🚀 Lakeforge API starting...")
    yield
    logger.info("🛑 Lakeforge API shutting down...")


# Create FastAPI app
app = FastAPI(
    title="Lakeforge API",
    description="Data Engineer's Source Inspection & Insight Tool",
    version="0.2.0",
    lifespan=lifespan,
)

# Add CORS middleware for frontend access
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Global error handler
@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """Handle uncaught exceptions."""
    logger.error(f"Unhandled exception: {str(exc)}", exc_info=exc)
    return JSONResponse(
        status_code=500,
        content={"error": "Internal server error", "detail": str(exc)},
    )


# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "version": "0.2.0"}


# Include route modules
app.include_router(sources.router)
app.include_router(inspection.router)
app.include_router(qa.router)
app.include_router(dbeaver.router)

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
