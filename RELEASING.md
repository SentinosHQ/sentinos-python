# Releasing `sentinos` (Python SDK)

This package is published to PyPI as `sentinos`.

If you also publish `sentinos-sdk-core`, release order is mandatory:

1. `sentinos-sdk-core` (core client + OpenAPI surface)
2. `sentinos` (ergonomic wrapper)

## One-Time Setup

### 1) Create a PyPI token

1. Log into PyPI and create an API token with access to the `sentinos` project.
2. Store it in your password manager.

Recommended: use scoped project tokens (not account-wide tokens).

### 2) Configure credentials locally (preferred)

Set `TWINE_PASSWORD` for the current shell:

```bash
export TWINE_USERNAME="__token__"
export TWINE_PASSWORD="pypi-<token>"
```

Or create `~/.pypirc`:

```ini
[distutils]
index-servers =
  pypi
  testpypi

[pypi]
username = __token__
password = pypi-<token>

[testpypi]
repository = https://test.pypi.org/legacy/
username = __token__
password = pypi-<token>
```

## Preflight (Must Pass)

From the repository root:

```bash
python3 -m venv .venv && source .venv/bin/activate
python -m pip install --upgrade pip
pip install -e ".[dev]"
tox -q
```

## Version Bump

1. Update `version` in `pyproject.toml`.
2. Ensure README examples still match current APIs.

## Build

From the repository root:

```bash
rm -rf dist/
python -m pip install --upgrade build twine
python -m build
python -m twine check dist/*
```

## Publish (Recommended Flow)

### 1) TestPyPI dry run

```bash
python -m twine upload --repository testpypi dist/*
```

Smoke test install:

```bash
python3 -m venv /tmp/sentinos-sdk-smoke
source /tmp/sentinos-sdk-smoke/bin/activate
pip install --upgrade pip
pip install --index-url https://test.pypi.org/simple/ --extra-index-url https://pypi.org/simple sentinos
python -c "from sentinos import SentinosClient; print('ok')"
```

### 2) Production PyPI publish

```bash
python -m twine upload dist/*
```

