"""Run the agent against the merchant.

Usage: uv run x402-aws-agent-run

Reads RESOURCE_URL, PAYMENT_MANAGER_ARN, PAYMENT_INSTRUMENT_ID, PAYMENT_SESSION_ID
from .env (populated by x402-aws-agent-setup). Issues a GET, handles the 402,
and prints the gated JSON + Arbiscan link.
"""

from __future__ import annotations

import json
import sys

import httpx
from bedrock_agentcore.payments import PaymentManager

from x402_aws_agent.config import load_run_config
from x402_aws_agent.http_client import (
    PaymentRequiredError,
    fetch_with_payment,
)


def main() -> int:
    cfg = load_run_config()

    payment_manager = PaymentManager(
        payment_manager_arn=cfg.payment_manager_arn,
        region_name=cfg.region,
    )

    print(f"GET {cfg.resource_url}")
    print(f"  via AgentCore PaymentSession {cfg.payment_session_id}")
    print(f"  using Instrument            {cfg.payment_instrument_id}")
    print()

    try:
        with httpx.Client(timeout=30.0) as client:
            response = fetch_with_payment(
                client=client,
                payment_manager=payment_manager,
                url=cfg.resource_url,
                user_id=cfg.user_id,
                payment_instrument_id=cfg.payment_instrument_id,
                payment_session_id=cfg.payment_session_id,
            )
    except PaymentRequiredError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1

    print(f"Status: {response.status_code}")
    print("Body:")
    print(json.dumps(response.json_body, indent=2))

    tx_hash = response.json_body.get("txHash") or response.json_body.get("tx_hash")
    if tx_hash:
        print(f"\nArbiscan: https://arbiscan.io/tx/{tx_hash}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
