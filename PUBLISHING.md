# Lakeforge Package Publishing Guide

## Publishing to PyPI

### Prerequisites

1. **PyPI Account**: Create at https://pypi.org/account/register/
2. **API Token**: Generate at https://pypi.org/manage/account/
3. **Build Tools**: Install locally
   ```bash
   pip install build twine
   ```

### Step 1: Prepare Release

#### Update Version

File: `pyproject.toml`

```toml
[project]
name = "lakeforge"
version = "0.1.0"  # Update to new version
```

Version format: MAJOR.MINOR.PATCH (semver)
- `0.1.0` → `0.1.1` (patch - bug fixes)
- `0.1.0` → `0.2.0` (minor - new features)
- `0.1.0` → `1.0.0` (major - breaking changes)

#### Update Changelog

File: `CHANGELOG.md`

```markdown
# Changelog

## [0.2.0] - 2024-11-21

### Added
- New GCS connector for Google Cloud Storage
- Support for semantic search
- Error handling improvements

### Fixed
- Fixed query timeout issue (#123)
- Fixed PostgreSQL connection pooling

### Changed
- Increased default result limit to 50,000 rows
- Improved error messages

### Deprecated
- Old API endpoint (use new endpoint instead)

### Removed
- Support for Python 3.9

## [0.1.0] - 2024-09-15

Initial release
```

#### Update README

Ensure README.md reflects current state:
- Installation instructions current
- Examples work
- Screenshots/demo up-to-date

### Step 2: Build Distribution

```bash
# Clean previous builds
rm -rf dist/ build/ *.egg-info/

# Build wheel and source distribution
python -m build

# Result
# dist/
# ├── lakeforge-0.2.0-py3-none-any.whl
# └── lakeforge-0.2.0.tar.gz
```

### Step 3: Verify Build

```bash
# Check contents
tar -tzf dist/lakeforge-0.2.0.tar.gz | head -20

# Verify wheel
unzip -l dist/lakeforge-0.2.0-py3-none-any.whl | head -20

# Test locally
pip install dist/lakeforge-0.2.0-py3-none-any.whl
lakeforge --version
```

### Step 4: Upload to TestPyPI (Optional)

Test before publishing to real PyPI:

```bash
# Upload to TestPyPI
twine upload --repository testpypi dist/*

# Test installation
pip install -i https://test.pypi.org/simple/ lakeforge

# Uninstall test version
pip uninstall lakeforge
```

### Step 5: Upload to PyPI

```bash
# Set up authentication
# Create ~/.pypirc (or use environment variable)
cat > ~/.pypirc << EOF
[distutils]
index-servers =
    pypi

[pypi]
username = __token__
password = pypi-...  # Your API token
EOF

# Or set environment variable
export TWINE_PASSWORD="pypi-AgEIcHlwaS5vcmc..."

# Upload to PyPI
twine upload dist/*

# Verify
pip install --upgrade lakeforge
lakeforge --version
```

### Step 6: Create GitHub Release

```bash
# Tag the release
git tag v0.2.0
git push origin v0.2.0

# On GitHub: Create Release
# - Title: "Release v0.2.0"
# - Description: Changelog for this version
# - Attach: dist/lakeforge-0.2.0.tar.gz and .whl
```

## Automated Publishing (GitHub Actions)

The CI/CD pipeline automatically publishes to PyPI when you push a tag.

### Setup

1. **Add PyPI Token to GitHub**:
   - Go to repository Settings → Secrets
   - Add secret: `PYPI_API_TOKEN` = your-pypi-token

2. **GitHub Actions Workflow**:
   Already configured in `.github/workflows/ci-cd.yml`:
   ```yaml
   - name: Publish to PyPI
     if: startsWith(github.ref, 'refs/tags')
     uses: pypa/gh-action-pypi-publish@release/v1
   ```

### Automated Release Process

```bash
# 1. Update version in pyproject.toml
# 2. Update CHANGELOG.md
# 3. Commit changes
git add pyproject.toml CHANGELOG.md
git commit -m "Release v0.2.0"

# 4. Push and tag
git tag v0.2.0
git push origin main
git push origin v0.2.0

# 5. GitHub Actions automatically:
#    - Runs tests
#    - Builds package
#    - Publishes to PyPI
#    - Creates GitHub release

# 6. Verify publication
pip install --upgrade lakeforge
```

## Version Management Best Practices

### Semantic Versioning

```
MAJOR.MINOR.PATCH

0.1.0
^     Major: 0 (pre-release phase)
  ^   Minor: 1 (feature additions)
    ^ Patch: 0 (bug fixes)

0.1.0 → 0.1.1  Fix: documentation error
0.1.0 → 0.2.0  Add: new PostgreSQL connector
0.1.0 → 1.0.0  Change: stable API, breaking changes
```

### Release Checklist

