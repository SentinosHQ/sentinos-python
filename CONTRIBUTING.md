# Contributing

Thanks for helping improve the Sentinos Python SDK.

## Development setup

```bash
python3 -m venv .venv && source .venv/bin/activate
python -m pip install --upgrade pip
pip install -e ".[dev]"
tox -q
```

## Style

- Lint: `python -m ruff check sentinos tests`
- Typecheck: `python -m mypy sentinos`

## Pull requests

- Keep changes focused.
- Add or update tests when behavior changes.
- Avoid breaking public APIs without a major version bump.
