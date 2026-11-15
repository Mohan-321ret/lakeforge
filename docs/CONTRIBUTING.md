# Contributing to Lakeforge

Thank you for your interest in contributing! This document provides guidelines and instructions for contributing.

## Code of Conduct

Be respectful, inclusive, and professional in all interactions.

## Getting Started

### 1. Fork and Clone

```bash
git clone https://github.com/yourusername/lakeforge.git
cd lakeforge
```

### 2. Set Up Development Environment

```bash
# Install with dev dependencies
make install-dev
# or
pip install -e ".[dev,databricks,postgres,pdf,semantic]"

# Create .env file with API keys
cp .env.example .env
# Edit .env with your Groq API key
```

### 3. Verify Setup

```bash
# Run tests
make test

# Check code quality
make lint type-check
```

## Development Workflow

### 1. Create a Feature Branch

```bash
git checkout -b feature/your-feature-name
```

Use descriptive branch names:
- `feature/add-gcs-connector` for new features
- `fix/query-timeout-issue` for bug fixes
- `docs/update-readme` for documentation
- `test/add-integration-tests` for tests

### 2. Make Changes

Follow the project structure:

```
lakeforge/
├── sources/          # Data connectors (CSV, Databricks, PostgreSQL, etc.)
├── executor/         # Query executors
├── router/           # SQL generation & routing
├── validator/        # Query validation
├── discover.py       # Schema discovery
├── session.py        # Q&A session management
├── cli.py           # Command-line interface
├── errors.py        # Error handling
└── config.py        # Configuration management
```

### 3. Code Style

**Use these tools locally:**

```bash
# Format code
make format

# Check linting
make lint

# Fix issues
make lint-fix

# Type checking
make type-check
```

**Code Style Guidelines:**

- **Python**: Follow PEP 8
- **Line Length**: Max 88 characters (Black default)
- **Naming**: 
  - Classes: `PascalCase` (e.g., `DuckDBConnector`)
  - Functions/variables: `snake_case` (e.g., `get_schema`)
  - Constants: `UPPER_CASE` (e.g., `MAX_RESULT_ROWS`)
- **Type Hints**: Use type hints for all function signatures
- **Docstrings**: Use Google-style docstrings

Example:

```python
def execute_query(
    sql: str,
    timeout_sec: int = 30
) -> ExecutionResult:
    """Execute SQL query and return results.
    
    Args:
        sql: SQL query string
        timeout_sec: Query timeout in seconds
        
    Returns:
        ExecutionResult with status, data, and metadata
        
    Raises:
        ValidationError: If SQL is invalid
        ExecutionError: If execution fails
    """
    # Implementation
```

### 4. Write Tests

**Test Location**: `tests/test_*.py`

```python
import pytest
from pathlib import Path

class TestMyFeature:
    """Tests for my feature."""
    
    def test_basic_functionality(self):
        """Test basic functionality."""
        result = my_function()
        assert result is not None
        
    def test_error_handling(self):
        """Test error handling."""
        with pytest.raises(MyError):
            my_function(invalid_input)
```

**Run tests:**

```bash
# Run all tests
make test

# Run specific test
pytest tests/test_myfeature.py -v

# Run with coverage
make test-cov

# Run in parallel
make test-fast
```

**Coverage Requirements:**
- New features: minimum 80% coverage
- Bug fixes: must include regression test
- Documentation: no coverage requirement

### 5. Commit Changes

Write clear, descriptive commit messages:

```bash
# Good
git commit -m "Add GCS connector for Cloud Storage integration

- Implement GoogleCloudStorageConnector class
- Add schema discovery for GCS parquet files
- Include authentication via GOOGLE_APPLICATION_CREDENTIALS"

# Avoid
git commit -m "Fix stuff"
git commit -m "WIP"
```

**Commit Guidelines:**
- One logical change per commit
- Include related tests in same commit
- Reference issues: `Fixes #123`

### 6. Push and Create Pull Request

```bash
git push origin feature/your-feature-name
```

**PR Template:**

```markdown
## Description
Brief description of changes.

## Type of Change
- [ ] New feature
- [ ] Bug fix
- [ ] Documentation
- [ ] Performance improvement

## Testing
Describe testing performed:
- [ ] Unit tests added/updated
- [ ] Integration tests added/updated
- [ ] Manual testing completed

## Checklist
- [ ] Code follows style guidelines (make lint)
- [ ] Tests pass locally (make test)
- [ ] Documentation updated
- [ ] No breaking changes (or documented)
```

## Adding a New Connector

To add support for a new data source:

