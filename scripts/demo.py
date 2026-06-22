"""Guided, presentation-grade walkthrough of the x402 demo.

This is the live "deck" for the provider and agent segments of the webinar.
It runs the REAL flow (real 402, real on-chain USDC settlement) but wraps each
step in large, readable, instructive output with narration and pauses so an
audience can follow along.

Run via the make targets (which use apps/agent's uv environment):

    make demo-preflight   # ~15 min before going live: refresh + smoke-test
    make demo-provider    # segment 3: the 402 / payment-terms side
    make demo-agent       # segment 4: pay + settle on Arbitrum One

Direct:  cd apps/agent && uv run python ../../scripts/demo.py <cmd> [--auto]

It never prints secrets: no private key, no wallet secret, no AWS account id.
Only public data (merchant URL, wallet address, recipient, tx hash, ids).
"""

from __future__ import annotations

import os
import shutil
import sys
import textwrap
import uuid
from pathlib import Path

import httpx
from dotenv import load_dotenv

REPO_ROOT = Path(__file__).resolve().parents[1]
ENV_PATH = REPO_ROOT / ".env"
load_dotenv(ENV_PATH, override=True)

from bedrock_agentcore.payments import PaymentManager  # noqa: E402

from x402_aws_agent.config import load_run_config  # noqa: E402
from x402_aws_agent.http_client import fetch_with_payment  # noqa: E402

ARB_RPC = "https://arb1.arbitrum.io/rpc"
USDC = "0xaf88d065e77c8cC2239327C5EDb3A432268e5831"

# ----------------------------------------------------------------------------
# Presentation helpers
# ----------------------------------------------------------------------------

_USE_COLOR = sys.stdout.isatty() and os.environ.get("NO_COLOR") is None


def _c(code: str) -> str:
    return code if _USE_COLOR else ""


RESET = _c("\033[0m")
BOLD = _c("\033[1m")
DIM = _c("\033[2m")
CYAN = _c("\033[36m")
GREEN = _c("\033[32m")
YELLOW = _c("\033[33m")
MAGENTA = _c("\033[35m")
BLUE = _c("\033[34m")
RED = _c("\033[31m")
GREY = _c("\033[90m")

_AUTO = False


def _width() -> int:
    return min(shutil.get_terminal_size((80, 24)).columns, 84)


def banner(title: str, subtitle: str = "", color: str = CYAN) -> None:
    w = _width()
    line = "═" * w
    print("\n" + color + line + RESET)
    print(color + BOLD + title.center(w) + RESET)
    if subtitle:
        print(color + subtitle.center(w) + RESET)
    print(color + line + RESET + "\n")


def section(text: str, color: str = MAGENTA) -> None:
    print("\n" + color + BOLD + "▶ " + text + RESET)
    print(color + DIM + "─" * min(len(text) + 2, _width()) + RESET)


def narrate(text: str, color: str = "") -> None:
    w = _width() - 2
    for para in text.strip().split("\n\n"):
        wrapped = textwrap.fill(" ".join(para.split()), width=w)
        print((color or "") + textwrap.indent(wrapped, "  ") + (RESET if color else ""))
        print()


def kv(label: str, value: str, note: str = "") -> None:
    tail = f"   {GREY}{note}{RESET}" if note else ""
    print(f"  {BOLD}{label:<22}{RESET}{CYAN}{value}{RESET}{tail}")


def ok(text: str) -> None:
    print(f"  {GREEN}✓{RESET} {text}")


def warn(text: str) -> None:
    print(f"  {YELLOW}!{RESET} {text}")


def fail(text: str) -> None:
    print(f"  {RED}✗ {text}{RESET}")


def pause(msg: str = "Press Enter to continue") -> None:
    if _AUTO:
        return
    try:
        input(f"\n{DIM}   [{msg}]{RESET} ")
    except (EOFError, KeyboardInterrupt):
        print()
        raise SystemExit(0)


