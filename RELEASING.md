# Releasing sentinos (Python SDK)

This package is published to PyPI as `sentinos`.

If releasing both SDK repos, publish in this order:

1. `sentinos-sdk-core`
2. `sentinos`

## Publishing model

This repo uses GitHub Actions + PyPI Trusted Publishing (OIDC).

- Workflow: `.github/workflows/publish.yml`
- Trigger: push tag `v*` (for example `v0.1.1`)
- No long-lived PyPI API token is required.

## Preflight

```bash
python3 -m venv .venv && source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -e ".[dev]"
python -m ruff check sentinos tests
python -m mypy sentinos
python -m pytest -q
rm -rf dist
python -m pip install -U build twine
python -m build
python -m twine check dist/*
```

## Release

1. Ensure dependency floor in `pyproject.toml` is correct:
   - `sentinos-sdk-core>=<required-version>`
2. Bump `version` in `pyproject.toml`.
3. Commit and push to `main`.
4. Create and push tag:

```bash
git tag -a vX.Y.Z -m "Release vX.Y.Z"
git push origin vX.Y.Z
```

5. Verify GitHub workflow success.
6. Verify package on PyPI:

```bash
python -m pip install -U sentinos
```

## Optional fallback (manual upload)

Use only if GitHub Actions is unavailable:

```bash
python -m twine upload dist/*
```
