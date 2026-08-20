from momo_sdk.constants import PartyIdType
from momo_sdk.models.common import Party


class TestParty:
    def test_serializes_to_camel_case(self) -> None:
        party = Party(party_id_type=PartyIdType.MSISDN, party_id="260960000000")
        assert party.model_dump(by_alias=True) == {
            "partyIdType": "MSISDN",
            "partyId": "260960000000",
        }

    def test_parses_from_camel_case(self) -> None:
        party = Party.model_validate({"partyIdType": "MSISDN", "partyId": "260960000000"})
        assert party.party_id_type == PartyIdType.MSISDN
