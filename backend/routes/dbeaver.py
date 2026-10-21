"""API routes for DBeaver integration."""

import logging
from fastapi import APIRouter, HTTPException, status
from lakeforge.sources.dbeaver_importer import DBeaverProfileImporter

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/dbeaver", tags=["dbeaver"])


@router.get("/connections")
async def get_dbeaver_connections():
    """List all saved DBeaver connections.

    Returns:
        List of available DBeaver connections with connection details
    """
    try:
        connections = DBeaverProfileImporter.list_connections()
        logger.info(f"Found {len(connections)} DBeaver connections")
        
        if not connections:
            logger.warning("No DBeaver connections found")
            return {
                'error': 'No DBeaver connections found. Please save a connection in DBeaver first.',
                'connections': []
            }
        
        # Format for frontend
        result = []
        for conn_id, conn_info in connections.items():
            result.append({
                'id': conn_id,
                'name': conn_info.get('name', conn_id),
                'driver': conn_info.get('driver', 'Unknown'),
                'host': conn_info.get('host', ''),
                'database': conn_info.get('database', ''),
            })
        
        return result
    except Exception as e:
        logger.error(f"Failed to load DBeaver connections: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to load DBeaver connections: {str(e)}"
        )


@router.post("/connections/{connection_id}")
async def import_dbeaver_connection(connection_id: str):
    """Import a DBeaver connection and return the URI.

    Args:
        connection_id: ID of the DBeaver connection to import

    Returns:
        Connection details including URI and driver type
    """
    try:
        logger.info(f"Importing DBeaver connection: {connection_id}")
        
        # First verify connection exists
        all_connections = DBeaverProfileImporter.list_connections()
        if connection_id not in all_connections:
            logger.warning(f"Connection not found: {connection_id}")
            available = list(all_connections.keys())
            raise ValueError(f"Connection '{connection_id}' not found. Available connections: {available}")
        
        imported = DBeaverProfileImporter.import_connection(connection_id)
        logger.info(f"Successfully imported connection: {imported.get('name')}")
        
        return {
            'name': imported.get('name', connection_id),
            'uri': imported.get('uri', ''),
            'driver': imported.get('driver', ''),
            'host': imported.get('host', ''),
            'database': imported.get('database', ''),
        }
    except ValueError as e:
        logger.error(f"Validation error: {str(e)}")
        raise HTTPException(
            status_code=400,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Failed to import connection: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to import connection: {str(e)}"
        )
