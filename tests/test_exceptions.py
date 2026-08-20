import pytest

from mtn_momo.exceptions import (
    ERROR_CODE_MAP,
    ApprovalRejectedError,
    AuthenticationError,
    DuplicateReferenceError,
    ExpiredError,
    InternalProcessingError,
    MomoAPIError,
    MomoConfigError,
    MomoConnectionError,
    MomoError,
    MomoTimeoutError,
    NotAllowedError,
    NotEnoughFundsError,
    PayeeNotFoundError,
    PayerNotFoundError,
    PollTimeoutError,
    ResourceNotFoundError,
    ServerError,
    UnknownMomoAPIError,
    ValidationError,
)


class TestMomoErrorHierarchy:
    @pytest.mark.parametrize(
        "exc_type",
        [MomoConfigError, MomoConnectionError, MomoTimeoutError, PollTimeoutError, MomoAPIError],
    )
    def test_is_a_momo_error(self, exc_type: type[MomoError]) -> None:
        assert issubclass(exc_type, MomoError)

    @pytest.mark.parametrize(
        "exc_type",
        [
            AuthenticationError,
            DuplicateReferenceError,
            ResourceNotFoundError,
            ValidationError,
            PayerNotFoundError,
            PayeeNotFoundError,
            NotAllowedError,
            NotEnoughFundsError,
            ExpiredError,
            ApprovalRejectedError,
            InternalProcessingError,
            ServerError,
            UnknownMomoAPIError,
        ],
    )
    def test_is_a_momo_api_error(self, exc_type: type[MomoAPIError]) -> None:
        assert issubclass(exc_type, MomoAPIError)


class TestMomoAPIError:
    def test_carries_context(self) -> None:
        error = MomoAPIError(
            "kaboom",
            status_code=400,
            error_code="PAYER_NOT_FOUND",
            raw_body={"x": 1},
        )
        assert error.status_code == 400
        assert error.error_code == "PAYER_NOT_FOUND"
        assert error.raw_body == {"x": 1}

    def test_error_code_and_raw_body_default_to_none(self) -> None:
        error = MomoAPIError("kaboom", status_code=500)
        assert error.error_code is None
        assert error.raw_body is None


class TestPollTimeoutError:
    def test_carries_last_status(self) -> None:
        error = PollTimeoutError("gave up", last_status="PENDING")
        assert error.last_status == "PENDING"

    def test_last_status_defaults_to_none(self) -> None:
        error = PollTimeoutError("gave up")
        assert error.last_status is None


class TestErrorCodeMap:
    @pytest.mark.parametrize(("code", "exc_type"), list(ERROR_CODE_MAP.items()))
    def test_maps_code_to_subclass_of_momo_api_error(
        self, code: str, exc_type: type[MomoAPIError]
    ) -> None:
        assert issubclass(exc_type, MomoAPIError)

    def test_resolves_payer_not_found(self) -> None:
        assert ERROR_CODE_MAP["PAYER_NOT_FOUND"] is PayerNotFoundError
