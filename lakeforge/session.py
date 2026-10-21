"""Session management for Q&A interactions.

Maintains state across multiple questions in REPL mode.
"""

import json
from datetime import datetime
from pathlib import Path
from typing import Any, Optional

from lakeforge.config import get_config
from lakeforge.discover import discover_source
from lakeforge.executor import DuckDBExecutor, AuditLogger
from lakeforge.llm import get_llm
from lakeforge.llm.router import QuestionRouter
from lakeforge.llm.sql_gen import SQLGenerator
from lakeforge.sources.registry import get_connector
from lakeforge.validator import SQLValidator


class QASession:
    """Manages Q&A session state and execution.

    Maintains:
    - Catalog (schema info)
    - Cards (retrieved context)
    - Query cache
    - Conversation history
    - Audit log
    """

    def __init__(
        self,
        source: str,
        output_dir: Optional[Path] = None,
        verbose: bool = False,
        profile: bool = False,
    ):
        """Initialize Q&A session.

        Args:
            source: Data source URI (file path, S3, etc.)
            output_dir: Directory for logs and outputs
            verbose: Enable verbose logging
            profile: Include profiling stats
        """
        self.source = source
        self.verbose = verbose
        self.profile = profile
        self.config = get_config()

        # Initialize output directory
        self.output_dir = Path(output_dir) if output_dir else self.config.output_dir
        self.output_dir.mkdir(parents=True, exist_ok=True)

        # Session files
        self.session_id = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.qa_log_file = self.output_dir / f"qa_log_{self.session_id}.jsonl"
        self.audit_log_file = self.output_dir / f"audit_{self.session_id}.jsonl"

        # Initialize components
        self.connector = None
        self.catalog = None
        self.executor = None
        self.validator = None
        self.router = None
        self.sql_generator = None
        self.audit_logger = None
        self.llm = None

        # Conversation history (for context)
        self.history = []  # List of {"question": str, "sql": str, "answer": str}
        self.query_cache = {}  # Cache SQL generation results

        self._initialize()

    def _initialize(self):
        """Initialize session components."""
        if self.verbose:
            print(f"[*] Initializing session for {self.source}")

        try:
            # Get connector
            self.connector = get_connector(self.source)

            # Discover schema
            self.catalog = discover_source(self.connector, verbose=self.verbose)

            # Initialize executor and validator
            self.executor = DuckDBExecutor(
                database=":memory:",
                max_result_rows=self.config.max_sample_rows,
            )
            self.validator = SQLValidator(max_result_bytes=self.config.max_result_bytes)

            # Initialize LLM components
            self.llm = get_llm(self.config.llm_provider)
            self.router = QuestionRouter(llm=self.llm)
            self.sql_generator = SQLGenerator(llm=self.llm, router=self.router)

            # Initialize audit logger
            self.audit_logger = AuditLogger(log_file=str(self.audit_log_file))

            if self.verbose:
                table_count = len(self.catalog.tables) if hasattr(self.catalog, 'tables') else len(self.catalog) if isinstance(self.catalog, dict) else 0
                print(f"[✓] Session initialized with {table_count} tables")
        except Exception as e:
            if self.verbose:
                print(f"[!] Initialization error: {e}")
            raise

    def ask(self, question: str) -> dict:
        """Ask a question and get answer.

        Args:
            question: Natural language question

        Returns:
            Dict with keys:
            - query_type: DESCRIBE|AGGREGATE|FILTER|JOIN|CUSTOM
            - sql: Generated SQL (or None if error)
            - valid: Whether SQL is valid
            - result: ExecutionResult
            - answer: Summarized answer (or error message)
            - error: Error message if any
        """
        response = {
            "question": question,
            "query_type": None,
            "sql": None,
            "valid": False,
            "result": None,
            "answer": None,
            "error": None,
        }

        try:
            # Step 1: Classify question
            if self.verbose:
                print("[*] Classifying question...")

            query_type = self.router.classify(question)
            response["query_type"] = query_type

            # Step 2: Generate SQL
            if self.verbose:
                print("[*] Generating SQL...")

            # Format schema for prompt
            schema_str = self._format_schema()
            sql_response = self.sql_generator.generate(
                question=question,
                schema=self._schema_dict(),
                use_cache=True,
            )

            response["sql"] = sql_response.get("sql")
            response["valid"] = sql_response.get("valid", False)

            if not response["sql"]:
                response["error"] = "Failed to generate SQL"
                response["answer"] = f"[Error] Could not generate SQL for: {question}"
                self._log_qa(response)
                return response

            # Step 3: Validate SQL
            if self.verbose:
                print("[*] Validating SQL...")

            validation = self.validator.validate(response["sql"])
            if not validation["valid"]:
                response["error"] = f"SQL validation failed: {validation['errors']}"
                response["answer"] = f"[Error] Invalid SQL: {validation['errors'][0]}"
                self._log_qa(response)
                return response

            # Step 4: Execute SQL
            if self.verbose:
                print("[*] Executing SQL...")

            result = self.executor.execute(
                response["sql"],
                timeout_sec=self.config.max_query_timeout_sec,
            )
            response["result"] = result

            # Log to audit trail
            self.audit_logger.log_execution(
                response["sql"],
                result,
                provider="duckdb",
                model=None,
                cost=0.0,
            )

            # Step 5: Format answer
            from lakeforge.executor import ExecutionStatus
            
            if result.status == ExecutionStatus.SUCCESS:
                # For now, return raw data; Phase 10.4 adds summarization
                answer_lines = [f"[Result] {result.rows} rows returned"]
                if result.warning:
                    answer_lines.append(f"[Warning] {result.warning}")
                if result.columns and result.data:
                    answer_lines.append("\nColumns: " + ", ".join(result.columns))
                    if len(result.data) <= 5:
                        # Show small results
                        for row in result.data:
                            answer_lines.append(str(row))
                    else:
                        # Show first 3 rows for large results
                        for row in result.data[:3]:
                            answer_lines.append(str(row))
                        answer_lines.append(f"... ({result.total_rows or result.rows} total rows)")
                response["answer"] = "\n".join(answer_lines)
            else:
                response["error"] = result.error_message
                response["answer"] = f"[Error] {result.error_message}"

            # Add to history
            self.history.append({
                "question": question,
                "query_type": query_type,
                "sql": response["sql"],
                "answer": response["answer"],
            })

            self._log_qa(response)
            return response

        except Exception as e:
            response["error"] = str(e)
            response["answer"] = f"[Error] {str(e)}"
            if self.verbose:
                print(f"[!] Error: {e}")
            self._log_qa(response)
            return response

    def _schema_dict(self) -> dict:
        """Convert catalog to schema dict for SQL generator."""
        schema = {}
        if self.catalog is None:
            return schema
        
        # Handle Catalog object with .tables attribute
        tables_dict = self.catalog.tables if hasattr(self.catalog, 'tables') else {}
        
        for table_name, table_info in tables_dict.items():
            # TableMetadata object has columns attribute
            columns = []
            if hasattr(table_info, '__dict__'):
                columns = table_info.__dict__.get('columns', {})
            elif isinstance(table_info, dict):
                columns = table_info.get('columns', {})
            
            schema[table_name] = {
                "columns": list(columns.keys()) if isinstance(columns, dict) else [c['name'] for c in columns],
            }
        return schema

    def _format_schema(self) -> str:
        """Format schema for display."""
        lines = []
        if self.catalog is None:
            return ""
        
        # Handle Catalog object with .tables attribute
        tables_dict = self.catalog.tables if hasattr(self.catalog, 'tables') else {}
        
        for table_name, table_info in tables_dict.items():
            lines.append(f"{table_name}:")
            
            # TableMetadata object has columns attribute
            columns = []
            if hasattr(table_info, '__dict__'):
                columns = table_info.__dict__.get('columns', {})
            elif isinstance(table_info, dict):
                columns = table_info.get('columns', {})
            
            if isinstance(columns, dict):
                for col_name, col_info in columns.items():
                    col_type = col_info.get('type', 'unknown') if isinstance(col_info, dict) else 'unknown'
                    lines.append(f"  - {col_name}: {col_type}")
            else:
                for col in columns:
                    col_name = col.get("name", "unknown") if isinstance(col, dict) else "unknown"
                    col_type = col.get("type", "unknown") if isinstance(col, dict) else "unknown"
                    lines.append(f"  - {col_name}: {col_type}")
        return "\n".join(lines)

    def _log_qa(self, response: dict) -> None:
        """Log Q&A pair to JSONL file.

        Args:
            response: Q&A response dict
        """
        try:
            log_entry = {
                "timestamp": datetime.now().isoformat(),
                "question": response.get("question"),
                "query_type": response.get("query_type"),
                "sql": response.get("sql"),
                "valid": response.get("valid"),
                "error": response.get("error"),
                "rows": response.get("result", {}).get("rows") if response.get("result") else None,
            }
            with open(self.qa_log_file, "a") as f:
                f.write(json.dumps(log_entry) + "\n")
        except Exception as e:
            if self.verbose:
                print(f"[!] Error logging QA: {e}")
            # Still silently fail on logging errors to not interrupt user flow

    def close(self) -> None:
        """Close session resources."""
        if self.executor:
            self.executor.close()
        if self.connector:
            self.connector.close()

    def get_summary(self) -> dict:
        """Get session summary.

        Returns:
            Dict with session stats and history
        """
        table_count = 0
        if self.catalog is not None:
            if hasattr(self.catalog, 'tables'):
                table_count = len(self.catalog.tables)
            elif isinstance(self.catalog, dict):
                table_count = len(self.catalog)
        
        return {
            "session_id": self.session_id,
            "source": self.source,
            "tables": table_count,
            "questions_asked": len(self.history),
            "audit_log": str(self.audit_log_file),
            "qa_log": str(self.qa_log_file),
            "history": self.history,
        }
