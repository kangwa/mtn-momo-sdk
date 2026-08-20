from mtn_momo.constants import PartyIdType
from mtn_momo.models.common import Party
from mtn_momo.models.requests import RequestToPayRequest


class TestRequestToPayRequest:
    def test_round_trip(self) -> None:
        req = RequestToPayRequest(
            amount="500",
            currency="ZMW",
            external_id="abc-123",
            payer=Party(party_id_type=PartyIdType.MSISDN, party_id="260960000000"),
            payer_message="Invoice 123",
        )

        dumped = req.model_dump(by_alias=True)

        assert dumped["amount"] == "500"
        assert dumped["externalId"] == "abc-123"
        assert dumped["payer"]["partyId"] == "260960000000"
