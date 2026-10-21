"""Pytest configuration and shared fixtures."""

import sys
from unittest.mock import MagicMock

# Mock external dependencies that may not be installed
sys.modules["databricks"] = MagicMock()
sys.modules["databricks.sql"] = MagicMock()