def diagram(lines: list[str], color: str = BLUE) -> None:
    for ln in lines:
        print("  " + color + ln + RESET)
    print()


# ----------------------------------------------------------------------------
# Live helpers (real network + chain calls)
# ----------------------------------------------------------------------------


def usdc_balance(address: str) -> float:
    data = "0x70a08231" + "0" * 24 + address.lower().replace("0x", "")
    payload = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "eth_call",
        "params": [{"to": USDC, "data": data}, "latest"],
    }
    r = httpx.post(ARB_RPC, json=payload, timeout=15.0)
    raw = int(r.json()["result"], 16)
    return raw / 1_000_000


def wallet_address(pm: PaymentManager, cfg) -> str | None:
    resp = pm.get_payment_instrument(
        user_id=cfg.user_id, payment_instrument_id=cfg.payment_instrument_id
    )
    inst = resp.get("paymentInstrument", resp)
    return inst["paymentInstrumentDetails"]["embeddedCryptoWallet"].get("walletAddress")


def mint_session(pm: PaymentManager, cfg) -> str:
    max_spend = os.environ["AGENTCORE_MAX_SPEND_USD"]
    expiry = int(os.environ["AGENTCORE_SESSION_EXPIRY_MINUTES"])
    resp = pm.create_payment_session(
        user_id=cfg.user_id,
        limits={"maxSpendAmount": {"value": max_spend, "currency": "USD"}},
        expiry_time_in_minutes=expiry,
    )
    return resp.get("paymentSession", resp)["paymentSessionId"]


def write_session_to_env(session_id: str) -> None:
    lines = ENV_PATH.read_text().splitlines()
    found = False
    for i, ln in enumerate(lines):
        if ln.startswith("PAYMENT_SESSION_ID="):
            lines[i] = f"PAYMENT_SESSION_ID={session_id}"
            found = True
            break
    if not found:
        lines.append(f"PAYMENT_SESSION_ID={session_id}")
    ENV_PATH.write_text("\n".join(lines) + "\n")


def pay(cfg, session_id: str):
    pm = PaymentManager(
        payment_manager_arn=cfg.payment_manager_arn, region_name=cfg.region
    )
    with httpx.Client(timeout=40.0) as client:
        return fetch_with_payment(
            client=client,
            payment_manager=pm,
            url=cfg.resource_url,
            user_id=cfg.user_id,
            payment_instrument_id=cfg.payment_instrument_id,
            payment_session_id=session_id,
        )


# ----------------------------------------------------------------------------
# Segment 3: provider side
# ----------------------------------------------------------------------------


def cmd_provider() -> int:
    cfg = load_run_config()
    banner("x402 · THE PROVIDER SIDE", "How a server asks an agent to pay", CYAN)

    narrate(
        "HTTP has always had a status code reserved for this moment: 402 Payment "
        "Required. For 30 years it sat unused. x402 finally gives it a job."
    )
    narrate(
        "Our merchant is a normal-looking API on AWS. A request with no payment "
        "does not get the data, it gets a 402 plus a machine-readable invoice "
        "telling the caller exactly how to pay."
    )
    diagram(
        [
            "┌────────┐   GET /report  (no payment)   ┌──────────────┐",
            "│ Client │ ────────────────────────────▶ │  CloudFront  │",
            "│ /Agent │ ◀──────────────────────────── │ +Lambda@Edge │",
            "└────────┘   402  +  payment terms        └──────────────┘",
            "                                          (viewer-request)",
        ]
    )
    narrate(
        "The 402 is produced at the edge by a Lambda@Edge viewer-request function, "
        "before the request ever reaches the origin. No payment, no origin call."
    )
    pause("hit the endpoint live")

    section("Calling the gated resource with NO payment")
    kv("GET", cfg.resource_url)
    r = httpx.get(cfg.resource_url, timeout=20.0)
    color = GREEN if r.status_code == 402 else RED
    print(f"\n  {BOLD}HTTP status:{RESET} {color}{BOLD}{r.status_code} "
          f"{'Payment Required' if r.status_code == 402 else ''}{RESET}\n")
    body = r.json()
    terms = body["accepts"][0]

    section("The payment terms (this is the invoice)")
    amt = int(terms["maxAmountRequired"]) / 1_000_000
    kv("scheme", terms["scheme"], "pay this exact amount")
    kv("network", terms["network"], "Arbitrum One (CAIP-2)")
    kv("price", f"{terms['maxAmountRequired']} base units", f"= ${amt:.2f} USDC (6 decimals)")
    kv("asset", terms["asset"], "native USDC on Arbitrum One")
    kv("payTo", terms["payTo"], "the merchant's payout address")
    kv("resource", terms["resource"])
    kv("x402Version", str(body["x402Version"]))
    print()
    narrate(
        "Everything an agent needs to pay is in this JSON: which chain, which "
        "token, how much, and who to pay. No human, no checkout page, no API key. "
        "An agent can read this and settle it on its own. That is segment 4."
    )
    banner("PROVIDER SIDE: the door is locked until payment", color=YELLOW)
    return 0


