"""Service for data inspection."""

import logging
from typing import Optional, Dict, Any
from backend.models import InspectionRequest
from backend.services.source_service import SourceService
from lakeforge.sources.registry import get_connector
from lakeforge.discover import discover_source, profile_source

logger = logging.getLogger(__name__)


class InspectionService:
    """Service for data inspection."""

    def __init__(self):
        """Initialize inspection service."""
        # Store sessions in memory (in production: use database)
        self.sessions = {}
        self.counter = 0
        self.source_service = SourceService()

    async def start_inspection(self, request: InspectionRequest) -> str:
        """Start an inspection session.

        Args:
            request: Inspection request

        Returns:
            Session ID
        """
        session_id = f"sess_{self.counter}"
        self.counter += 1

        # Initialize session
        self.sessions[session_id] = {
            "source_id": request.source_id,
            "status": "in_progress",
            "schema": None,
            "profile": None,
            "samples": None,
        }

        try:
            # Get source from source service
            source = await self.source_service.get_source(request.source_id)
            if not source:
                raise ValueError(f"Source {request.source_id} not found")
            
            # Get connector using source URI
            connector = get_connector(source.uri)
            # Ensure connector exposes a `.source` attribute for discover/profile
            if not hasattr(connector, "source"):
                connector.source = source.uri
            connector.connect()
            logger.info(f"Connected to {request.source_id}: {source.source_type}")

            # Discover schema
            catalog = discover_source(connector)
            self.sessions[session_id]["schema"] = catalog.to_dict()
            logger.info(f"Discovered schema with {len(catalog.tables)} tables")

            # Profile if requested
            if request.include_profile:
                profile = profile_source(connector, catalog, max_rows=request.sample_size or 1000)
                self.sessions[session_id]["profile"] = profile.to_dict() if hasattr(profile, "to_dict") else str(profile)
                logger.info(f"Generated profile")

            # Collect sample rows for tables
            from lakeforge.profile import Sampler
            sampler = Sampler(max_rows=min(request.sample_size or 50, 50))
            samples_dict = {}
            for table_name in catalog.tables.keys():
                try:
                    samples_dict[table_name] = sampler.sample_from_connector(connector, table_name)
                except Exception as s_err:
                    logger.warning(f"Sample collection failed for {table_name}: {s_err}")
                    samples_dict[table_name] = []
            self.sessions[session_id]["samples"] = samples_dict

            self.sessions[session_id]["status"] = "completed"
            logger.info(f"Inspection {session_id} completed")

        except Exception as e:
            logger.error(f"Inspection failed: {str(e)}")
            self.sessions[session_id]["status"] = "error"
            self.sessions[session_id]["error"] = str(e)
        finally:
            if connector is not None:
                try:
                    connector.close()
                except Exception:
                    pass

        return session_id

    async def get_status(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get inspection status.

        Args:
            session_id: Session ID

        Returns:
            Status dict or None
        """
        session = self.sessions.get(session_id)
        if not session:
            return None
        return {"session_id": session_id, "status": session["status"]}

    async def get_schema(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get discovered schema.

        Args:
            session_id: Session ID

        Returns:
            Schema dict or None
        """
        session = self.sessions.get(session_id)
        if not session:
            logger.warning(f"Session {session_id} not found")
            return None
        if session["status"] != "completed":
            logger.info(f"Session {session_id} status: {session['status']}")
        if not session["schema"]:
            logger.warning(f"No schema in session {session_id}")
            return None
        logger.debug(f"Returning schema for {session_id}: {len(session['schema'])} tables")
        return {"schema": session["schema"]}

    async def get_profile(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get profile data.

        Args:
            session_id: Session ID

        Returns:
            Profile dict or None
        """
        session = self.sessions.get(session_id)
        if not session:
            logger.warning(f"Session {session_id} not found")
            return None
        if session["status"] != "completed":
            logger.info(f"Session {session_id} status: {session['status']}")
        if not session["profile"]:
            logger.warning(f"No profile in session {session_id}")
            return None
        logger.debug(f"Returning profile for {session_id}: {len(session['profile'])} tables")
        return {"profile": session["profile"]}

    async def get_samples(self, session_id: str, limit: int) -> Optional[Dict[str, Any]]:
        """Get sample rows.

        Args:
            session_id: Session ID
            limit: Max rows

        Returns:
            Samples dict or None
        """
        session = self.sessions.get(session_id)
        if not session:
            return None
        return {"samples": session.get("samples", [])}
