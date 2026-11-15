"""Service for Q&A operations using LLM-generated SQL."""

import logging
import time
from typing import Dict, Any, Optional

from lakeforge.sources.registry import get_connector
from lakeforge.discover import discover_source
from lakeforge.llm.sql_gen import SQLGenerator
from lakeforge.validator import SQLValidator

logger = logging.getLogger(__name__)


class QAService:
    """Service for handling Q&A requests against data sources."""

    # Class-level storage for singleton pattern and sessions
    _instance = None
    _sessions: Dict[str, list] = {}

    def __init__(self):
        """Initialize QA service."""
        self.generator = None  # Lazy-load
        self.validator = SQLValidator()

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
                raise
        return self.generator

    def get_history(self, session_id: str) -> list:
        """Retrieve conversation history for a session."""
        return self._sessions.get(session_id, [])

    def _get_dialect(self, source_uri: str) -> str:
        """Extract database dialect from URI."""
        if "://" in source_uri:
            scheme = source_uri.split("://", 1)[0].lower()
            if "postgres" in scheme:
                return "postgres"
            if "sqlite" in scheme:
                return "sqlite"
            if "mysql" in scheme:
                return "mysql"
            if "oracle" in scheme:
                return "oracle"
            if "sqlserver" in scheme or "mssql" in scheme:
                return "tsql"
            if "databricks" in scheme:
                return "databricks"
            if "duckdb" in scheme:
                return "duckdb"
            return scheme
        return "sqlite"

    async def ask_question(
        self,
        source_uri: str,
        question: str,
        session_id: Optional[str] = None,
        timeout_seconds: int = 30,
        max_retries: int = 2,
    ) -> Dict[str, Any]:
        """
        Ask a natural language question about a data source with multi-turn
        context awareness and automated self-correction retry loop.

        Args:
            source_uri: Data source URI
            question: Natural language question
            session_id: Optional session identifier for conversation continuity
            timeout_seconds: Query timeout
            max_retries: Number of self-correction attempts on failure

        Returns:
            Dict with question, generated_sql, execution_status, results,
            error_message, execution_time_ms, session_id, attempts, self_corrected.
        """
        start_time = time.time()
        connector = None
        current_sql = None
        session_id = session_id or f"qa_sess_{int(time.time() * 1000)}"
        dialect = self._get_dialect(source_uri)
        attempts = 0
        max_attempts = 1 + max_retries
        corrections = []
        self_corrected = False

        try:
            generator = self._get_generator()
            
            logger.info(f"Getting connector for {source_uri}")
            connector = get_connector(source_uri)
            
            logger.info(f"Discovering schema for {source_uri}")
            catalog = discover_source(connector)
            schema_dict = self._catalog_to_schema_dict(catalog)
            
            # Fetch existing conversation history for multi-turn context
            history = self.get_history(session_id)
            
            # Initial SQL generation
            attempts += 1
            logger.info(f"Generating SQL (Attempt 1) for question: '{question}' with history depth {len(history)}")
            gen_result = generator.generate(
                question=question,
                schema=schema_dict,
                use_cache=True,
                history=history,
            )
            
            current_sql = gen_result.get("sql")
            if not current_sql or not gen_result.get("valid"):
                last_error = f"Could not generate initial valid SQL: {current_sql}"
                
                # Attempt self-correction if retries available
                if attempts < max_attempts and hasattr(generator, "correct"):
                    logger.info("Attempting self-correction on invalid initial generation...")
                    attempts += 1
                    corr_res = generator.correct(
                        question=question,
                        failed_sql=current_sql or "-- empty query",
                        error_message=last_error,
                        schema=schema_dict,
                        dialect=dialect,
                    )
                    current_sql = corr_res.get("sql")
                    if current_sql and corr_res.get("valid"):
                        self_corrected = True
                        corrections.append("Corrected initial invalid generation")
                    else:
                        return self._record_and_return(
                            session_id=session_id,
                            question=question,
                            generated_sql=current_sql,
                            status="error",
                            results=None,
                            error_msg=last_error,
                            exec_time=(time.time() - start_time) * 1000,
                            attempts=attempts,
                            self_corrected=False,
                            corrections=corrections,
                        )
                else:
                    return self._record_and_return(
                        session_id=session_id,
                        question=question,
                        generated_sql=current_sql,
                        status="error",
                        results=None,
                        error_msg=last_error,
                        exec_time=(time.time() - start_time) * 1000,
                        attempts=attempts,
                        self_corrected=False,
                        corrections=corrections,
                    )

            # Execution & Self-Correction Loop
            while attempts <= max_attempts:
                # Step 1: Validate SQL safety with SQLValidator
                val_error = None
                try:
                    val_res = self.validator.validate(current_sql)
                    if not val_res.get("valid", True):
                        val_error = ", ".join(val_res.get("errors", ["Query failed safety validation"]))
                except Exception as val_err:
                    logger.warning(f"SQLValidator notice (proceeding): {val_err}")

                if val_error:
                    logger.warning(f"SQLValidator rejected query: {val_error}")
                    # Destructive queries (DROP, DELETE, TRUNCATE) should fail immediately
                    if any(term in val_error.lower() for term in ["drop", "delete", "truncate", "alter"]):
                        return self._record_and_return(
                            session_id=session_id,
                            question=question,
                            generated_sql=current_sql,
                            status="error",
                            results=None,
                            error_msg=f"Safety validation failed: {val_error}",
                            exec_time=(time.time() - start_time) * 1000,
                            attempts=attempts,
                            self_corrected=self_corrected,
                            corrections=corrections,
                        )

                    # For other validator errors, attempt self-correction if retries remain
                    if attempts < max_attempts and hasattr(generator, "correct"):
                        attempts += 1
                        corrections.append(f"Validation error fixed: {val_error}")
                        logger.info(f"Self-correcting validation error (Attempt {attempts})...")
                        corr = generator.correct(
                            question=question,
                            failed_sql=current_sql,
                            error_message=val_error,
                            schema=schema_dict,
                            dialect=dialect,
                        )
                        current_sql = corr.get("sql")
                        self_corrected = True
                        continue
                    else:
                        return self._record_and_return(
                            session_id=session_id,
                            question=question,
                            generated_sql=current_sql,
                            status="error",
                            results=None,
                            error_msg=f"Safety validation failed: {val_error}",
                            exec_time=(time.time() - start_time) * 1000,
                            attempts=attempts,
                            self_corrected=self_corrected,
                            corrections=corrections,
                        )

                # Step 2: Execute query against connector
                logger.info(f"Executing SQL query on connector (Attempt {attempts}): {current_sql}")
                exec_start = time.time()
                try:
                    results = connector.query(current_sql, limit=1000)
                    exec_duration_ms = (time.time() - exec_start) * 1000
                    
                    return self._record_and_return(
                        session_id=session_id,
                        question=question,
                        generated_sql=current_sql,
                        status="success",
                        results=results or [],
                        error_msg=None,
                        exec_time=exec_duration_ms,
                        attempts=attempts,
                        self_corrected=self_corrected,
                        corrections=corrections,
                    )

                except Exception as exec_err:
                    exec_err_msg = str(exec_err)
                    logger.warning(f"Database execution failed on attempt {attempts}: {exec_err_msg}")
                    
                    if attempts < max_attempts and hasattr(generator, "correct"):
                        attempts += 1
                        corrections.append(f"Database error fixed: {exec_err_msg}")
                        logger.info(f"Triggering LLM self-correction for attempt {attempts}...")
                        corr = generator.correct(
                            question=question,
                            failed_sql=current_sql,
                            error_message=exec_err_msg,
                            schema=schema_dict,
                            dialect=dialect,
                        )
                        current_sql = corr.get("sql")
                        self_corrected = True
                        continue
                    else:
                        return self._record_and_return(
                            session_id=session_id,
                            question=question,
                            generated_sql=current_sql,
                            status="error",
                            results=None,
                            error_msg=f"Execution error: {exec_err_msg}",
                            exec_time=(time.time() - start_time) * 1000,
                            attempts=attempts,
                            self_corrected=self_corrected,
                            corrections=corrections,
                        )

        except Exception as e:
            logger.error(f"Q&A error: {str(e)}", exc_info=True)
            return self._record_and_return(
                session_id=session_id,
                question=question,
                generated_sql=current_sql,
                status="error",
                results=None,
                error_msg=str(e),
                exec_time=(time.time() - start_time) * 1000,
                attempts=attempts,
                self_corrected=self_corrected,
                corrections=corrections,
            )
        finally:
            if connector is not None:
                try:
                    connector.close()
                except Exception:
                    pass

    def _record_and_return(
        self,
        session_id: str,
        question: str,
        generated_sql: Optional[str],
        status: str,
        results: Optional[list],
        error_msg: Optional[str],
        exec_time: float,
        attempts: int,
        self_corrected: bool,
        corrections: list,
    ) -> Dict[str, Any]:
        """Record turn into session store and return structured response."""
        turn = {
            "question": question,
            "generated_sql": generated_sql,
            "execution_status": status,
            "results_count": len(results) if results else 0,
            "error_message": error_msg,
            "execution_time_ms": exec_time,
            "timestamp": time.time(),
            "self_corrected": self_corrected,
            "attempts": attempts,
            "corrections": corrections,
        }
        if session_id not in self._sessions:
            self._sessions[session_id] = []
        self._sessions[session_id].append(turn)

        return {
            "session_id": session_id,
            "question": question,
            "generated_sql": generated_sql,
            "execution_status": status,
            "results": results,
            "error_message": error_msg,
            "execution_time_ms": exec_time,
            "attempts": attempts,
            "self_corrected": self_corrected,
            "corrections": corrections,
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
