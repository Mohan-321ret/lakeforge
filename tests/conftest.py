"""Pytest configuration and shared fixtures."""

import sys
from unittest.mock import MagicMock

_databricks_mock = MagicMock()
sys.modules["databricks"] = _databricks_mock
sys.modules["databricks.sql"] = _databricks_mock.sql
