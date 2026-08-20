# Changelog

All notable changes to this project are documented here.
Format based on [Keep a Changelog](https://keepachangelog.com/).

## [Unreleased]

### Added

- Project skeleton: pyproject.toml, tooling (ruff/mypy/pytest), CI, docs scaffold.
- Request/response models (Party, RequestToPayRequest, TransferRequest, TransactionStatus,
  BalanceInfo, TokenResponse, ApiUserInfo, BasicUserInfo) and exception hierarchy
  (MomoError, MomoAPIError, and per-error-code subclasses).
- ProductConfig for per-product credentials/settings, with env var loading via from_env().
- Pure token cache (TokenCache/CachedToken) with expiry leeway and injectable clock.
- PreparedRequest and raise_for_response() for shared, transport-agnostic request/error
  handling used by both the sync and async clients.
- CollectionsClient/AsyncCollectionsClient: request_to_pay, get_transaction_status
- _BaseProductCore + _SyncExecMixin/_AsyncExecMixin sharing all request/response
  logic between sync and async, differing only in I/O execution
- SyncHttpTransport/AsyncHttpTransport wrapping httpx, with network errors
  mapped to MomoConnectionError/MomoTimeoutError
- Sync/async Disbursements and Remittance clients (transfer(), get_transaction_status()),
  reusing the shared product core and exec mixins built for Collections.
- Added polling helpers to polling clients
- MomoClient/AsyncMomoClient composing Collections, Disbursements, and Remittance under
  one entry point, each product optional.
- Curated top-level `mtn_momo` package re-exports (client, config, models, exceptions,
  polling), so `import mtn_momo as momo` gives a full public surface.
- SandboxProvisioner/AsyncSandboxProvisioner for creating sandbox API users/keys
  (subscription-key-only auth, no bearer token required).
- mtn-momo-provision CLI entry point for provisioning sandbox credentials from the
  command line.
