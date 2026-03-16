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

- Run formatting/lint: `python -m ruff check sentinos tests`
- Typecheck: `python -m mypy sentinos`

## Pull requests

- Keep changes focused.
- Add/adjust tests when behavior changes.
- Avoid breaking public APIs without bumping major versions.
