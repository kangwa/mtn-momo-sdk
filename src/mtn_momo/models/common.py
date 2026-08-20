"""Shared base model and value types used by other MoMo request and response models."""

from pydantic import BaseModel, ConfigDict
from pydantic.alias_generators import to_camel

from mtn_momo.constants import PartyIdType


class MomoModel(BaseModel):
    """Base for all MoMo wire models: camelCase on the wire, snake_case in Python."""

    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)


class Party(MomoModel):
    """A payer (Collections) or payee (Disbursements/Remittance) in a MoMo transaction.

    Attributes:
        party_id_type: How the party is identified (MSISDN, email, or party code).
        party_id: The identifier itself, e.g. a phone number for MSISDN.
    """

    party_id_type: PartyIdType
    party_id: str
