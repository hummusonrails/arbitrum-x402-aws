"""One-shot bootstrap: create AgentCore PaymentManager + Connector + Instrument + Session.

Run with: uv run x402-aws-agent-setup

Prints the resource IDs at the end. The user copies these into .env before
running x402-aws-agent-run.
"""

from __future__ import annotations

import json
import os
import sys
import uuid
from pathlib import Path

import boto3
from bedrock_agentcore.payments import PaymentClient, PaymentManager

from x402_aws_agent.config import (
    SetupConfig,
    load_setup_config,
    resolve_repo_relative,
)


def _read_cdp_credentials(api_key_file: Path) -> dict[str, str]:
    """Read CDP API key JSON + wallet secret from env.

    The Coinbase Developer Portal exports an API key JSON with id/name and
    privateKey. The wallet secret is a separate value generated under
    Embedded Wallets > Policies (requires Delegated signing enabled).
    """
    raw = json.loads(api_key_file.read_text())
    api_key_id = raw.get("id") or raw.get("name")
    private_key = raw.get("privateKey")
    if not api_key_id or not private_key:
        raise ValueError(
            f"CDP API key JSON at {api_key_file} missing 'id'/'name' or 'privateKey'. "
            f"Found keys: {sorted(raw.keys())}"
        )

    wallet_secret = os.environ.get("CDP_WALLET_SECRET", "").strip()
    if not wallet_secret:
        raise ValueError(
            "CDP_WALLET_SECRET is required in .env. "
            "Generate it in the Coinbase Developer Platform under "
            "Project > Wallet > Embedded Wallets > Policies "
            "(enable Delegated signing first)."
        )

    return {
        "api_key_id": api_key_id,
        "api_key_secret": private_key,
        "wallet_secret": wallet_secret,
    }


def _resolve_service_role_arn(region: str) -> str:
    """Resolve the AgentCore service role ARN.

    Defaults to the conventional name; override with AGENTCORE_SERVICE_ROLE_ARN.
    The role must exist with the documented trust policy + base permissions:
    https://docs.aws.amazon.com/bedrock-agentcore/latest/devguide/payments-iam-roles.html
    """
    explicit = os.environ.get("AGENTCORE_SERVICE_ROLE_ARN", "").strip()
    if explicit:
        return explicit

    sts = boto3.client("sts", region_name=region)
    account_id = sts.get_caller_identity()["Account"]
    return f"arn:aws:iam::{account_id}:role/AgentCorePaymentsResourceRetrievalRole"


