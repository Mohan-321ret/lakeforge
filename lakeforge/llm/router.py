"""Question router - classifies questions into query types."""

from enum import Enum
from lakeforge.llm import BaseLLM, get_llm


class QueryType(str, Enum):
    """Query type classifications."""
    
    DESCRIBE = "DESCRIBE"
    AGGREGATE = "AGGREGATE"
    FILTER = "FILTER"
    JOIN = "JOIN"
    CUSTOM = "CUSTOM"


class QuestionRouter:
    """Route questions to appropriate SQL generation templates."""
    
    def __init__(self, llm: BaseLLM | None = None):
        """
        Initialize question router.
        
        Args:
            llm: LLM client to use for classification (default: Groq)
        """
        self.llm = llm or get_llm(provider="groq")
    
    def classify(self, question: str) -> QueryType:
        """
        Classify a question into a query type.
        
        Args:
            question: Natural language question
            
        Returns:
            QueryType (DESCRIBE, AGGREGATE, FILTER, JOIN, or CUSTOM)
        """
        # Load template
        from pathlib import Path
        template_path = Path(__file__).parent.parent / "prompts" / "route.j2"
        template_text = template_path.read_text()
        
        # Simple Jinja2 rendering (replace placeholders)
        prompt = template_text.replace("{{ question }}", question)
        
        # Call LLM
        response = self.llm.complete(
            prompt,
            max_tokens=10,
            temperature=0.0,  # Deterministic classification
        )
        
        # Parse response
        category = response.text.strip().upper()
        
        # Validate
        try:
            return QueryType[category]
        except KeyError:
            # Default to CUSTOM if unrecognized
            return QueryType.CUSTOM
    
    def classify_batch(self, questions: list[str]) -> dict[str, QueryType]:
        """
        Classify multiple questions.
        
        Args:
            questions: List of questions
            
        Returns:
            Dict mapping question → QueryType
        """
        return {q: self.classify(q) for q in questions}
