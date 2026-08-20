import json
import threading
import time

import httpx
import pytest
import respx

from mtn_momo.config import ProductConfig
from mtn_momo.constants import PartyIdType, TransactionStatusValue
from mtn_momo.exceptions import PayerNotFoundError, PollTimeoutError
from mtn_momo.models.common import Party
from mtn_momo.polling import PollConfig
from mtn_momo.products.collections import CollectionsClient

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


class TestCollectionsClient:
    @respx.mock
    def test_happy_path_token_then_request_then_status(self, config: ProductConfig) -> None:
        _mock_token()
        payment_route = respx.post(f"{BASE_URL}/collection/v1_0/requesttopay").mock(
            return_value=httpx.Response(202)
        )

        client = CollectionsClient(config)
        reference_id = client.request_to_pay(
            amount="500",
            currency="EUR",
            payer=Party(party_id_type=PartyIdType.MSISDN, party_id="260960000000"),
        )

        status_route = respx.get(f"{BASE_URL}/collection/v1_0/requesttopay/{reference_id}").mock(
            return_value=httpx.Response(200, json={"status": "SUCCESSFUL"})
        )
        status = client.get_transaction_status(reference_id)

        assert payment_route.called
        assert status_route.called
        assert status.status == TransactionStatusValue.SUCCESSFUL

    @respx.mock
    def test_reuses_cached_token_across_calls(self, config: ProductConfig) -> None:
        token_route = respx.post(f"{BASE_URL}/collection/token/").mock(
            return_value=httpx.Response(
                200,
                json={"access_token": "abc123", "token_type": "access_token", "expires_in": 3600},
            )
        )
        respx.post(f"{BASE_URL}/collection/v1_0/requesttopay").mock(
            return_value=httpx.Response(202)
        )

        client = CollectionsClient(config)
        reference_id = client.request_to_pay(
            amount="500",
            currency="EUR",
            payer=Party(party_id_type=PartyIdType.MSISDN, party_id="260960000000"),
        )

        respx.get(f"{BASE_URL}/collection/v1_0/requesttopay/{reference_id}").mock(
            return_value=httpx.Response(200, json={"status": "PENDING"})
        )
        client.get_transaction_status(reference_id)

        assert token_route.call_count == 1

    @respx.mock
    def test_sends_expected_headers_and_body(self, config: ProductConfig) -> None:
        _mock_token()
        payment_route = respx.post(f"{BASE_URL}/collection/v1_0/requesttopay").mock(
            return_value=httpx.Response(202)
        )

        client = CollectionsClient(config)
        reference_id = client.request_to_pay(
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
    def test_payer_not_found_raises(self, config: ProductConfig) -> None:
        _mock_token()
        respx.post(f"{BASE_URL}/collection/v1_0/requesttopay").mock(
            return_value=httpx.Response(
                400, json={"code": "PAYER_NOT_FOUND", "message": "no payer"}
            )
        )

        client = CollectionsClient(config)
        with pytest.raises(PayerNotFoundError):
            client.request_to_pay(
                amount="500",
                currency="EUR",
                payer=Party(party_id_type=PartyIdType.MSISDN, party_id="260960000000"),
            )

    def test_close_closes_transport(self, config: ProductConfig) -> None:
        client = CollectionsClient(config)
        client.close()
        assert client._transport._client.is_closed

    def test_context_manager_closes_transport_on_exit(self, config: ProductConfig) -> None:
        with CollectionsClient(config) as client:
            pass
        assert client._transport._client.is_closed

    @respx.mock
    def test_concurrent_ensure_token_only_fetches_once(self, config: ProductConfig) -> None:
        call_count = 0

        def _token_response(request: httpx.Request) -> httpx.Response:
            nonlocal call_count
            call_count += 1
            time.sleep(0.05)
            return httpx.Response(
                200,
                json={"access_token": "abc123", "token_type": "access_token", "expires_in": 3600},
            )

        respx.post(f"{BASE_URL}/collection/token/").mock(side_effect=_token_response)
        respx.post(f"{BASE_URL}/collection/v1_0/requesttopay").mock(
            return_value=httpx.Response(202)
        )

        client = CollectionsClient(config)

        def _make_request() -> None:
            client.request_to_pay(
                amount="500",
                currency="EUR",
                payer=Party(party_id_type=PartyIdType.MSISDN, party_id="260960000000"),
            )

        threads = [threading.Thread(target=_make_request) for _ in range(5)]
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join()

        assert call_count == 1

    @respx.mock
    def test_wait_for_transaction_polls_until_successful(self, config: ProductConfig) -> None:
        _mock_token()
        respx.post(f"{BASE_URL}/collection/v1_0/requesttopay").mock(
            return_value=httpx.Response(202)
        )

        client = CollectionsClient(config)
        reference_id = client.request_to_pay(
            amount="500",
            currency="EUR",
            payer=Party(party_id_type=PartyIdType.MSISDN, party_id="260960000000"),
        )

        status_route = respx.get(f"{BASE_URL}/collection/v1_0/requesttopay/{reference_id}")
        status_route.side_effect = [
            httpx.Response(200, json={"status": "PENDING"}),
            httpx.Response(200, json={"status": "SUCCESSFUL"}),
        ]

        status = client.wait_for_transaction(
            reference_id, poll_config=PollConfig(interval=0.01, timeout=5.0)
        )

        assert status.status == TransactionStatusValue.SUCCESSFUL
        assert status_route.call_count == 2

    @respx.mock
    def test_wait_for_transaction_raises_on_timeout(self, config: ProductConfig) -> None:
        _mock_token()
        respx.post(f"{BASE_URL}/collection/v1_0/requesttopay").mock(
            return_value=httpx.Response(202)
        )

        client = CollectionsClient(config)
        reference_id = client.request_to_pay(
            amount="500",
            currency="EUR",
            payer=Party(party_id_type=PartyIdType.MSISDN, party_id="260960000000"),
        )

        respx.get(f"{BASE_URL}/collection/v1_0/requesttopay/{reference_id}").mock(
            return_value=httpx.Response(200, json={"status": "PENDING"})
        )

        with pytest.raises(PollTimeoutError):
            client.wait_for_transaction(
                reference_id, poll_config=PollConfig(interval=0.01, timeout=0.02)
            )

    @respx.mock
    def test_get_balance_without_currency(self, config: ProductConfig) -> None:
        _mock_token()
        route = respx.get(f"{BASE_URL}/collection/v1_0/account/balance").mock(
            return_value=httpx.Response(200, json={"availableBalance": "1000", "currency": "EUR"})
        )

        client = CollectionsClient(config)
        balance = client.get_balance()

        assert route.called
        assert balance.available_balance == "1000"
        assert balance.currency == "EUR"

    @respx.mock
    def test_get_balance_with_currency(self, config: ProductConfig) -> None:
        _mock_token()
        route = respx.get(f"{BASE_URL}/collection/v1_0/account/balance/EUR").mock(
            return_value=httpx.Response(200, json={"availableBalance": "1000", "currency": "EUR"})
        )

        client = CollectionsClient(config)
        client.get_balance("EUR")

        assert route.called

    @respx.mock
    def test_is_account_holder_active_true(self, config: ProductConfig) -> None:
        _mock_token()
        respx.get(f"{BASE_URL}/collection/v1_0/accountholder/MSISDN/260960000000/active").mock(
            return_value=httpx.Response(200, json={"result": True})
        )

        client = CollectionsClient(config)
        is_active = client.is_account_holder_active(PartyIdType.MSISDN, "260960000000")

        assert is_active is True

    @respx.mock
    def test_is_account_holder_active_false(self, config: ProductConfig) -> None:
        _mock_token()
        respx.get(f"{BASE_URL}/collection/v1_0/accountholder/MSISDN/260960000000/active").mock(
            return_value=httpx.Response(200, json={"result": False})
        )

        client = CollectionsClient(config)
        is_active = client.is_account_holder_active(PartyIdType.MSISDN, "260960000000")

        assert is_active is False
