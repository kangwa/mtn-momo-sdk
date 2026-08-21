from __future__ import annotations

import os
from dataclasses import dataclass

from mtn_momo.constants import SANDBOX_BASE_URL
from mtn_momo.exceptions import MomoConfigError


@dataclass(frozen=True)
class ProductConfig:
    """Credentials and connection settings for one MoMo product.

    One ProductConfig covers a single product (Collections, Disbursements or Remittance).
    Each has its own subscription key and usually its own sandbox API key/user pair.

    Attributes:
        base_url: The API base URL, e.g. https://sandbox.momodeveloper.mtn.com.
        subscription_key: The Ocp-Apim-Subscription-Key for this product.
        api_user: The provisioned API user UUID.
        api_key: The provisioned API key.
        target_environment: The X-Target-Environment header value, e.g. "sandbox".
        timeout: Request timeout in seconds.
    """

    base_url: str
    subscription_key: str
    api_user: str
    api_key: str
    target_environment: str = "sandbox"
    timeout: float = 10.0

    def __post_init__(self) -> None:
        for field_name in ("base_url", "subscription_key", "api_user", "api_key"):
            if not getattr(self, field_name):
                raise MomoConfigError(f"{field_name} must not be empty")

    @classmethod
    def from_env(cls, prefix: str, *, base_url: str = SANDBOX_BASE_URL) -> ProductConfig:
        """Build a ProductConfig from environment variables.

        Reads `{prefix}SUBSCRIPTION_KEY`, `{prefix}API_USER`, and `{prefix}API_KEY`
        (all required), plus optional `{prefix}BASE_URL` and `{prefix}TARGET_ENVIRONMENT`.

        Args:
            prefix: Env var prefix, e.g. "MOMO_COL_".
            base_url: The API base URL to use if `{prefix}BASE_URL` isn't set.

        Raises:
            MomoConfigError: If a required environment variable is missing.
        """

        def _require(name: str) -> str:
            value = os.environ.get(f"{prefix}{name}")
            if not value:
                raise MomoConfigError(f"missing required environment variable: {prefix}{name}")
            return value

        return cls(
            base_url=os.environ.get(f"{prefix}BASE_URL") or base_url,
            subscription_key=_require("SUBSCRIPTION_KEY"),
            api_user=_require("API_USER"),
            api_key=_require("API_KEY"),
            target_environment=os.environ.get(f"{prefix}TARGET_ENVIRONMENT") or "sandbox",
        )
