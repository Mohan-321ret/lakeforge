"""Service for Q&A operations using LLM-generated SQL."""

import logging
import time
from typing import Dict, Any, Optional

from lakeforge.sources.registry import get_connector
from lakeforge.discover import discover_source
from lakeforge.llm.sql_gen import SQLGenerator
from lakeforge.executor.duckdb_ import DuckDBExecutor

logger = logging.getLogger(__name__)


class QAService:
    """Service for handling Q&A requests against data sources."""

    # Class-level storage for singleton pattern
    _instance = None

    def __init__(self):
        """Initialize QA service."""
        self.generator = None  # Lazy-load
        self.executor = DuckDBExecutor(database=":memory:", max_result_rows=10000)

    def __new__(cls):
        """Implement singleton pattern."""
        if cls._instance is None:
            cls._instance = super(QAService, cls).__new__(cls)
        return cls._instance

    def _get_generator(self) -> SQLGenerator:
        """Lazy-load SQLGenerator to avoid Groq API key issues at import time."""
        if self.generator is None:
            try:
                self.generator = SQLGenerator()
            except ValueError as e:
                # If Groq API key is not available, log but don't fail
                logger.warning(f"SQLGenerator initialization issue: {e}")
                # Will fail at query time if needed
                raise
        return self.generator

    async def ask_question(
        self,
        source_uri: str,
        question: str,
        timeout_seconds: int = 30,
    ) -> Dict[str, Any]:
        """
        Ask a natural language question about a data source.

        Args:
            source_uri: Data source URI
            question: Natural language question
            timeout_seconds: Query timeout

        Returns:
            Dict with:
                - question: Original question
                - generated_sql: Generated SQL (or None if error)
                - execution_status: "success" or "error"
                - results: Query results (list of dicts) or None
                - error_message: Error message if any
                - execution_time_ms: Query execution time
        """
        start_time = time.time()
        
        try:
            # Get generator (lazy-load)
            generator = self._get_generator()
            
            # Get connector
            logger.info(f"Getting connector for {source_uri}")
            connector = get_connector(source_uri)
            
            # Discover schema
            logger.info(f"Discovering schema for {source_uri}")
            catalog = discover_source(connector)
            
            # Convert catalog to schema dict for SQL generator
            schema_dict = self._catalog_to_schema_dict(catalog)
            
            # Generate SQL
            logger.info(f"Generating SQL for question: {question}")
            gen_result = generator.generate(
                question=question,
                schema=schema_dict,
                use_cache=True,
            )
            
            generated_sql = gen_result.get("sql")
            
            if not gen_result.get("valid"):
                return {
                    "question": question,
                    "generated_sql": generated_sql,
                    "execution_status": "error",
                    "results": None,
                    "error_message": f"Invalid SQL generated: {generated_sql}",
                    "execution_time_ms": (time.time() - start_time) * 1000,
                }
            
            logger.info(f"Generated SQL: {generated_sql}")
            
            # Execute SQL
            logger.info(f"Executing SQL with {timeout_seconds}s timeout")
            exec_result = self.executor.execute(generated_sql, timeout_sec=timeout_seconds)
            
            # Check execution status
            if exec_result.status.value != "success":
                return {
                    "question": question,
                    "generated_sql": generated_sql,
                    "execution_status": "error",
                    "results": None,
                    "error_message": exec_result.error_message or "Unknown execution error",
                    "execution_time_ms": (time.time() - start_time) * 1000,
                }
            
            # Return successful result
            return {
                "question": question,
                "generated_sql": generated_sql,
                "execution_status": "success",
                "results": exec_result.data or [],
                "error_message": None,
                "execution_time_ms": exec_result.duration_ms,
            }

        except Exception as e:
            logger.error(f"Q&A error: {str(e)}", exc_info=True)
            return {
                "question": question,
                "generated_sql": None,
                "execution_status": "error",
                "results": None,
                "error_message": str(e),
                "execution_time_ms": (time.time() - start_time) * 1000,
            }

    def _catalog_to_schema_dict(self, catalog: Any) -> Dict[str, list]:
        """Convert catalog object to schema dict for SQL generator.
        
        Args:
            catalog: Catalog object or dict from discovery
            
        Returns:
            Dict mapping table_name -> list of column dicts
        """
        if isinstance(catalog, dict):
            # Already a dict
            result = {}
            for table_name, table_info in catalog.items():
                if isinstance(table_info, dict) and "columns" in table_info:
                    result[table_name] = table_info["columns"]
                elif isinstance(table_info, list):
                    result[table_name] = table_info
                else:
                    result[table_name] = []
            return result
        
        # If it's an object with tables attribute
        if hasattr(catalog, "tables"):
            result = {}
            for table in catalog.tables:
                table_name = table.get("name") if isinstance(table, dict) else getattr(table, "name", "unknown")
                columns = table.get("columns") if isinstance(table, dict) else getattr(table, "columns", [])
                result[table_name] = columns
            return result
        
        # Fallback
        return {}
