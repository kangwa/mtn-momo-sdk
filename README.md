<div align="center" markdown="1">

# MTN Mobile Money (MoMo) Python SDK

**Unofficial Python SDK for the [MTN Mobile Money (MoMo) Open API](https://momodeveloper.mtn.com/api-documentation/)**

[![CI](https://github.com/kangwa/mtn-momo-sdk/actions/workflows/ci.yml/badge.svg)](https://github.com/kangwa/mtn-momo-sdk/actions/workflows/ci.yml)
[![Python 3.10+](https://img.shields.io/badge/python-3.10%2B-3776ab?style=flat-square&logo=python&logoColor=white)](pyproject.toml)
[![Typed](https://img.shields.io/badge/typing-typed-4c1?style=flat-square)](pyproject.toml)
[![License: MIT](https://img.shields.io/badge/license-MIT-yellow?style=flat-square)](LICENSE.md)

Collections, Disbursements, and Remittance — sync and async clients, built on httpx.

</div>

Not affiliated with, endorsed by, or officially connected to MTN Group.

## Installation

Not yet on PyPI — install from source:

```bash
git clone https://github.com/kangwa/mtn-momo-sdk
cd mtn-momo-sdk
uv sync
```

Requires Python 3.10+.

## Usage

Sign up at the [MoMo Developer Portal](https://momodeveloper.mtn.com/) and subscribe to the products you need — Collections, Disbursements, and Remittance are separate subscriptions, **each with its own subscription key**. Provision a sandbox API user and key once per product, against that product's key:

```python
from mtn_momo import SandboxProvisioner

provisioner = SandboxProvisioner("YOUR_COLLECTIONS_SUBSCRIPTION_KEY")
credentials = provisioner.provision()
print(credentials.api_user, credentials.api_key)
```

Or from the command line, which prints output shaped for `.env` directly:

```bash
uv run mtn-momo-provision --product collections --subscription-key YOUR_COLLECTIONS_SUBSCRIPTION_KEY
# MOMO_COL_SUBSCRIPTION_KEY=...
# MOMO_COL_API_USER=...
# MOMO_COL_API_KEY=...
```

Repeat with `--product disbursements`/`--product remittance` and that product's own subscription key for the others. Copy `.env.example` to `.env` and fill in the values for whichever products you use:

| Product       | Prefix      | Required variables                        |
| ------------- | ----------- | ----------------------------------------- |
| Collections   | `MOMO_COL_` | `SUBSCRIPTION_KEY`, `API_USER`, `API_KEY` |
| Disbursements | `MOMO_DIS_` | `SUBSCRIPTION_KEY`, `API_USER`, `API_KEY` |
| Remittance    | `MOMO_REM_` | `SUBSCRIPTION_KEY`, `API_USER`, `API_KEY` |

> [!TIP]
> `.env` is gitignored. Run scripts with `uv run --env-file .env python your_script.py` to load it without exporting anything into your shell.

`MomoClient()` then builds each product client automatically from its environment variables the moment you touch it:

```python
import mtn_momo as momo

client = momo.MomoClient()
reference_id = client.collections.request_to_pay(
    amount="500",
    currency="ZMW",
    payer=momo.Party(party_id_type=momo.PartyIdType.MSISDN, party_id="256770000000"),
    payer_message="Invoice 123",
)
status = client.collections.wait_for_transaction(reference_id)
print(status.status.value)
```

```text
SUCCESSFUL
```

> [!IMPORTANT]
> Touching a product whose environment variables aren't set (e.g. `client.disbursements` with no `MOMO_DIS_*` vars) raises `MomoConfigError` immediately — there's no silent partial configuration.

All endpoints are available on both the sync `MomoClient`/`CollectionsClient` and the async `AsyncMomoClient`/`AsyncCollectionsClient`:

```python
import asyncio
import mtn_momo as momo


async def main() -> None:
    client = momo.AsyncMomoClient()
    reference_id = await client.collections.request_to_pay(
        amount="500",
        currency="ZMW",
        payer=momo.Party(party_id_type=momo.PartyIdType.MSISDN, party_id="256770000000"),
    )
    status = await client.collections.wait_for_transaction(reference_id)
    print(status.status.value)


asyncio.run(main())
```

Disbursements and Remittance work the same way — `client.disbursements`/`client.remittance` build themselves from `MOMO_DIS_*`/`MOMO_REM_*`, and `transfer()` takes a `payee` instead of a `payer`:

```python
client = momo.MomoClient()
reference_id = client.disbursements.transfer(
    amount="1000",
    currency="ZMW",
    payee=momo.Party(party_id_type=momo.PartyIdType.MSISDN, party_id="256770000001"),
)
```

Balance and account-holder checks:

```python
balance = client.collections.get_balance()  # or get_balance("ZMW")
print(balance.available_balance, balance.currency)

is_active = client.collections.is_account_holder_active(
    momo.PartyIdType.MSISDN, "256770000000"
)
```

## Handling errors

If a request fails, the SDK raises a typed `MomoAPIError` subclass instead of a generic HTTP error, so you can match on what actually went wrong:

```python
from mtn_momo import MomoAPIError, NotEnoughFundsError, PayerNotFoundError, PollTimeoutError

try:
    client.collections.request_to_pay(...)
except PayerNotFoundError:
    ...
except NotEnoughFundsError:
    ...
except PollTimeoutError as e:
    print("still pending after timeout:", e.last_status)
except MomoAPIError as e:
    # Any other rejection from the MoMo API.
    print(e.status_code, e.error_code, e.raw_body)
```

## Configuration

### Explicit config instead of environment variables

Pass a `ProductConfig` directly for secrets from a vault, or to run multiple accounts in one process — it takes priority over any environment variables for that product:

```python
config = momo.ProductConfig(
    base_url="https://sandbox.momodeveloper.mtn.com",
    subscription_key="...", api_user="...", api_key="...",
)
client = momo.MomoClient(collections=config)
```

`ProductConfig.from_env(prefix)` is also available directly, if you want the same environment-loading behavior `MomoClient()` uses without the lazy client wrapper.

### Long-running processes

The examples above skip explicit cleanup, since a one-shot script's connections close when the process exits. In a long-running service, use `MomoClient()`/`AsyncMomoClient()` as a context manager so idle HTTP connections get closed properly:

```python
with momo.MomoClient() as client:
    ...
```

## Examples

Runnable scripts in [`examples/`](examples/):

| Script                                                          | Demonstrates                           |
| --------------------------------------------------------------- | -------------------------------------- |
| [`sync_request_to_pay.py`](examples/sync_request_to_pay.py)     | Collections, sync client               |
| [`async_request_to_pay.py`](examples/async_request_to_pay.py)   | Collections, async client              |
| [`disbursement_transfer.py`](examples/disbursement_transfer.py) | Disbursements payout                   |
| [`sandbox_provisioning.py`](examples/sandbox_provisioning.py)   | `SandboxProvisioner` used as a library |
| [`poll_until_complete.py`](examples/poll_until_complete.py)     | Custom poll timing/backoff             |

## Verifying against a real sandbox

Once you have sandbox credentials, run the live smoke tests:

```bash
uv run --env-file .env pytest -m sandbox -v
```

These tests are skipped by default and excluded from normal CI; run them explicitly, or trigger the **Sandbox Smoke Test** GitHub Actions workflow with the equivalent secrets configured.

## Development

```bash
uv sync --dev
uv run pre-commit install
uv run pytest                          # unit tests only, no network
uv run ruff check .
uv run ruff format --check
uv run mypy src
```

## Resources

- [MoMo Developer Portal](https://momodeveloper.mtn.com/)
- [MoMo API documentation](https://momodeveloper.mtn.com/api-documentation/)
