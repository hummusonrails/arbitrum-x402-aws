"""Diagnostic: inspect the current payment instrument, its balance, grant state,
and list all instruments for the user. Read-only.
"""

from __future__ import annotations

import json
import os
from pathlib import Path

from dotenv import load_dotenv

REPO_ROOT = Path(__file__).resolve().parents[1]
load_dotenv(REPO_ROOT / ".env", override=True)

from bedrock_agentcore.payments import PaymentManager  # noqa: E402


def dump(label, fn):
    print(f"=== {label} ===")
    try:
        print(json.dumps(fn(), indent=2, default=str))
    except Exception as e:  # noqa: BLE001
        print(f"ERROR: {e!r}")


def main() -> int:
    region = os.environ["AGENTCORE_REGION"]
    user = os.environ["AGENTCORE_USER_ID"]
    arn = os.environ["PAYMENT_MANAGER_ARN"]
    inst = os.environ["PAYMENT_INSTRUMENT_ID"]
    pm = PaymentManager(payment_manager_arn=arn, region_name=region)

    print(f"instrument in .env: {inst}\n")
    dump("get_payment_instrument", lambda: pm.get_payment_instrument(
        user_id=user, payment_instrument_id=inst))
    dump("get_payment_instrument_balance", lambda: pm.get_payment_instrument_balance(
        user_id=user, payment_instrument_id=inst))
    dump("list_payment_instruments", lambda: pm.list_payment_instruments(user_id=user))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