### 1. Create Connector Class

File: `lakeforge/sources/your_source.py`

```python
from lakeforge.sources.registry import BaseConnector

class YourSourceConnector(BaseConnector):
    """Connector for YourSource."""
    
    def __init__(self, source: str):
        """Initialize connector."""
        self.source = source
        self._connect()
        
    def _connect(self) -> None:
        """Establish connection."""
        # Implementation
        
    def list_tables(self) -> list[str]:
        """List tables."""
        # Implementation
        
    def get_schema(self, table_name: str) -> dict[str, str]:
        """Get table schema."""
        # Implementation
        
    def get_row_count(self, table_name: str) -> int:
        """Get row count."""
        # Implementation
        
    def query(self, sql: str, limit: int = 10000) -> list[dict]:
        """Execute query."""
        # Implementation
```

### 2. Create Executor Class

File: `lakeforge/executor/your_source.py`

```python
from lakeforge.executor.base import BaseExecutor, ExecutionResult

class YourSourceExecutor(BaseExecutor):
    """Executor for YourSource."""
    
    def execute(
        self,
        sql: str,
        timeout_sec: int = 30
    ) -> ExecutionResult:
        """Execute query."""
        # Implementation
```

### 3. Register in Registry

File: `lakeforge/sources/registry.py`

```python
def get_connector(source: str) -> BaseConnector:
    """Get connector for source."""
    
    if source.startswith("yoursource://"):
        return YourSourceConnector(source)
    # ...
```

### 4. Write Tests

File: `tests/test_your_source_connector.py`

```python
class TestYourSourceConnector:
    """Tests for YourSource connector."""
    
    def test_initialization(self):
        """Test connector initialization."""
        # Test
        
    def test_list_tables(self):
        """Test listing tables."""
        # Test
        
    def test_query(self):
        """Test query execution."""
        # Test
```

### 5. Update Documentation

- Add to README.md supported sources
- Document environment variables needed
- Add to USAGE.md with examples

## Improving Error Handling

Error types are in `lakeforge/errors.py`.

When adding new error handling:

```python
from lakeforge.errors import LakeforgeException

class NewError(LakeforgeException):
    """Description of error."""
    pass

# Usage
raise NewError(
    message="What went wrong",
    suggestion="How to fix it"
)
```

## Documentation

### Updating README

- Keep examples up-to-date
- Document new features
- Update installation instructions

### Adding API Documentation

See API.md for documented patterns. Update when adding public functions.

### Docstring Format

Use Google-style docstrings:

```python
def function(arg1: str, arg2: int) -> dict:
    """Short description.
    
    Longer description if needed.
    
    Args:
        arg1: Description of arg1
        arg2: Description of arg2
        
    Returns:
        Description of return value
        
    Raises:
        ValueError: When value is invalid
        RuntimeError: When runtime error occurs
    """
```

## Performance Considerations

When submitting performance improvements:

1. Provide benchmarks (before/after timing)
2. Test with realistic data sizes
3. Document optimization trade-offs
4. Include performance tests

Example:

```python
import time

start = time.time()
# Code to benchmark
duration = time.time() - start
print(f"Time: {duration:.2f}s for {rows} rows")
```

## Pull Request Review

**Reviewers will check:**

1. Code quality and style
2. Test coverage
3. Documentation completeness
4. Performance impact
5. Backward compatibility
6. Error handling

**Expected response time:** 2-5 business days

## Reporting Issues

**Before creating an issue:**

1. Check existing issues and discussions
2. Verify the problem is reproducible
3. Gather error messages and logs

**Issue Template:**

```markdown
## Description
Clear description of the issue.

## Steps to Reproduce
1. Step one
2. Step two
3. Step three

## Expected Behavior
What should happen.

## Actual Behavior
What actually happens.

## Environment
- Python version: 3.13
- OS: macOS/Linux/Windows
- Lakeforge version: 0.1.0

## Logs
```
Error message and stack trace
```
```

## Release Process

Maintainers use this process to release new versions:

1. Update version in `pyproject.toml`
2. Update CHANGELOG.md
3. Create git tag: `git tag v0.2.0`
4. Push tag: `git push origin v0.2.0`
5. GitHub Actions publishes to PyPI

## Community

- **Discussions**: GitHub Discussions for questions
- **Issues**: GitHub Issues for bugs and features
- **Slack/Discord**: (If available, link here)

## Questions?

- Read CONTRIBUTING.md and TROUBLESHOOTING.md
- Open a Discussion in GitHub
- Check existing Issues and PRs

Thank you for contributing! 🙏
