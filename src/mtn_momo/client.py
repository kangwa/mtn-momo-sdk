"""Composed clients tying Collections, Disbursements, and Remittance together.

Each product client is built lazily on first access: pass an explicit
ProductConfig to the constructor to configure a product directly, or leave it
unset and it's built from that product's environment variables the moment you
touch client.collections / .disbursements / .remittance (MOMO_COL_*,
MOMO_DIS_*, MOMO_REM_* respectively). Accessing a product with neither an
explicit config nor its environment variables set raises MomoConfigError.
"""

from __future__ import annotations

from typing import Any

from mtn_momo.config import ProductConfig
from mtn_momo.products.collections import AsyncCollectionsClient, CollectionsClient
from mtn_momo.products.disbursements import AsyncDisbursementsClient, DisbursementsClient
from mtn_momo.products.remittance import AsyncRemittanceClient, RemittanceClient


class MomoClient:
    """Composes the sync Collections, Disbursements, and Remittance clients.

    See module docstring for the lazy env-var-driven construction behavior.
    """

    def __init__(
        self,
        *,
        collections: ProductConfig | None = None,
        disbursements: ProductConfig | None = None,
        remittance: ProductConfig | None = None,
    ) -> None:
        self._collections_config = collections
        self._disbursements_config = disbursements
        self._remittance_config = remittance
        self._collections: CollectionsClient | None = None
        self._disbursements: DisbursementsClient | None = None
        self._remittance: RemittanceClient | None = None

    @property
    def collections(self) -> CollectionsClient:
        """The Collections client, built from MOMO_COL_* env vars on first access."""
        if self._collections is None:
            config = self._collections_config or ProductConfig.from_env("MOMO_COL_")
            self._collections = CollectionsClient(config)
        return self._collections

    @property
    def disbursements(self) -> DisbursementsClient:
        """The Disbursements client, built from MOMO_DIS_* env vars on first access."""
        if self._disbursements is None:
            config = self._disbursements_config or ProductConfig.from_env("MOMO_DIS_")
            self._disbursements = DisbursementsClient(config)
        return self._disbursements

    @property
    def remittance(self) -> RemittanceClient:
        """The Remittance client, built from MOMO_REM_* env vars on first access."""
        if self._remittance is None:
            config = self._remittance_config or ProductConfig.from_env("MOMO_REM_")
            self._remittance = RemittanceClient(config)
        return self._remittance

    def close(self) -> None:
        """Close whichever product clients have actually been built."""
        for client in (self._collections, self._disbursements, self._remittance):
            if client is not None:
                client.close()

    def __enter__(self) -> MomoClient:
        return self

    def __exit__(self, *exc: Any) -> None:
        self.close()


class AsyncMomoClient:
    """Composes the async Collections, Disbursements, and Remittance clients.

    See module docstring for the lazy env-var-driven construction behavior.
    """

    def __init__(
        self,
        *,
        collections: ProductConfig | None = None,
        disbursements: ProductConfig | None = None,
        remittance: ProductConfig | None = None,
    ) -> None:
        self._collections_config = collections
        self._disbursements_config = disbursements
        self._remittance_config = remittance
        self._collections: AsyncCollectionsClient | None = None
        self._disbursements: AsyncDisbursementsClient | None = None
        self._remittance: AsyncRemittanceClient | None = None

    @property
    def collections(self) -> AsyncCollectionsClient:
        """The Collections client, built from MOMO_COL_* env vars on first access."""
        if self._collections is None:
            config = self._collections_config or ProductConfig.from_env("MOMO_COL_")
            self._collections = AsyncCollectionsClient(config)
        return self._collections

    @property
    def disbursements(self) -> AsyncDisbursementsClient:
        """The Disbursements client, built from MOMO_DIS_* env vars on first access."""
        if self._disbursements is None:
            config = self._disbursements_config or ProductConfig.from_env("MOMO_DIS_")
            self._disbursements = AsyncDisbursementsClient(config)
        return self._disbursements

    @property
    def remittance(self) -> AsyncRemittanceClient:
        """The Remittance client, built from MOMO_REM_* env vars on first access."""
        if self._remittance is None:
            config = self._remittance_config or ProductConfig.from_env("MOMO_REM_")
            self._remittance = AsyncRemittanceClient(config)
        return self._remittance

    async def aclose(self) -> None:
        """Close whichever product clients have actually been built."""
        for client in (self._collections, self._disbursements, self._remittance):
            if client is not None:
                await client.aclose()

    async def __aenter__(self) -> AsyncMomoClient:
        return self

    async def __aexit__(self, *exc: Any) -> None:
        await self.aclose()
