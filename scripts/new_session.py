"""Mint a fresh PaymentSession on an existing PaymentManager.

Used to resume after the previous session expired without re-running full setup.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

from dotenv import load_dotenv

REPO_ROOT = Path(__file__).resolve().parents[1]
load_dotenv(REPO_ROOT / ".env", override=True)

from bedrock_agentcore.payments import PaymentManager  # noqa: E402


def main() -> int:
    region = os.environ["AGENTCORE_REGION"]
    user_id = os.environ["AGENTCORE_USER_ID"]
    max_spend = os.environ["AGENTCORE_MAX_SPEND_USD"]
    expiry = int(os.environ["AGENTCORE_SESSION_EXPIRY_MINUTES"])

    arn = os.environ.get("NEW_SESSION_MANAGER_ARN") or os.environ["PAYMENT_MANAGER_ARN"]

    manager = PaymentManager(payment_manager_arn=arn, region_name=region)
    response = manager.create_payment_session(
        user_id=user_id,
        limits={"maxSpendAmount": {"value": max_spend, "currency": "USD"}},
        expiry_time_in_minutes=expiry,
    )
    session = response.get("paymentSession", response)
    print(session["paymentSessionId"])
    return 0


if __name__ == "__main__":
    sys.exit(main())
