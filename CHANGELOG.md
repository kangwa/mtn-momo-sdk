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
