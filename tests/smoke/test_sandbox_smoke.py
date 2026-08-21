"""Smoke tests against MTN's real sandbox.

Requires live MOMO_* env vars per product; each product's tests are skipped
independently if its credentials aren't set. These exist to catch drift
between this SDK's modeled request/response shapes and MoMo's actual API —
the models were built from documented behavior, not a live Swagger export,
so this is the first real verification point for that.

Run explicitly with: uv run pytest -m sandbox -v
"""

import os

import pytest

from mtn_momo.config import ProductConfig
from mtn_momo.constants import PartyIdType
from mtn_momo.models.common import Party
from mtn_momo.products.collections import CollectionsClient
from mtn_momo.products.disbursements import DisbursementsClient
from mtn_momo.products.remittance import RemittanceClient
from mtn_momo.provisioning import SandboxProvisioner

pytestmark = pytest.mark.sandbox

# Adjust via env var if your sandbox account uses a different test MSISDN.
# `or` (not a plain .get default) so an empty-but-set var, e.g. from a .env
# template, still falls back instead of silently sending an empty party_id.
_TEST_MSISDN = os.environ.get("MOMO_SANDBOX_TEST_MSISDN") or "46733123450"


def _has_product_env(prefix: str) -> bool:
    return all(
        os.environ.get(f"{prefix}{name}") for name in ("SUBSCRIPTION_KEY", "API_USER", "API_KEY")
    )


@pytest.mark.skipif(not _has_product_env("MOMO_COL_"), reason="missing MOMO_COL_* env vars")
class TestCollectionsSandboxSmoke:
    def test_request_to_pay_and_check_status(self) -> None:
        config = ProductConfig.from_env("MOMO_COL_")
        with CollectionsClient(config) as client:
            reference_id = client.request_to_pay(
                amount="500",
                currency="EUR",
                payer=Party(party_id_type=PartyIdType.MSISDN, party_id=_TEST_MSISDN),
                payer_message="mtn-momo smoke test",
            )
            status = client.get_transaction_status(reference_id)
            assert status.status is not None

    def test_get_balance(self) -> None:
        config = ProductConfig.from_env("MOMO_COL_")
        with CollectionsClient(config) as client:
            balance = client.get_balance()
            assert balance.currency

    def test_is_account_holder_active(self) -> None:
        config = ProductConfig.from_env("MOMO_COL_")
        with CollectionsClient(config) as client:
            # Just confirming the call succeeds and parses — sandbox test
            # accounts aren't guaranteed to report active either way.
            client.is_account_holder_active(PartyIdType.MSISDN, _TEST_MSISDN)


@pytest.mark.skipif(not _has_product_env("MOMO_DIS_"), reason="missing MOMO_DIS_* env vars")
class TestDisbursementsSandboxSmoke:
    def test_transfer_and_check_status(self) -> None:
        config = ProductConfig.from_env("MOMO_DIS_")
        with DisbursementsClient(config) as client:
            reference_id = client.transfer(
                amount="500",
                currency="EUR",
                payee=Party(party_id_type=PartyIdType.MSISDN, party_id=_TEST_MSISDN),
            )
            status = client.get_transaction_status(reference_id)
            assert status.status is not None


@pytest.mark.skipif(not _has_product_env("MOMO_REM_"), reason="missing MOMO_REM_* env vars")
class TestRemittanceSandboxSmoke:
    def test_transfer_and_check_status(self) -> None:
        config = ProductConfig.from_env("MOMO_REM_")
        with RemittanceClient(config) as client:
            reference_id = client.transfer(
                amount="500",
                currency="EUR",
                payee=Party(party_id_type=PartyIdType.MSISDN, party_id=_TEST_MSISDN),
            )
            status = client.get_transaction_status(reference_id)
            assert status.status is not None


@pytest.mark.skipif(
    not os.environ.get("MOMO_SANDBOX_SUBSCRIPTION_KEY"),
    reason="missing MOMO_SANDBOX_SUBSCRIPTION_KEY env var",
)
class TestProvisioningSandboxSmoke:
    def test_provision_creates_real_credentials(self) -> None:
        subscription_key = os.environ["MOMO_SANDBOX_SUBSCRIPTION_KEY"]
        with SandboxProvisioner(subscription_key) as provisioner:
            credentials = provisioner.provision(callback_host="https://example.test/callback")
            assert credentials.api_user
            assert credentials.api_key
