"""Request a payment from a payer (sync) and wait for it to complete.

Requires MOMO_COL_SUBSCRIPTION_KEY, MOMO_COL_API_USER, and
MOMO_COL_API_KEY to be set in the environment.
"""

import mtn_momo as momo

client = momo.MomoClient()
reference_id = client.collections.request_to_pay(
    amount="500",
    currency="ZMW",
    payer=momo.Party(party_id_type=momo.PartyIdType.MSISDN, party_id="256770000000"),
    payer_message="Invoice 123",
)
print(f"Submitted request_to_pay, reference_id={reference_id}")

status = client.collections.wait_for_transaction(reference_id)
print(f"Final status: {status.status}")
