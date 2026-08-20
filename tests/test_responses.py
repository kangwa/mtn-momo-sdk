from mtn_momo.constants import TransactionStatusValue
from mtn_momo.models.responses import TransactionStatus


class TestTransactionStatus:
    def test_parses_pending(self) -> None:
        status = TransactionStatus.model_validate({"status": "PENDING"})
        assert status.status == TransactionStatusValue.PENDING
        assert status.financial_transaction_id is None

    def test_parses_failed_with_reason(self) -> None:
        status = TransactionStatus.model_validate(
            {
                "status": "FAILED",
                "reason": {"code": "PAYER_NOT_FOUND", "message": "Payer not found"},
            }
        )

        assert status.reason is not None
        assert status.reason.code == "PAYER_NOT_FOUND"
