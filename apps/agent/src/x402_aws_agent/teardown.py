"""Delete AgentCore resources created by setup.

Usage: uv run x402-aws-agent-teardown

Reads the IDs from .env and deletes session, instrument, connectors, manager.
Credential providers are left in place (they are reusable across runs).
"""

from __future__ import annotations

import sys

import boto3

from x402_aws_agent.config import load_run_config


def _payment_manager_id_from_arn(arn: str) -> str:
    # arn:aws:bedrock-agentcore:<region>:<account>:payment-manager/<name>-<suffix>
    return arn.rsplit("/", 1)[-1]


def main() -> int:
    cfg = load_run_config()

    dp_client = boto3.client("bedrock-agentcore", region_name=cfg.region)
    cp_client = boto3.client("bedrock-agentcore-control", region_name=cfg.region)
    payment_manager_id = _payment_manager_id_from_arn(cfg.payment_manager_arn)

    print(f"Deleting PaymentSession {cfg.payment_session_id} ...")
    try:
        dp_client.delete_payment_session(
            userId=cfg.user_id,
            paymentManagerArn=cfg.payment_manager_arn,
            paymentSessionId=cfg.payment_session_id,
        )
        print("  deleted")
    except Exception as exc:
        print(f"  warning: {exc}")

    print(f"\nDeleting PaymentInstrument {cfg.payment_instrument_id} ...")
    try:
        dp_client.delete_payment_instrument(
            userId=cfg.user_id,
            paymentManagerArn=cfg.payment_manager_arn,
            paymentInstrumentId=cfg.payment_instrument_id,
        )
        print("  deleted")
    except Exception as exc:
        print(f"  warning: {exc}")

    print(f"\nDeleting PaymentConnectors under {payment_manager_id} ...")
    try:
        connectors = cp_client.list_payment_connectors(
            paymentManagerId=payment_manager_id,
        ).get("paymentConnectors", [])
        for c in connectors:
            cp_client.delete_payment_connector(
                paymentManagerId=payment_manager_id,
                paymentConnectorId=c["paymentConnectorId"],
            )
            print(f"  deleted connector {c['paymentConnectorId']}")
        if not connectors:
            print("  no connectors found")
    except Exception as exc:
        print(f"  warning: {exc}")

    print(f"\nDeleting PaymentManager {payment_manager_id} ...")
    try:
        cp_client.delete_payment_manager(paymentManagerId=payment_manager_id)
        print("  deleted")
    except Exception as exc:
        print(f"  warning: {exc}")

    print(
        "\nDone. Clear PAYMENT_MANAGER_ARN, PAYMENT_INSTRUMENT_ID, "
        "PAYMENT_SESSION_ID from .env before re-running setup."
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