- [ ] Tests pass: `pytest tests/ -v`
- [ ] Linting passes: `ruff check lakeforge/`
- [ ] Type checking passes: `mypy lakeforge/`
- [ ] Version updated in `pyproject.toml`
- [ ] CHANGELOG.md updated
- [ ] README.md reviewed
- [ ] All imports working: `python -c "import lakeforge"`
- [ ] Sample data included in `tests/data/`
- [ ] Documentation complete (INSTALL, USAGE, API, CONTRIBUTING)
- [ ] Git tag created and pushed
- [ ] PyPI publication successful

## Managing Dependencies

### Update Dependencies Safely

```bash
# Check for updates
pip list --outdated

# Update individual packages
pip install --upgrade package-name

# Test updates
pytest tests/ -v

# Update requirements
pip freeze > requirements.txt

# Commit changes
git add requirements.txt pyproject.toml
git commit -m "Update dependencies"
```

### Dependency Pinning

In `pyproject.toml`:

```toml
dependencies = [
    "typer[all]>=0.9.0",        # Minimum version
    "duckdb>=0.10.0,<1.0.0",    # Version range
    "pydantic==2.5.0",          # Exact version (for stability)
]
```

## Maintaining Multiple Versions

### Branch Strategy

```
main (latest stable)
├── v0.2.x (maintenance branch)
├── v0.1.x (legacy branch)
└── develop (development branch)
```

### Backporting Fixes

```bash
# Cherry-pick fix to older branch
git checkout v0.1.x
git cherry-pick commit-hash
git push origin v0.1.x
git tag v0.1.4
git push origin v0.1.4
```

## PyPI Package Management

### View Package Info

```bash
# View on PyPI
https://pypi.org/project/lakeforge/

# View releases
https://pypi.org/project/lakeforge/#history

# View statistics
https://pypi.org/stats/
```

### Package Metadata

Verify package displays correctly on PyPI:

```bash
# Check metadata
python -c "
import pkg_resources
dist = pkg_resources.get_distribution('lakeforge')
print(f'Name: {dist.project_name}')
print(f'Version: {dist.version}')
print(f'Location: {dist.location}')
"

# Or download and inspect
pip download lakeforge --no-deps
tar -xzf lakeforge-*.tar.gz
cat lakeforge-*/PKG-INFO
```

### Download Statistics

```bash
# View stats on PyPI dashboard
# Monthly and daily download trends
# Version breakdown
```

## Distributing Pre-Releases

For beta versions:

```toml
version = "0.2.0rc1"  # Release Candidate
version = "0.2.0b2"   # Beta 2
version = "0.2.0a1"   # Alpha 1
```

PyPI automatically marks as pre-release.

Users opt-in with:
```bash
pip install --pre lakeforge
```

## Docker Distribution

### Build and Push to Docker Hub

```bash
# Build image
docker build -t myusername/lakeforge:0.2.0 .
docker build -t myusername/lakeforge:latest .

# Push to Docker Hub
docker push myusername/lakeforge:0.2.0
docker push myusername/lakeforge:latest

# Users can then use
docker pull myusername/lakeforge:0.2.0
docker run -it myusername/lakeforge:0.2.0 --version
```

Dockerfile:

```dockerfile
FROM python:3.13-slim

WORKDIR /app

RUN pip install --no-cache-dir lakeforge[databricks,postgres]

ENV GROQ_API_KEY=""

ENTRYPOINT ["lakeforge"]
CMD ["--help"]
```

## Conda Distribution (Future)

```bash
# Create conda-forge feedstock
# (Requires separate process, see conda documentation)

# Users can then install
conda install -c conda-forge lakeforge
```

## Security

### Scan for Vulnerabilities

```bash
# Check for known vulnerabilities
pip install safety
safety check

# Or use GitHub's built-in scanning
# Settings → Security & analysis → Dependabot
```

### Signing Releases

```bash
# Sign with GPG
gpg --detach-sign dist/lakeforge-0.2.0-py3-none-any.whl

# Publish signature to PyPI
# (Configure in `.pypirc`)
```

## Troubleshooting

### "File already exists" on PyPI

Can't overwrite existing version. Must bump version.

```bash
# Solution: Increment patch version
# 0.2.0 → 0.2.1
```

### "Metadata errors" during upload

```bash
# Check metadata
twine check dist/*

# Fix DESCRIPTION format
# Make sure valid reStructuredText
```

### "Authentication failed"

```bash
# Verify API token is correct
cat ~/.pypirc

# Or use environment variable
export TWINE_USERNAME="__token__"
export TWINE_PASSWORD="pypi-..."
```

## Next Steps

1. Verify package installation: `pip install lakeforge`
2. Test all features work
3. Gather feedback from users
4. Plan next release based on issues/features
5. Create GitHub Discussions for feedback

## References

- PyPI Documentation: https://pypi.org/help/
- Twine Documentation: https://twine.readthedocs.io/
- Semantic Versioning: https://semver.org/
- Python Packaging Guide: https://packaging.python.org/
