"""Markdown document ingester."""

import re
from pathlib import Path
from typing import List, Any

from lakeforge.docs.base import BaseDocIngester
from lakeforge.models import GlossaryCard
from lakeforge.docs.sanitizer import DocSanitizer


class MarkdownIngester(BaseDocIngester):
    """Ingest Markdown files and extract glossary terms, examples, metadata."""

    def supports(self, source: str | Path) -> bool:
        """Check if source is a Markdown file."""
        path = Path(source)
        return path.suffix.lower() in [".md", ".markdown"]

    def ingest(self, source: str | Path) -> List[Any]:
        """
        Ingest Markdown file and extract glossary terms and examples.

        Args:
            source: Path to Markdown file

        Returns:
            List of GlossaryCard objects
        """
        path = Path(source)

        if not path.exists():
            return []

        text = path.read_text(encoding="utf-8")
        cards = []

        # Parse headings as potential glossary terms
        heading_pattern = r"^#+\s+(.+)$"
        headings = re.findall(heading_pattern, text, re.MULTILINE)

        for heading in headings:
            heading_clean = DocSanitizer.sanitize_text(heading.strip())

            # Extract content until next heading
            # Find the heading in text
            heading_pattern_exact = r"^#{1,6}\s+" + re.escape(heading) + r"\s*\n(.*?)(?=^#{1,6}\s|$)"
            match = re.search(heading_pattern_exact, text, re.MULTILINE | re.DOTALL)

            if match:
                content = match.group(1).strip()

                # Skip if content is empty or too short
                if len(content) < 10:
                    continue

                # Extract first paragraph as definition
                paragraphs = re.split(r"\n\n+", content)
                definition = ""
                for para in paragraphs:
                    # Skip code blocks and lists for definition
                    if not para.startswith("```") and not para.startswith("-"):
                        definition = para.strip()
                        break

                if definition:
                    definition = DocSanitizer.sanitize_text(definition)

                    # Check for injection
                    if DocSanitizer.check_injection(definition):
                        definition = "[MALICIOUS CONTENT DETECTED - REDACTED]"

                    card = GlossaryCard(
                        term=heading_clean,
                        definition=definition,
                        source="markdown",
                    )
                    cards.append(card)

        return cards
