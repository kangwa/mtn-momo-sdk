"""Pay money out to a payee (sync) and wait for the transfer to complete.

Requires MOMO_DIS_SUBSCRIPTION_KEY, MOMO_DIS_API_USER, and
MOMO_DIS_API_KEY to be set in the environment.
"""

import mtn_momo as momo

client = momo.MomoClient()
reference_id = client.disbursements.transfer(
    amount="1000",
    currency="ZMW",
    payee=momo.Party(party_id_type=momo.PartyIdType.MSISDN, party_id="256770000001"),
    payee_note="Salary payment",
)
print(f"Submitted transfer, reference_id={reference_id}")

status = client.disbursements.wait_for_transaction(reference_id)
print(f"Final status: {status.status}")
