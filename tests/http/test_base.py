import httpx
import pytest

from mtn_momo.exceptions import (
    AuthenticationError,
    DuplicateReferenceError,
    NotEnoughFundsError,
    PayerNotFoundError,
    ResourceNotFoundError,
    ServerError,
    UnknownMomoAPIError,
    ValidationError,
)
from mtn_momo.http.base import PreparedRequest, raise_for_response


class TestRaiseForResponse:
    def test_success_does_not_raise(self) -> None:
        raise_for_response(httpx.Response(200, json={"status": "PENDING"}))

    def test_409_raises_duplicate_reference_error(self) -> None:
        with pytest.raises(DuplicateReferenceError):
            raise_for_response(httpx.Response(409))

    def test_401_raises_authentication_error(self) -> None:
        with pytest.raises(AuthenticationError):
            raise_for_response(httpx.Response(401))

    def test_404_raises_resource_not_found_error(self) -> None:
        with pytest.raises(ResourceNotFoundError):
            raise_for_response(httpx.Response(404))

    def test_known_error_code_maps_to_specific_exception(self) -> None:
        response = httpx.Response(400, json={"code": "PAYER_NOT_FOUND", "message": "no payer"})
        with pytest.raises(PayerNotFoundError) as exc_info:
            raise_for_response(response)
        assert exc_info.value.error_code == "PAYER_NOT_FOUND"
        assert exc_info.value.status_code == 400

    def test_another_known_error_code_maps_correctly(self) -> None:
        response = httpx.Response(
            400, json={"code": "NOT_ENOUGH_FUNDS", "message": "insufficient balance"}
        )
        with pytest.raises(NotEnoughFundsError):
            raise_for_response(response)

    def test_unrecognized_error_code_raises_unknown_momo_api_error(self) -> None:
        response = httpx.Response(400, json={"code": "SOMETHING_NEW", "message": "?"})
        with pytest.raises(UnknownMomoAPIError) as exc_info:
            raise_for_response(response)
        assert exc_info.value.error_code == "SOMETHING_NEW"

    def test_no_body_and_5xx_raises_server_error(self) -> None:
        with pytest.raises(ServerError):
            raise_for_response(httpx.Response(500))

    def test_no_body_and_4xx_raises_validation_error(self) -> None:
        with pytest.raises(ValidationError):
            raise_for_response(httpx.Response(400))


class TestPreparedRequest:
    def test_holds_request_fields(self) -> None:
        request = PreparedRequest(
            method="POST",
            url="https://sandbox.momodeveloper.mtn.com/collection/v1_0/requesttopay",
            headers={"Authorization": "Bearer abc"},
            json={"amount": "500"},
        )
        assert request.method == "POST"
        assert request.json == {"amount": "500"}
