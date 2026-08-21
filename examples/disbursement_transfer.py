"""Pay money out to a payee (sync) and wait for the transfer to complete.

Requires MOMO_DISBURSEMENTS_SUBSCRIPTION_KEY, MOMO_DISBURSEMENTS_API_USER, and
MOMO_DISBURSEMENTS_API_KEY to be set in the environment.
"""

import mtn_momo as momo


def main() -> None:
    config = momo.ProductConfig.from_env("MOMO_DISBURSEMENTS_")

    with momo.DisbursementsClient(config) as client:
        reference_id = client.transfer(
            amount="1000",
            currency="EUR",
            payee=momo.Party(party_id_type=momo.PartyIdType.MSISDN, party_id="256770000001"),
            payee_note="Salary payment",
        )
        print(f"Submitted transfer, reference_id={reference_id}")

        status = client.wait_for_transaction(reference_id)
        print(f"Final status: {status.status}")


if __name__ == "__main__":
    main()
