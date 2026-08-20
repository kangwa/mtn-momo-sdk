# Contributing

## Setup

```bash
uv sync --dev
uv run pre-commit install
```

## Before submitting a change

```bash
uv run ruff check .
uv run ruff format .
uv run mypy src
uv run pytest -m "not sandbox"
```

All four must pass.

## Guidelines

- Add tests alongside any new code (respx-mocked, no real network calls in the default test suite).
- Keep commits scoped to one logical change.

## Reporting issues

Open a GitHub issue with a minimal repro. If it's an MTN API behavior mismatch, note the product (Collections/Disbursements/Remittance) and environment (sandbox/production).
