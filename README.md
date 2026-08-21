# MTN MoMo Python SDK

[![CI](https://github.com/kangwa/mtn-momo-sdk/actions/workflows/ci.yml/badge.svg)](https://github.com/kangwa/mtn-momo-sdk/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Python 3.10+](https://img.shields.io/badge/python-3.10%2B-blue.svg)](pyproject.toml)

An unofficial Python SDK for the [MTN Mobile Money (MoMo) Open API](https://momodeveloper.mtn.com/api-documentation/) — Collections, Disbursements, and Remittance, with sync and async clients built on httpx.

Not affiliated with, endorsed by, or officially connected to MTN Group.

> **Status:** functionally complete against MoMo's documented API shape, not yet verified against a live sandbox or published to PyPI. See [Verifying against a real sandbox](#verifying-against-a-real-sandbox).

## Features

- Sync and async clients for all three products, sharing one request/response core
- Typed models (pydantic) and a typed exception hierarchy — no raw dicts, no string-matching error codes
- Automatic per-product token caching and refresh
- `wait_for_transaction()` — polls a request/transfer until it reaches a terminal status
- Sandbox provisioning helpers, usable as a library or a CLI

## Installation

Not yet on PyPI. Install from source:

```bash
git clone https://github.com/kangwa/mtn-momo-sdk
cd mtn-momo-sdk
uv sync
```

Requires Python 3.10+.

## Quickstart

### 1. Get sandbox credentials

Sign up at the [MoMo Developer Portal](https://momodeveloper.mtn.com/), subscribe to a product, and grab its subscription key. Then provision a sandbox API user/key:

```python
from mtn_momo import SandboxProvisioner

with SandboxProvisioner("YOUR_SUBSCRIPTION_KEY") as provisioner:
    credentials = provisioner.provision()
    print(credentials.api_user, credentials.api_key)
```

Or from the command line:

```bash
uv run mtn-momo-provision --subscription-key YOUR_SUBSCRIPTION_KEY
```

### 2. Request a payment (sync)

```python
import mtn_momo as momo

config = momo.ProductConfig(
    base_url="https://sandbox.momodeveloper.mtn.com",
    subscription_key="YOUR_COLLECTIONS_SUBSCRIPTION_KEY",
    api_user="...",
    api_key="...",
)

with momo.MomoClient(collections=config) as client:
    assert client.collections is not None
    reference_id = client.collections.request_to_pay(
        amount="500",
        currency="EUR",
        payer=momo.Party(party_id_type=momo.PartyIdType.MSISDN, party_id="256770000000"),
        payer_message="Invoice 123",
    )
    status = client.collections.wait_for_transaction(reference_id)
    print(status.status)  # SUCCESSFUL | FAILED | ...
```

### 3. Same thing, async

```python
import asyncio
import mtn_momo as momo

async def main() -> None:
    config = momo.ProductConfig(...)
    async with momo.AsyncMomoClient(collections=config) as client:
        assert client.collections is not None
        reference_id = await client.collections.request_to_pay(
            amount="500",
            currency="EUR",
            payer=momo.Party(party_id_type=momo.PartyIdType.MSISDN, party_id="256770000000"),
        )
        status = await client.collections.wait_for_transaction(reference_id)
        print(status.status)

asyncio.run(main())
```

### 4. Disbursements / Remittance

Same shape, a different product config, and `transfer()` with a `payee` instead of a `payer`:

```python
config = momo.ProductConfig(..., subscription_key="YOUR_DISBURSEMENTS_KEY")
with momo.MomoClient(disbursements=config) as client:
    assert client.disbursements is not None
    reference_id = client.disbursements.transfer(
        amount="1000",
        currency="EUR",
        payee=momo.Party(party_id_type=momo.PartyIdType.MSISDN, party_id="256770000001"),
    )
```

### 5. Balance and account-holder checks

```python
balance = client.collections.get_balance()  # or get_balance("EUR")
print(balance.available_balance, balance.currency)

is_active = client.collections.is_account_holder_active(
    momo.PartyIdType.MSISDN, "256770000000"
)
```

### 6. Handling errors

```python
from mtn_momo import NotEnoughFundsError, PayerNotFoundError, MomoAPIError, PollTimeoutError

try:
    client.collections.request_to_pay(...)
except PayerNotFoundError:
    ...
except NotEnoughFundsError:
    ...
except PollTimeoutError as e:
    print("still pending after timeout:", e.last_status)
except MomoAPIError as e:
    print(e.status_code, e.error_code, e.raw_body)
```

### Loading credentials from the environment

```python
config = momo.ProductConfig.from_env("MOMO_COLLECTIONS_")
# reads MOMO_COLLECTIONS_SUBSCRIPTION_KEY, MOMO_COLLECTIONS_API_USER,
# MOMO_COLLECTIONS_API_KEY, and optionally MOMO_COLLECTIONS_TARGET_ENVIRONMENT
```

## Development

```bash
uv sync --dev
uv run pre-commit install
uv run pytest                          # unit tests only, no network
uv run ruff check .
uv run ruff format --check
uv run mypy src
```

## Roadmap

- [x] All three products, sync + async
- [x] Polling, sandbox provisioning, CLI
- [ ] Usage examples
- [ ] Publish to PyPI

## License

MIT — see [LICENSE](LICENSE).
