"""PII Detection and Masking."""

import hashlib
import re
from enum import Enum
from typing import Any, Optional


class PIIMaskingMethod(str, Enum):
    """PII masking methods."""

    HASH = "hash"
    REDACT = "redact"


class PIIDetector:
    """Detect PII in column names and values."""

    # Regex patterns for common PII
    PII_PATTERNS = {
        "email": re.compile(
            r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$", re.IGNORECASE
        ),
        "phone": re.compile(
            r"^[\+]?[(]?[0-9]{3}[)]?[-\s\.]?[0-9]{3}[-\s\.]?[0-9]{4,6}$|^[0-9]{3}[-\s\.][0-9]{4}$",
            re.IGNORECASE,
        ),
        "ssn": re.compile(r"^\d{3}-\d{2}-\d{4}$"),
        "credit_card": re.compile(r"^[0-9]{4}[\s\-]?[0-9]{4}[\s\-]?[0-9]{4}[\s\-]?[0-9]{4}$"),
        "ip_address": re.compile(
            r"^(?:[0-9]{1,3}\.){3}[0-9]{1,3}$|^(?:[0-9a-f]{0,4}:){2,7}[0-9a-f]{0,4}$",
            re.IGNORECASE,
        ),
    }

    # Column name heuristics
    RISKY_COLUMN_NAMES = {
        "email",
        "ssn",
        "social_security",
        "phone",
        "credit_card",
        "card_number",
        "password",
        "api_key",
        "token",
        "secret",
        "ip_address",
        "mac_address",
        "address",
        "zip_code",
        "postal_code",
        "date_of_birth",
        "dob",
    }

    def __init__(self, detection_method: str = "regex"):
        """Initialize PII detector.

        Args:
            detection_method: "regex" or "llm" (llm coming in Phase 3).
        """
        self.detection_method = detection_method

    def is_column_risky_by_name(self, column_name: str) -> bool:
        """Check if column name suggests PII.

        Args:
            column_name: Column name to check.

        Returns:
            True if column name is risky.
        """
        col_lower = column_name.lower()
        return any(risky in col_lower for risky in self.RISKY_COLUMN_NAMES)

    def detect_pii_type(self, value: Any) -> Optional[str]:
        """Detect PII type in a value.

        Args:
            value: Value to check.

        Returns:
            PII type (email, phone, ssn, etc.) or None.
        """
        if value is None or value == "":
            return None

        value_str = str(value).strip()

        for pii_type, pattern in self.PII_PATTERNS.items():
            if pattern.match(value_str):
                return pii_type

        return None

    def analyze_column(
        self, column_name: str, sample_values: list[Any], confidence_threshold: float = 0.5
    ) -> tuple[bool, Optional[str], float]:
        """Analyze column for PII.

        Args:
            column_name: Column name.
            sample_values: Sample values from column.
            confidence_threshold: Minimum confidence (0-1) to flag as PII.

        Returns:
            Tuple of (is_pii, pii_type, confidence).
        """
        # Check column name
        if self.is_column_risky_by_name(column_name):
            return True, None, 0.9

        # Check sample values
        pii_counts = {}
        for value in sample_values:
            pii_type = self.detect_pii_type(value)
            if pii_type:
                pii_counts[pii_type] = pii_counts.get(pii_type, 0) + 1

        if not pii_counts:
            return False, None, 0.0

        # Calculate confidence
        most_common_pii = max(pii_counts.items(), key=lambda x: x[1])
        confidence = most_common_pii[1] / len(sample_values)

        if confidence >= confidence_threshold:
            return True, most_common_pii[0], confidence

        return False, None, confidence


class PIIMasker:
    """Mask PII values in data."""

    def __init__(self, masking_method: PIIMaskingMethod = PIIMaskingMethod.HASH):
        """Initialize masker.

        Args:
            masking_method: Masking method (hash or redact).
        """
        self.masking_method = masking_method

    def mask_value(self, value: Any, pii_type: Optional[str] = None) -> Any:
        """Mask a PII value.

        Args:
            value: Value to mask.
            pii_type: Type of PII (for context).

        Returns:
            Masked value.
        """
        if value is None or value == "":
            return value

        if self.masking_method == PIIMaskingMethod.HASH:
            return self._hash_value(value)
        else:  # REDACT
            return self._redact_value(value, pii_type)

    def _hash_value(self, value: Any) -> str:
        """Hash a value.

        Args:
            value: Value to hash.

        Returns:
            SHA256 hash (first 12 chars).
        """
        value_str = str(value).encode("utf-8")
        hash_obj = hashlib.sha256(value_str)
        return f"***{hash_obj.hexdigest()[:8]}***"

    def _redact_value(self, value: Any, pii_type: Optional[str] = None) -> str:
        """Redact a value.

        Args:
            value: Value to redact.
            pii_type: Type of PII.

        Returns:
            Redacted value.
        """
        value_str = str(value)

        if pii_type == "email":
            return "[REDACTED_EMAIL]"
        elif pii_type == "phone":
            return "[REDACTED_PHONE]"
        elif pii_type == "ssn":
            return "[REDACTED_SSN]"
        elif pii_type == "credit_card":
            return f"****{value_str[-4:]}"
        else:
            return f"[REDACTED]"

    def mask_row(
        self, row: dict[str, Any], pii_columns: dict[str, Optional[str]]
    ) -> dict[str, Any]:
        """Mask PII in a row.

        Args:
            row: Row data as dict.
            pii_columns: Dict mapping column name to PII type (or None).

        Returns:
            Row with PII masked.
        """
        masked_row = {}
        for col_name, value in row.items():
            if col_name in pii_columns:
                masked_row[col_name] = self.mask_value(value, pii_columns[col_name])
            else:
                masked_row[col_name] = value
        return masked_row