# ----------------------------------------------------------------------------
# Segment 4: agent side
# ----------------------------------------------------------------------------


def cmd_agent() -> int:
    cfg = load_run_config()
    banner("x402 · THE AGENT SIDE", "Pay the 402 and settle on Arbitrum One", GREEN)

    narrate(
        "Now the buyer. Our agent runs on AWS Bedrock AgentCore, which gives it an "
        "embedded crypto wallet (backed by Coinbase CDP) and a spending budget."
    )
    diagram(
        [
            "Agent ─GET─▶ 402 ─▶ AgentCore signs EIP-3009 ─▶ retry w/ X-PAYMENT",
            "                     (from the embedded wallet,        │",
            "                      within the session budget)       ▼",
            "  200 + data ◀─ CDP facilitator verify + settle ◀──────┘",
            "                          │",
            "                          ▼  USDC moves on Arbitrum One",
            "                     Arbiscan tx",
        ],
        color=GREEN,
    )
    narrate(
        "The signature is an EIP-3009 transferWithAuthorization: the wallet "
        "authorizes a USDC transfer without holding ETH for gas. The merchant's "
        "edge function hands that proof to the CDP facilitator, which verifies it "
        "and settles it on-chain. Then, and only then, the data is returned."
    )
    kv("PaymentSession", cfg.payment_session_id, "budgeted, time-limited")
    kv("Wallet instrument", cfg.payment_instrument_id, "the agent's embedded wallet")
    pause("run the live payment")

    section("Agent requests the resource, pays, and retries")
    print(f"  {DIM}GET {cfg.resource_url}{RESET}")
    print(f"  {DIM}... 402 received, signing payment, retrying ...{RESET}\n")
    try:
        resp = pay(cfg, cfg.payment_session_id)
    except Exception as exc:  # noqa: BLE001
        fail(f"Payment failed: {exc}")
        warn("Recovery: `make demo-preflight` mints a fresh session and re-tests.")
        return 1

    color = GREEN if resp.status_code == 200 else RED
    print(f"  {BOLD}HTTP status:{RESET} {color}{BOLD}{resp.status_code}{RESET}\n")

    section("The gated data (paid for, on-chain)")
    import json

    body = resp.json_body
    for line in json.dumps(body, indent=2).splitlines():
        print("  " + line)

    tx = body.get("txHash") or body.get("tx_hash")
    if tx:
        banner("SETTLED ON ARBITRUM ONE", color=GREEN)
        kv("Arbiscan", f"https://arbiscan.io/tx/{tx}")
        narrate(
            "That link is the real, public, on-chain USDC transfer from the agent's "
            "wallet to the merchant. Open it: an autonomous agent just bought data "
            "and paid for it, settled in seconds for a fraction of a cent."
        )
    return 0


