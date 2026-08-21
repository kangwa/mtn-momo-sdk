"""Use poll_until_complete_sync directly for custom polling behavior.

wait_for_transaction() on the product clients is a thin wrapper around this
same helper using default timing (PollConfig()). Reach for
poll_until_complete_sync/async directly when you want custom backoff/timeout
behavior, e.g. a slower start with a longer max wait for a low-priority job.

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
        )

        # Starts slower, backs off up to 30s between polls, gives up after 2 minutes.
        poll_config = momo.PollConfig(interval=3.0, backoff=1.5, max_interval=30.0, timeout=120.0)

        status = momo.poll_until_complete_sync(
            lambda: client.get_transaction_status(reference_id),
            poll_config,
        )
        print(f"Final status: {status.status}")


if __name__ == "__main__":
    main()
