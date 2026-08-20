import json

import httpx
import pytest
import respx

from mtn_momo.config import ProductConfig
from mtn_momo.constants import PartyIdType, TransactionStatusValue
from mtn_momo.exceptions import NotEnoughFundsError
from mtn_momo.models.common import Party
from mtn_momo.products.remittance import AsyncRemittanceClient

BASE_URL = "https://sandbox.momodeveloper.mtn.com"


@pytest.fixture
def config() -> ProductConfig:
    return ProductConfig(
        base_url=BASE_URL,
        subscription_key="sub-key",
        api_user="api-user",
        api_key="api-key",
    )


def _mock_token() -> None:
    respx.post(f"{BASE_URL}/remittance/token/").mock(
        return_value=httpx.Response(
            200,
            json={"access_token": "abc123", "token_type": "access_token", "expires_in": 3600},
        )
    )


class TestAsyncRemittanceClient:
    @respx.mock
    async def test_happy_path_token_then_transfer_then_status(self, config: ProductConfig) -> None:
        _mock_token()
        transfer_route = respx.post(f"{BASE_URL}/remittance/v1_0/transfer").mock(
            return_value=httpx.Response(202)
        )

        client = AsyncRemittanceClient(config)
        reference_id = await client.transfer(
            amount="500",
            currency="USD",
            payee=Party(party_id_type=PartyIdType.MSISDN, party_id="260960000000"),
        )

        status_route = respx.get(f"{BASE_URL}/remittance/v1_0/transfer/{reference_id}").mock(
            return_value=httpx.Response(200, json={"status": "SUCCESSFUL"})
        )
        status = await client.get_transaction_status(reference_id)

        assert transfer_route.called
        assert status_route.called
        assert status.status == TransactionStatusValue.SUCCESSFUL

    @respx.mock
    async def test_sends_expected_headers_and_body(self, config: ProductConfig) -> None:
        _mock_token()
        transfer_route = respx.post(f"{BASE_URL}/remittance/v1_0/transfer").mock(
            return_value=httpx.Response(202)
        )

        client = AsyncRemittanceClient(config)
        reference_id = await client.transfer(
            amount="500",
            currency="USD",
            payee=Party(party_id_type=PartyIdType.MSISDN, party_id="260960000000"),
        )

        request = transfer_route.calls.last.request
        assert request.headers["X-Reference-Id"] == reference_id
        assert request.headers["Authorization"] == "Bearer abc123"
        assert json.loads(request.content) == {
            "amount": "500",
            "currency": "USD",
            "externalId": reference_id,
            "payee": {"partyIdType": "MSISDN", "partyId": "260960000000"},
            "payerMessage": "",
            "payeeNote": "",
        }

    @respx.mock
    async def test_not_enough_funds_raises(self, config: ProductConfig) -> None:
        _mock_token()
        respx.post(f"{BASE_URL}/remittance/v1_0/transfer").mock(
            return_value=httpx.Response(
                400, json={"code": "NOT_ENOUGH_FUNDS", "message": "insufficient balance"}
            )
        )

        client = AsyncRemittanceClient(config)
        with pytest.raises(NotEnoughFundsError):
            await client.transfer(
                amount="500",
                currency="USD",
                payee=Party(party_id_type=PartyIdType.MSISDN, party_id="260960000000"),
            )