def _bootstrap_resources(cfg: SetupConfig) -> dict[str, str]:
    if cfg.provider != "CoinbaseCDP":
        raise NotImplementedError(
            f"Provider {cfg.provider} is not implemented in setup yet. "
            "This demo wires up CoinbaseCDP. See apps/agent/README.md for adding StripePrivy."
        )

    cdp_creds = _read_cdp_credentials(resolve_repo_relative(cfg.cdp_api_key_file))
    service_role_arn = _resolve_service_role_arn(cfg.region)

    payment_client = PaymentClient(region_name=cfg.region)

    print(f"Creating PaymentManager + Connector in {cfg.region} ...")
    print(f"  Using service role: {service_role_arn}")
    # AWS naming constraints:
    #   PaymentManager name: ^[a-zA-Z][a-zA-Z0-9]{0,47}$ (strict alphanumeric)
    #   PaymentManager description: ^[a-zA-Z0-9\s]+$ (alphanumeric + spaces only)
    #   PaymentConnector name: alphanumeric + underscore, max 48
    #   PaymentCredentialProvider name: alphanumeric + underscore + hyphen
    # Use camelCase alphanumeric across the board to satisfy all four.
    suffix = uuid.uuid4().hex[:8]
    pm_response = payment_client.create_payment_manager_with_connector(
        payment_manager_name=f"x402AwsDemo{suffix}",
        payment_manager_description="x402 aws demo Payment Manager",
        authorizer_type="AWS_IAM",
        role_arn=service_role_arn,
        payment_connector_config={
            "name": f"x402AwsDemoCoinbase{suffix}",
            "description": "Coinbase CDP connector for x402 aws demo",
            "payment_credential_provider_config": {
                "name": f"x402AwsCdp{suffix}",
                "credential_provider_vendor": "CoinbaseCDP",
                "credentials": cdp_creds,
            },
        },
        wait_for_ready=True,
        max_wait=300,
        poll_interval=5,
    )
    payment_manager_arn = pm_response["paymentManager"]["paymentManagerArn"]
    payment_connector_id = pm_response["paymentConnector"]["paymentConnectorId"]
    print(f"  PaymentManager ARN:    {payment_manager_arn}")
    print(f"  PaymentConnector ID:   {payment_connector_id}")

    manager = PaymentManager(
        payment_manager_arn=payment_manager_arn,
        region_name=cfg.region,
    )

    print("\nCreating PaymentInstrument (embedded crypto wallet, ETHEREUM/Arbitrum One) ...")
    instrument_response = manager.create_payment_instrument(
        user_id=cfg.user_id,
        payment_connector_id=payment_connector_id,
        payment_instrument_type="EMBEDDED_CRYPTO_WALLET",
        payment_instrument_details={
            "embeddedCryptoWallet": {
                "network": "ETHEREUM",
                "linkedAccounts": [
                    {"email": {"emailAddress": cfg.linked_email}}
                ],
            }
        },
    )
    # The response may be either {paymentInstrument: {...}} or the instrument
    # fields at the top level; handle both shapes.
    instrument = instrument_response.get("paymentInstrument", instrument_response)
    payment_instrument_id = instrument["paymentInstrumentId"]
    instrument_details = instrument["paymentInstrumentDetails"]["embeddedCryptoWallet"]
    wallet_address = instrument_details.get("walletAddress")
    redirect_url = instrument_details.get("redirectUrl")
    print(f"  PaymentInstrument ID:  {payment_instrument_id}")
    print(f"  Wallet address:        {wallet_address}")

    print("\n" + "=" * 70)
    print("ACTION REQUIRED: Fund the wallet and grant agent permissions")
    print("=" * 70)
    print(f"\nOpen this URL in your browser:\n\n  {redirect_url}\n")
    print(
        f"On Coinbase WalletHub:\n"
        f"  1. Log in with the linked email\n"
        f"     ({cfg.linked_email})\n"
        f"  2. Bridge or transfer at least ${cfg.max_spend_usd} USDC to\n"
        f"     the wallet address on Arbitrum One:\n"
        f"     {wallet_address}\n"
        f"     (use https://bridge.arbitrum.io for ETH-to-Arbitrum)\n"
        f"  3. Grant signing permissions to the agent\n"
    )
    input("Press Enter once funding and permissions are complete... ")

    print(
        f"\nCreating PaymentSession "
        f"(budget ${cfg.max_spend_usd}, expiry {cfg.session_expiry_minutes}m) ..."
    )
    session_response = manager.create_payment_session(
        user_id=cfg.user_id,
        limits={"maxSpendAmount": {"value": cfg.max_spend_usd, "currency": "USD"}},
        expiry_time_in_minutes=cfg.session_expiry_minutes,
    )
    session = session_response.get("paymentSession", session_response)
    payment_session_id = session["paymentSessionId"]
    print(f"  PaymentSession ID:     {payment_session_id}")

    return {
        "PAYMENT_MANAGER_ARN": payment_manager_arn,
        "PAYMENT_INSTRUMENT_ID": payment_instrument_id,
        "PAYMENT_SESSION_ID": payment_session_id,
    }


def main() -> int:
    cfg = load_setup_config()
    try:
        result = _bootstrap_resources(cfg)
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1

    print("\n" + "=" * 70)
    print("SUCCESS: Add these lines to your repo-root .env file:")
    print("=" * 70)
    for key, value in result.items():
        print(f"{key}={value}")
    print()
    print("Then run: make run-agent")
    return 0


if __name__ == "__main__":
    sys.exit(main())
