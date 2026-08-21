from mtn_momo.constants import TransactionStatusValue
from mtn_momo.models.responses import TransactionStatus


class TestTransactionStatus:
    def test_parses_pending(self) -> None:
        status = TransactionStatus.model_validate({"status": "PENDING"})
        assert status.status == TransactionStatusValue.PENDING
        assert status.financial_transaction_id is None

    def test_parses_failed_with_reason(self) -> None:
        # Verified against a real sandbox response: `reason` is a bare error
        # code string (e.g. "INTERNAL_PROCESSING_ERROR"), not a nested object.
        status = TransactionStatus.model_validate({"status": "FAILED", "reason": "PAYER_NOT_FOUND"})

        assert status.reason == "PAYER_NOT_FOUND"
