"""Provision a sandbox API user and key, and print them for use as env vars.

Requires MOMO_SANDBOX_SUBSCRIPTION_KEY to be set in the environment. Collections,
Disbursements, and Remittance each have their own subscription key — pass the
one for whichever product you're provisioning, and run this once per product.

Equivalent to running:
    uv run mtn-momo-provision --product collections --subscription-key YOUR_KEY
This script shows the same flow used as a library instead of the CLI.
"""

import os
import sys

from mtn_momo import SandboxProvisioner

subscription_key = os.environ.get("MOMO_SANDBOX_SUBSCRIPTION_KEY")
if not subscription_key:
    sys.exit("missing required environment variable: MOMO_SANDBOX_SUBSCRIPTION_KEY")

provisioner = SandboxProvisioner(subscription_key)
credentials = provisioner.provision()
info = provisioner.get_api_user_info(credentials.api_user)

print(f"API_USER={credentials.api_user}")
print(f"API_KEY={credentials.api_key}")
print(f"Target environment: {info.target_environment}")
