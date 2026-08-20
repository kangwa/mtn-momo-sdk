import asyncio
import json

import httpx
import pytest
import respx

from mtn_momo.config import ProductConfig
from mtn_momo.constants import PartyIdType, TransactionStatusValue
from mtn_momo.exceptions import PayerNotFoundError
from mtn_momo.models.common import Party
from mtn_momo.products.collections import AsyncCollectionsClient

BASE_URL = "https://sandbox.momodeveloper.mtn.com"


@pytest.fixture
def config() -> ProductConfig:
    return ProductConfig(
        base_url=BASE_URL,
        subscription_key="sub-key",
        api_user="api-user",
        api_key="api-key",
    )


def _mock_token(status_code: int = 200) -> None:
    respx.post(f"{BASE_URL}/collection/token/").mock(
        return_value=httpx.Response(
            status_code,
            json={"access_token": "abc123", "token_type": "access_token", "expires_in": 3600},
        )
    )


class TestAsyncCollectionsClient:
    @respx.mock
    async def test_happy_path_token_then_request_then_status(self, config: ProductConfig) -> None:
        _mock_token()
        payment_route = respx.post(f"{BASE_URL}/collection/v1_0/requesttopay").mock(
            return_value=httpx.Response(202)
        )

        client = AsyncCollectionsClient(config)
        reference_id = await client.request_to_pay(
            amount="500",
            currency="EUR",
            payer=Party(party_id_type=PartyIdType.MSISDN, party_id="260960000000"),
        )

        status_route = respx.get(f"{BASE_URL}/collection/v1_0/requesttopay/{reference_id}").mock(
            return_value=httpx.Response(200, json={"status": "SUCCESSFUL"})
        )
        status = await client.get_transaction_status(reference_id)

        assert payment_route.called
        assert status_route.called
        assert status.status == TransactionStatusValue.SUCCESSFUL

    @respx.mock
    async def test_reuses_cached_token_across_calls(self, config: ProductConfig) -> None:
        token_route = respx.post(f"{BASE_URL}/collection/token/").mock(
            return_value=httpx.Response(
                200,
                json={"access_token": "abc123", "token_type": "access_token", "expires_in": 3600},
            )
        )
        respx.post(f"{BASE_URL}/collection/v1_0/requesttopay").mock(
            return_value=httpx.Response(202)
        )

        client = AsyncCollectionsClient(config)
        reference_id = await client.request_to_pay(
            amount="500",
            currency="EUR",
            payer=Party(party_id_type=PartyIdType.MSISDN, party_id="260960000000"),
        )

        respx.get(f"{BASE_URL}/collection/v1_0/requesttopay/{reference_id}").mock(
            return_value=httpx.Response(200, json={"status": "PENDING"})
        )
        await client.get_transaction_status(reference_id)

        assert token_route.call_count == 1

    @respx.mock
    async def test_sends_expected_headers_and_body(self, config: ProductConfig) -> None:
        _mock_token()
        payment_route = respx.post(f"{BASE_URL}/collection/v1_0/requesttopay").mock(
            return_value=httpx.Response(202)
        )

        client = AsyncCollectionsClient(config)
        reference_id = await client.request_to_pay(
            amount="500",
            currency="EUR",
            payer=Party(party_id_type=PartyIdType.MSISDN, party_id="260960000000"),
            payer_message="Invoice 123",
        )

        request = payment_route.calls.last.request
        assert request.headers["X-Reference-Id"] == reference_id
        assert request.headers["X-Target-Environment"] == "sandbox"
        assert request.headers["Authorization"] == "Bearer abc123"
        assert json.loads(request.content) == {
            "amount": "500",
            "currency": "EUR",
            "externalId": reference_id,
            "payer": {"partyIdType": "MSISDN", "partyId": "260960000000"},
            "payerMessage": "Invoice 123",
            "payeeNote": "",
        }

    @respx.mock
    async def test_payer_not_found_raises(self, config: ProductConfig) -> None:
        _mock_token()
        respx.post(f"{BASE_URL}/collection/v1_0/requesttopay").mock(
            return_value=httpx.Response(
                400, json={"code": "PAYER_NOT_FOUND", "message": "no payer"}
            )
        )

        client = AsyncCollectionsClient(config)
        with pytest.raises(PayerNotFoundError):
            await client.request_to_pay(
                amount="500",
                currency="EUR",
                payer=Party(party_id_type=PartyIdType.MSISDN, party_id="260960000000"),
            )

    async def test_aclose_closes_transport(self, config: ProductConfig) -> None:
        client = AsyncCollectionsClient(config)
        await client.aclose()
        assert client._transport._client.is_closed

    async def test_context_manager_closes_transport_on_exit(self, config: ProductConfig) -> None:
        async with AsyncCollectionsClient(config) as client:
            pass
        assert client._transport._client.is_closed

    @respx.mock
    async def test_concurrent_ensure_token_only_fetches_once(self, config: ProductConfig) -> None:
        call_count = 0

        async def _token_response(request: httpx.Request) -> httpx.Response:
            nonlocal call_count
            call_count += 1
            await asyncio.sleep(0.05)
            return httpx.Response(
                200,
                json={"access_token": "abc123", "token_type": "access_token", "expires_in": 3600},
            )

        respx.post(f"{BASE_URL}/collection/token/").mock(side_effect=_token_response)
        respx.post(f"{BASE_URL}/collection/v1_0/requesttopay").mock(
            return_value=httpx.Response(202)
        )

        client = AsyncCollectionsClient(config)

        async def _make_request() -> None:
            await client.request_to_pay(
                amount="500",
                currency="EUR",
                payer=Party(party_id_type=PartyIdType.MSISDN, party_id="260960000000"),
            )

        await asyncio.gather(*(_make_request() for _ in range(5)))

        assert call_count == 1
