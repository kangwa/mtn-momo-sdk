"""Provision a sandbox API user and key, and print them for use as env vars.

Requires MOMO_SANDBOX_SUBSCRIPTION_KEY to be set in the environment — this is
the sandbox subscription key for whichever product you're provisioning against
(Collections, Disbursements, and Remittance all use the same provisioning flow).

Equivalent to running: uv run mtn-momo-provision --subscription-key YOUR_KEY
This script shows the same flow used as a library instead of the CLI.
"""

import os
import sys

from mtn_momo import SandboxProvisioner


def main() -> None:
    subscription_key = os.environ.get("MOMO_SANDBOX_SUBSCRIPTION_KEY")
    if not subscription_key:
        sys.exit("missing required environment variable: MOMO_SANDBOX_SUBSCRIPTION_KEY")

    with SandboxProvisioner(subscription_key) as provisioner:
        credentials = provisioner.provision(callback_host="https://example.com/callback")
        info = provisioner.get_api_user_info(credentials.api_user)

    print(f"API_USER={credentials.api_user}")
    print(f"API_KEY={credentials.api_key}")
    print(f"Target environment: {info.target_environment}")


if __name__ == "__main__":
    main()
