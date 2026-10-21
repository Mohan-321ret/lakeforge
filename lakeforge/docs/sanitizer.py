"""Document sanitizer to prevent prompt injection and malicious content."""

import re
from typing import Any, Dict, List


class DocSanitizer:
    """Sanitize user-provided documentation to prevent injection attacks."""

    # Patterns that indicate potential injection attempts
    INJECTION_PATTERNS = [
        r"(?i)ignore.*previous.*instructions",
        r"(?i)system.*prompt",
        r"(?i)execute.*command",
        r"(?i)override.*safety",
        r"(?i)bypass.*security",
        r"(?i)eval\s*\(",
        r"(?i)exec\s*\(",
        r"<script",
        r"javascript:",
    ]

    @staticmethod
    def sanitize_text(text: str) -> str:
        """
        Sanitize plain text by removing dangerous patterns.

        Args:
            text: Input text

        Returns:
            Sanitized text
        """
        if not isinstance(text, str):
            return text

        # Remove HTML tags
        text = re.sub(r"<[^>]+>", "", text)

        # Remove JavaScript protocol
        text = re.sub(r"javascript:", "", text, flags=re.IGNORECASE)

        # Remove control characters
        text = "".join(c for c in text if ord(c) >= 32 or c in "\n\r\t")

        return text

    @staticmethod
    def check_injection(text: str) -> bool:
        """
        Check if text contains injection patterns.

        Args:
            text: Input text

        Returns:
            True if injection patterns detected
        """
        if not isinstance(text, str):
            return False

        text_lower = text.lower()
        for pattern in DocSanitizer.INJECTION_PATTERNS:
            if re.search(pattern, text_lower):
                return True

        return False

    @staticmethod
    def sanitize_dict(data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Recursively sanitize a dictionary.

        Args:
            data: Input dictionary

        Returns:
            Sanitized dictionary
        """
        if not isinstance(data, dict):
            return data

        sanitized = {}
        for key, value in data.items():
            # Sanitize key
            if isinstance(key, str):
                sanitized[DocSanitizer.sanitize_text(key)] = None
            else:
                sanitized[key] = None

            # Sanitize value recursively
            if isinstance(value, dict):
                sanitized[list(sanitized.keys())[-1]] = DocSanitizer.sanitize_dict(
                    value
                )
            elif isinstance(value, list):
                sanitized[list(sanitized.keys())[-1]] = [
                    DocSanitizer.sanitize_dict(v)
                    if isinstance(v, dict)
                    else DocSanitizer.sanitize_text(v)
                    if isinstance(v, str)
                    else v
                    for v in value
                ]
            elif isinstance(value, str):
                sanitized[list(sanitized.keys())[-1]] = DocSanitizer.sanitize_text(
                    value
                )
            else:
                sanitized[list(sanitized.keys())[-1]] = value

        return sanitized

    @staticmethod
    def sanitize_list(items: List[Any]) -> List[Any]:
        """
        Sanitize a list of items.

        Args:
            items: Input list

        Returns:
            Sanitized list
        """
        if not isinstance(items, list):
            return items

        return [
            DocSanitizer.sanitize_dict(item)
            if isinstance(item, dict)
            else DocSanitizer.sanitize_text(item)
            if isinstance(item, str)
            else item
            for item in items
        ]
