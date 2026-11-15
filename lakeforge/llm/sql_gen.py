"""SQL generator - converts natural language to SQL."""

import re
from pathlib import Path
from lakeforge.llm import BaseLLM, get_llm
from lakeforge.llm.router import QuestionRouter, QueryType
from lakeforge.prompts.examples import format_examples_for_prompt


class SQLGenerator:
    """Generate SQL queries from natural language questions."""
    
    def __init__(self, llm: BaseLLM | None = None, router: QuestionRouter | None = None):
        """
        Initialize SQL generator.
        
        Args:
            llm: LLM client (default: Groq)
            router: Question router (default: new instance)
        """
        self.llm = llm or get_llm(provider="groq")
        self.router = router or QuestionRouter(llm)
        self.templates_dir = Path(__file__).parent.parent / "prompts"
    
    def generate(
        self,
        question: str,
        schema: dict,
        glossary: list[dict] | None = None,
        use_cache: bool = True,
        history: list[dict] | None = None,
    ) -> dict:
        """
        Generate SQL for a question.
        
        Args:
            question: Natural language question
            schema: Database schema dict (table_name → [columns])
            glossary: Optional list of glossary terms with definitions
            use_cache: Whether to use prompt cache
            history: Optional previous exchanges in multi-turn conversation
            
        Returns:
            Dict with keys:
                - sql: Generated SQL string (or refusal message)
                - valid: Whether SQL is valid (basic check)
                - query_type: Classified query type
                - explanation: Why SQL was generated this way
        """
        # Classify question
        query_type = self.router.classify(question)
        
        # Load SQL generation template
        sql_template_path = self.templates_dir / "sql.j2"
        sql_template = sql_template_path.read_text()
        
        # Build context
        glossary = glossary or []
        
        # Simple Jinja2 rendering
        prompt = sql_template.replace("{{ question }}", question)
        
        # Prepend conversation history if provided
        if history:
            hist_lines = ["\n**Previous Conversation Context:**"]
            for turn in history[-3:]:
                q = turn.get("question", "")
                s = turn.get("generated_sql", "")
                if q and s:
                    hist_lines.append(f"User asked: {q}")
                    hist_lines.append(f"Generated SQL: {s}")
            if len(hist_lines) > 1:
                hist_text = "\n".join(hist_lines) + "\n\n"
                prompt = prompt.replace("**Question:**", f"{hist_text}**Question:**")

        # Replace schema
        schema_text = self._format_schema(schema)
        prompt = prompt.replace("{% for table_name, columns in schema.items() %}", "")
        prompt = prompt.replace("Table: {{ table_name }}", "")
        prompt = prompt.replace("{% for col in columns %}", "")
        prompt = prompt.replace("  - {{ col.name }} ({{ col.type }}){% if col.nullable %} [nullable]{% endif %}{% if col.description %} -- {{ col.description }}{% endif %}", "")
        prompt = prompt.replace("{% endfor %}", "")
        
        # Insert formatted schema
        prompt = prompt.replace("**Database Schema:**", f"**Database Schema:**\n{schema_text}")
        
        # Add few-shot examples
        examples = format_examples_for_prompt(query_type.value, max_examples=2)
        if examples:
            prompt = prompt.replace("**Rules:**", f"**Few-shot Examples:**\n{examples}\n\n**Rules:**")
        
        # Generate SQL
        response = self.llm.complete(
            prompt,
            max_tokens=512,
            temperature=0.3,  # Some creativity but mostly deterministic
        )
        
        sql_text = response.text.strip()
        
        # Extract SQL if wrapped in markdown code blocks
        sql = self._extract_sql(sql_text)
        
        # Validate
        valid = self._validate_sql(sql)
        
        return {
            "sql": sql,
            "valid": valid,
            "query_type": query_type.value,
            "explanation": f"Generated {query_type.value} query using schema context",
            "confidence": response.completion_tokens,  # Placeholder
        }

    def correct(
        self,
        question: str,
        failed_sql: str,
        error_message: str,
        schema: dict,
        dialect: str = "sqlite",
    ) -> dict:
        """Self-correct a failed SQL query using LLM reflection.

        Args:
            question: Original natural language question
            failed_sql: Previous SQL that caused an error
            error_message: Execution or validation error message
            schema: Database schema dict
            dialect: Target database dialect (sqlite, postgres, mysql, etc.)

        Returns:
            Dict with corrected sql, validity, and explanation
        """
        schema_text = self._format_schema(schema)
        prompt = f"""You are an expert SQL debugger. The following SQL query was generated to answer:
"{question}"

However, executing it against the {dialect} database failed with this error:
{error_message}

Failed SQL:
```sql
{failed_sql}
```

Database Schema:
{schema_text}

Rules:
1. Fix the SQL query to resolve the exact error.
2. Target dialect: {dialect}.
3. ONLY use read-only SELECT or WITH statements (no modifications).
4. Verify all table and column names exist in the schema.
5. Return ONLY the corrected SQL query inside a ```sql code block.
"""
        response = self.llm.complete(
            prompt,
            max_tokens=512,
            temperature=0.1,
        )
        sql_text = response.text.strip()
        sql = self._extract_sql(sql_text)
        valid = self._validate_sql(sql)
        return {
            "sql": sql,
            "valid": valid,
            "query_type": "CORRECTION",
            "explanation": f"Self-corrected SQL to resolve error: {error_message}",
        }
    
    def _format_schema(self, schema: dict) -> str:
        """Format schema dict for prompt."""
        parts = []
        for table_name, columns in schema.items():
            parts.append(f"Table: {table_name}")
            for col in columns:
                col_def = f"  - {col.get('name', 'unknown')}: {col.get('type', 'unknown')}"
                if col.get("nullable"):
                    col_def += " [nullable]"
                if col.get("description"):
                    col_def += f" -- {col.get('description')}"
                parts.append(col_def)
            parts.append("")
        return "\n".join(parts)
    
    def _extract_sql(self, response_text: str) -> str:
        """Extract SQL from LLM response (may be wrapped in markdown)."""
        # Check for markdown code block
        if "```sql" in response_text:
            match = re.search(r"```sql\n(.*?)\n```", response_text, re.DOTALL)
            if match:
                return match.group(1).strip()
        elif "```" in response_text:
            match = re.search(r"```\n(.*?)\n```", response_text, re.DOTALL)
            if match:
                return match.group(1).strip()
        
        return response_text
    
    def _validate_sql(self, sql: str) -> bool:
        """Basic SQL validation."""
        if not sql or len(sql) < 5:
            return False
        
        # Check for dangerous commands
        dangerous = ["DELETE", "DROP", "TRUNCATE", "ALTER", "INSERT", "UPDATE"]
        upper_sql = sql.upper()
        
        if any(f"{cmd} " in upper_sql or upper_sql.startswith(cmd) for cmd in dangerous):
            return False
        
        # Must be SELECT or WITH
        if not (upper_sql.strip().startswith("SELECT") or upper_sql.strip().startswith("WITH")):
            return False
        
        return True