# ----------------------------------------------------------------------------
# Pre-flight: run ~15 min before going live
# ----------------------------------------------------------------------------


def cmd_preflight() -> int:
    banner("PRE-FLIGHT · run ~15 min before going live", color=YELLOW)
    cfg = load_run_config()
    pm = PaymentManager(
        payment_manager_arn=cfg.payment_manager_arn, region_name=cfg.region
    )

    section("1. Merchant is live and returns 402")
    code = httpx.get(cfg.resource_url, timeout=20.0).status_code
    if code == 402:
        ok(f"{cfg.resource_url} -> 402")
    else:
        fail(f"Expected 402, got {code}. CloudFront may be down or mis-deployed.")
        return 1

    section("2. Agent wallet is funded")
    addr = wallet_address(pm, cfg)
    bal = usdc_balance(addr) if addr else 0.0
    kv("Wallet", addr or "unknown")
    kv("USDC balance", f"${bal:.4f}")
    if bal <= 0.02:
        fail("Wallet has insufficient USDC. Fund it before the demo.")
        return 1
    ok(f"Funded (~{int(bal / 0.01)} payments of headroom)")

    section("3. Mint a fresh PaymentSession (today's is expired)")
    sid = mint_session(pm, cfg)
    write_session_to_env(sid)
    ok(f"New session written to .env: {sid}")

    section("4. Real end-to-end smoke test (one $0.01 payment)")
    try:
        resp = pay(cfg, sid)
    except Exception as exc:  # noqa: BLE001
        fail(f"Smoke-test payment failed: {exc}")
        warn("If 'Delegated signing grant is not active': re-grant the wallet at "
             "its WalletHub URL (scripts/inspect_instrument.py prints it).")
        return 1
    if resp.status_code == 200:
        tx = resp.json_body.get("txHash") or resp.json_body.get("tx_hash") or "(none)"
        ok(f"Paid + settled. Status 200. tx: {tx}")
    else:
        fail(f"Smoke test returned {resp.status_code}, not 200.")
        return 1

    section("5. Mint a clean session for the live run")
    sid2 = mint_session(pm, cfg)
    write_session_to_env(sid2)
    ok(f"Live-run session written to .env: {sid2}")

    banner("✅ READY FOR LIVE DEMO", color=GREEN)
    kv("Merchant", cfg.resource_url)
    kv("Agent wallet", addr or "unknown")
    kv("USDC balance", f"${usdc_balance(addr):.4f}" if addr else "?")
    print()
    warn("Before you share your screen:")
    print(f"     {GREY}- Close .env and cdp_api_key.json in your editor{RESET}")
    print(f"     {GREY}- Clear terminal scrollback (Cmd+K) so no secrets are visible{RESET}")
    print(f"     {GREY}- Bump terminal font size for readability{RESET}")
    print(f"     {GREY}- Pre-open browser tabs: Arbiscan (wallet), CDP, AWS console{RESET}")
    print(f"\n  Then run: {BOLD}make demo-provider{RESET}  and  {BOLD}make demo-agent{RESET}\n")
    return 0


COMMANDS = {"preflight": cmd_preflight, "provider": cmd_provider, "agent": cmd_agent}


def main(argv: list[str] | None = None) -> int:
    global _AUTO
    args = list(sys.argv[1:] if argv is None else argv)
    if "--auto" in args:
        _AUTO = True
        args.remove("--auto")
    cmd = args[0] if args else ""
    if cmd not in COMMANDS:
        print(f"Usage: demo.py [{' | '.join(COMMANDS)}] [--auto]")
        return 2
    try:
        return COMMANDS[cmd]()
    except KeyboardInterrupt:
        print()
        return 0


if __name__ == "__main__":
    raise SystemExit(main())
