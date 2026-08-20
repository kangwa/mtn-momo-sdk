"""Composed clients tying Collections, Disbursements, and Remittance together."""

from __future__ import annotations

from typing import Any

from mtn_momo.config import ProductConfig
from mtn_momo.products.collections import AsyncCollectionsClient, CollectionsClient
from mtn_momo.products.disbursements import AsyncDisbursementsClient, DisbursementsClient
from mtn_momo.products.remittance import AsyncRemittanceClient, RemittanceClient


class MomoClient:
    """Composes the sync Collections, Disbursements, and Remittance clients.

    Each product is optional — pass a ProductConfig only for the products you use;
    the rest stay None.
    """

    def __init__(
        self,
        *,
        collections: ProductConfig | None = None,
        disbursements: ProductConfig | None = None,
        remittance: ProductConfig | None = None,
    ) -> None:
        self.collections = CollectionsClient(collections) if collections else None
        self.disbursements = DisbursementsClient(disbursements) if disbursements else None
        self.remittance = RemittanceClient(remittance) if remittance else None

    def close(self) -> None:
        """Close every configured product client's HTTP transport."""
        for client in (self.collections, self.disbursements, self.remittance):
            if client is not None:
                client.close()

    def __enter__(self) -> MomoClient:
        return self

    def __exit__(self, *exc: Any) -> None:
        self.close()


class AsyncMomoClient:
    """Composes the async Collections, Disbursements, and Remittance clients.

    Each product is optional — pass a ProductConfig only for the products you use;
    the rest stay None.
    """

    def __init__(
        self,
        *,
        collections: ProductConfig | None = None,
        disbursements: ProductConfig | None = None,
        remittance: ProductConfig | None = None,
    ) -> None:
        self.collections = AsyncCollectionsClient(collections) if collections else None
        self.disbursements = AsyncDisbursementsClient(disbursements) if disbursements else None
        self.remittance = AsyncRemittanceClient(remittance) if remittance else None

    async def aclose(self) -> None:
        """Close every configured product client's HTTP transport."""
        for client in (self.collections, self.disbursements, self.remittance):
            if client is not None:
                await client.aclose()

    async def __aenter__(self) -> AsyncMomoClient:
        return self

    async def __aexit__(self, *exc: Any) -> None:
        await self.aclose()
