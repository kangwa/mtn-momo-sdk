"""Request a payment from a payer (async) and wait for it to complete.

Requires MOMO_COL_SUBSCRIPTION_KEY, MOMO_COL_API_USER, and
MOMO_COL_API_KEY to be set in the environment.
"""

import asyncio

import mtn_momo as momo


async def main() -> None:
    client = momo.AsyncMomoClient()
    reference_id = await client.collections.request_to_pay(
        amount="500",
        currency="ZMW",
        payer=momo.Party(party_id_type=momo.PartyIdType.MSISDN, party_id="256770000000"),
        payer_message="Invoice 123",
    )
    print(f"Submitted request_to_pay, reference_id={reference_id}")

    status = await client.collections.wait_for_transaction(reference_id)
    print(f"Final status: {status.status}")


asyncio.run(main())
