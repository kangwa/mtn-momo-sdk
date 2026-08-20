# Changelog

All notable changes to this project are documented here.
Format based on [Keep a Changelog](https://keepachangelog.com/).

## [Unreleased]

### Added

- Project skeleton: pyproject.toml, tooling (ruff/mypy/pytest), CI, docs scaffold.
- Request/response models (Party, RequestToPayRequest, TransferRequest, TransactionStatus,
  BalanceInfo, TokenResponse, ApiUserInfo, BasicUserInfo) and exception hierarchy
  (MomoError, MomoAPIError, and per-error-code subclasses).
