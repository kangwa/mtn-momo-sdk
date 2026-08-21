"""Request a payment from a payer (sync) and wait for it to complete.

Requires MOMO_COLLECTIONS_SUBSCRIPTION_KEY, MOMO_COLLECTIONS_API_USER, and
MOMO_COLLECTIONS_API_KEY to be set in the environment.
"""

import mtn_momo as momo


def main() -> None:
    config = momo.ProductConfig.from_env("MOMO_COLLECTIONS_")

    with momo.CollectionsClient(config) as client:
        reference_id = client.request_to_pay(
            amount="500",
            currency="EUR",
            payer=momo.Party(party_id_type=momo.PartyIdType.MSISDN, party_id="256770000000"),
            payer_message="Invoice 123",
        )
        print(f"Submitted request_to_pay, reference_id={reference_id}")

        status = client.wait_for_transaction(reference_id)
        print(f"Final status: {status.status}")


if __name__ == "__main__":
    main()
