# momo-sdk

[![CI](https://github.com/kangwa/momo-sdk/actions/workflows/ci.yml/badge.svg)](https://github.com/kangwa/momo-sdk/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Python 3.10+](https://img.shields.io/badge/python-3.10%2B-blue.svg)](pyproject.toml)

An unofficial Python SDK for the [MTN Mobile Money (MoMo) Open API](https://momodeveloper.mtn.com/api-documentation/) — Collections, Disbursements, and Remittance, with sync and async clients built on httpx.

Not affiliated with, endorsed by, or officially connected to MTN Group.

## Development

```bash
uv sync --dev
uv run pytest
uv run ruff check .
uv run mypy src
```

Requires Python 3.10+.

## License

MIT — see [LICENSE](LICENSE).
