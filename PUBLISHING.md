# Publishing Guide for EPUB2Speech

This guide outlines the steps to publish EPUB2Speech to PyPI.

## Prerequisites

1. **PyPI Account**: Create an account at https://pypi.org if you don't have one
2. **API Token**: Generate an API token from your PyPI account settings
3. **Repository Access**: Ensure you have admin access to the GitHub repository

## Pre-Publishing Checklist

### 1. Version Management
- [ ] Update version in `pyproject.toml`
- [ ] Commit all changes

### 2. Code Quality
- [ ] All tests pass: `poetry run python test.py`
- [ ] Code formatting: `poetry run black epub2speech/ tests/`
- [ ] Import sorting: `poetry run isort epub2speech/ tests/`
- [ ] Linting: `poetry run ruff check epub2speech/ tests/`
- [ ] Type checking: `poetry run mypy epub2speech/`

### 3. Documentation
- [ ] README.md is up to date
- [ ] All docstrings are accurate
- [ ] Examples in README work correctly

### 4. Build Verification
- [ ] Build succeeds: `poetry build`
- [ ] Distribution files are generated in `dist/`
- [ ] Test installation locally: `pip install dist/*.whl`

## Publishing Methods

### Method 1: Manual Publishing (Recommended for First Release)

1. **Build the package**:
   ```bash
   poetry build
   ```

2. **Upload to Test PyPI** (optional but recommended):
   ```bash
   poetry config repositories.test-pypi https://test.pypi.org/legacy/
   poetry config pypi-token.test-pypi YOUR_TEST_PYPI_TOKEN
   poetry publish -r test-pypi
   ```

3. **Test the package**:
   ```bash
   pip install --index-url https://test.pypi.org/simple/ epub2speech
   epub2speech --help
   ```

4. **Upload to PyPI**:
   ```bash
   poetry config pypi-token.pypi YOUR_PYPI_TOKEN
   poetry publish
   ```

### Method 2: GitHub Actions (Automated)

1. **Set up secrets in GitHub**:
   - Go to Settings → Secrets and variables → Actions
   - Add `PYPI_API_TOKEN` with your PyPI API token

2. **Create a release**:
   - Go to Releases → Create a new release
   - Tag format: `v0.1.0` (must match semantic versioning)
   - Fill in release notes
   - Publish release

3. **GitHub Actions will automatically**:
   - Run tests
   - Build the package
   - Publish to PyPI

### Method 3: Using the Release Script

1. **Bump version**:
   ```bash
   python scripts/release.py patch  # or minor/major
   ```

2. **Review changes**:
   ```bash
   git diff
   ```

3. **Commit and tag**:
   ```bash
   git add -A
   git commit -m "chore: release version 0.1.1"
   git tag v0.1.1
   git push origin main --tags
   ```

## Post-Publishing Verification

### 1. PyPI Package Verification
- [ ] Package appears on https://pypi.org/project/epub2speech/
- [ ] All metadata is correct
- [ ] README renders properly
- [ ] Classifiers are appropriate

### 2. Installation Testing
- [ ] Test installation: `pip install epub2speech`
- [ ] Verify CLI works: `epub2speech --help`
- [ ] Test basic functionality with sample EPUB

### 3. Documentation
- [ ] Update repository with new version
- [ ] Announce release if applicable
- [ ] Monitor for any user issues

## Troubleshooting

### Common Issues

1. **Build fails**: Check for syntax errors or missing dependencies
2. **Upload fails**: Verify API token and network connection
3. **Metadata errors**: Ensure pyproject.toml is valid
4. **Import errors**: Check package structure and __init__.py files

### Getting Help

- PyPI documentation: https://pypi.org/help/
- Poetry documentation: https://python-poetry.org/docs/
- Project issues: https://github.com/oomol-lab/epub2speech/issues

## Security Considerations

- Never commit API tokens to code
- Use GitHub Secrets for automated publishing
- Rotate API tokens regularly
- Monitor package downloads for anomalies

## Release Schedule

- **Patch releases**: Bug fixes and minor improvements
- **Minor releases**: New features, backwards compatible
- **Major releases**: Breaking changes (rare, with deprecation warnings)

## Version Numbering

Follow [Semantic Versioning](https://semver.org/):
- MAJOR.MINOR.PATCH
- MAJOR: Breaking changes
- MINOR: New features, backwards compatible
- PATCH: Bug fixes

Example: `0.1.0` → `0.1.1` (patch) → `0.2.0` (minor) → `1.0.0` (major)