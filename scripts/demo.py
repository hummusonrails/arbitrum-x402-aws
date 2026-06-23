"""Guided, presentation-grade walkthrough of the x402 demo (Rich edition).

This is the live "deck" for the provider and agent segments of the webinar.
It runs the REAL flow (real 402, real on-chain USDC settlement) but renders it
as a sequence of beautiful, slide-like screens with a branded palette,
syntax-highlighted JSON, a bold wordmark, and an Enter-to-advance rhythm.

Run via the make targets (which use apps/agent's uv environment):

    make demo             # THE entry point: pre-flight -> segments 3 + 4
    make demo-preflight   # escape hatch: prep + smoke-test only
    make demo-provider    # escape hatch: segment 3 only
    make demo-agent       # escape hatch: segment 4 only

Direct:  cd apps/agent && uv run python ../../scripts/demo.py <cmd> [--auto]

It never prints secrets: no private key, no wallet secret, no AWS account id.
Only public data (merchant URL, wallet address, recipient, tx hash, ids).
"""

from __future__ import annotations

import base64
import json
import os
import shutil
import subprocess
import sys
import uuid
from pathlib import Path

import httpx
from dotenv import load_dotenv
from rich import box
from rich.align import Align
from rich.console import Console, Group
from rich.panel import Panel
from rich.rule import Rule
from rich.syntax import Syntax
from rich.table import Table
from rich.text import Text
from rich.theme import Theme

REPO_ROOT = Path(__file__).resolve().parents[1]
ENV_PATH = REPO_ROOT / ".env"
load_dotenv(ENV_PATH, override=True)

from bedrock_agentcore.payments import PaymentManager  # noqa: E402

from x402_aws_agent.config import load_run_config  # noqa: E402
from x402_aws_agent.http_client import fetch_with_payment  # noqa: E402

ARB_RPC = "https://arb1.arbitrum.io/rpc"
USDC = "0xaf88d065e77c8cC2239327C5EDb3A432268e5831"

# ----------------------------------------------------------------------------
# Brand palette + console
# ----------------------------------------------------------------------------

BLUE = "#12AAFF"     # Arbitrum
PURPLE = "#8B5CF6"   # x402
AMBER = "#FF9900"    # AWS
CDP = "#1652F0"      # Coinbase
GREEN = "#22C55E"
RED = "#EF4444"
SLATE = "#94A3B8"

THEME = Theme(
    {
        "brand.blue": BLUE,
        "brand.purple": PURPLE,
        "brand.amber": AMBER,
        "brand.cdp": CDP,
        "ok": f"bold {GREEN}",
        "warn": f"bold {AMBER}",
        "err": f"bold {RED}",
        "muted": SLATE,
        "val": f"bold {BLUE}",
        "key": "bold white",
    }
)

console = Console(theme=THEME, highlight=False)
_AUTO = False


def slide_w() -> int:
    return min(max(console.size.width - 4, 60), 92)


def pause(msg: str = "press Enter to continue  ▸") -> None:
    if _AUTO:
        return
    try:
        console.input(f"\n   [muted]{msg}[/muted]  ")
    except (EOFError, KeyboardInterrupt):
        raise SystemExit(0)


def show(renderable, *, top: int = 1, advance: bool = True) -> None:
    """Clear the screen and present one centered renderable as a slide."""
    console.clear()
    console.print("\n" * top, end="")
    console.print(Align.center(renderable))
    if advance:
        pause()


def deck_panel(
    renderable,
    *,
    title: str | None = None,
    subtitle: str | None = None,
    border: str = "brand.blue",
    box_=box.HEAVY,
    pad=(2, 5),
) -> Panel:
    return Panel(
        renderable,
        title=title,
        subtitle=subtitle,
        title_align="center",
        subtitle_align="center",
        border_style=border,
        box=box_,
        padding=pad,
        width=slide_w(),
    )


def short(s: str, keep: int = 22) -> str:
    """Truncate an identifier for on-screen display."""
    return s if len(s) <= keep + 1 else s[:keep] + "…"


def title_slide(subtitle: str, tagline: str, colors: list[str], border: str) -> None:
    group = Group(
        Text("x402", style=f"bold {colors[0]}", justify="center"),
        Text(subtitle, style=f"bold {colors[-1]}", justify="center"),
        Text(""),
        Text(tagline, style="muted", justify="center"),
    )
    show(deck_panel(group, border=border, pad=(3, 6)))


def para(text: str, justify: str = "left") -> Text:
    return Text(" ".join(text.split()), justify=justify)


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
    return int(r.json()["result"], 16) / 1_000_000


def wallet_address(pm: PaymentManager, cfg) -> str | None:
    resp = pm.get_payment_instrument(
        user_id=cfg.user_id, payment_instrument_id=cfg.payment_instrument_id
    )
    inst = resp.get("paymentInstrument", resp)
    return inst["paymentInstrumentDetails"]["embeddedCryptoWallet"].get("walletAddress")


def mint_session(pm: PaymentManager, cfg) -> str:
    resp = pm.create_payment_session(
        user_id=cfg.user_id,
        limits={
            "maxSpendAmount": {
                "value": os.environ["AGENTCORE_MAX_SPEND_USD"],
                "currency": "USD",
            }
        },
        expiry_time_in_minutes=int(os.environ["AGENTCORE_SESSION_EXPIRY_MINUTES"]),
    )
    return resp.get("paymentSession", resp)["paymentSessionId"]


def write_session_to_env(session_id: str) -> None:
    lines = ENV_PATH.read_text().splitlines()
    for i, ln in enumerate(lines):
        if ln.startswith("PAYMENT_SESSION_ID="):
            lines[i] = f"PAYMENT_SESSION_ID={session_id}"
            break
    else:
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


def json_panel(obj, title: str, border: str = "brand.blue") -> Panel:
    code = Syntax(
        json.dumps(obj, indent=2),
        "json",
        theme="monokai",
        word_wrap=True,
        padding=(1, 3),
        background_color="default",
    )
    return deck_panel(code, title=title, border=border, pad=(1, 3))


SCREENSHOTS = REPO_ROOT / "docs" / "getting-started" / "images"


def code_slide(rel_path: str, lexer: str, a: int, b: int, *, title: str,
               callout: str, highlight=None, border: str = "brand.blue") -> None:
    """Read a real source file at runtime and present lines a..b (1-based).

    Line numbers are the actual file line numbers; `highlight` is a set of those
    same numbers to emphasize.
    """
    src = (REPO_ROOT / rel_path).read_text().splitlines()
    snippet = "\n".join(src[a - 1:b])
    syn = Syntax(
        snippet, lexer, theme="monokai", line_numbers=True, start_line=a,
        word_wrap=True, padding=(1, 2), background_color="default",
        highlight_lines=set(highlight or []),
    )
    group = Group(
        syn, Text(""),
        para(callout, justify="center"), Text(""),
        Text(f"{rel_path}  ·  lines {a}-{b}", style="muted", justify="center"),
    )
    show(deck_panel(group, title=title, border=border, pad=(1, 3)))


def _kitty_capable() -> bool:
    """Terminals that implement the kitty graphics protocol."""
    term = os.environ.get("TERM", "")
    return (
        "kitty" in term
        or "ghostty" in term
        or os.environ.get("TERM_PROGRAM", "") == "WezTerm"
    )


def _kitty_draw(path: Path, rows: int) -> None:
    """Transmit + display a PNG inline via the kitty graphics protocol.

    `f=100` sends the PNG bytes (the terminal decodes them at full resolution);
    `r=rows` fixes the height in cells and the width is derived from the image's
    aspect ratio, so the render is pixel-sharp and exactly `rows` tall. The
    payload is base64-chunked at 4096 bytes per the spec.
    """
    data = base64.standard_b64encode(path.read_bytes())
    out = sys.stdout.buffer
    chunk, n, i, first = 4096, len(data), 0, True
    while i < n:
        part = data[i:i + chunk]
        i += chunk
        more = 0 if i >= n else 1
        header = f"a=T,f=100,r={rows},q=2,m={more}" if first else f"m={more}"
        out.write(b"\x1b_G" + header.encode("ascii") + b";" + part + b"\x1b\\")
        first = False
    out.flush()


def _png_size(path: Path) -> tuple[int, int]:
    """Read a PNG's pixel (width, height) from its IHDR header. No dependency."""
    b = path.read_bytes()[:24]
    return int.from_bytes(b[16:20], "big"), int.from_bytes(b[20:24], "big")


# Approximate terminal cell height:width ratio (cells are ~twice as tall as wide).
_CELL_RATIO = 2.1


def show_screenshot(name: str, reserve_rows: int = 9) -> None:
    """Show a docs screenshot inline, as large as the viewport allows.

    Sized to fill the screen (leaving `reserve_rows` for the title, caption and
    prompt) so the screenshot is upscaled rather than shrunk and stays legible.
    Falls back to chafa, then Preview, on terminals without kitty graphics.
    """
    if _AUTO:
        return
    path = SCREENSHOTS / name
    if not path.exists():
        return

    w_px, h_px = _png_size(path)
    avail_rows = max(10, console.size.height - reserve_rows)
    avail_cols = max(20, console.size.width - 4)
    aspect = (w_px / h_px) * _CELL_RATIO  # cols-per-row for this image
    rows = avail_rows
    if rows * aspect > avail_cols:        # would overflow width -> bind on width
        rows = max(10, int(avail_cols / aspect))
    pad = max(0, (avail_cols - int(rows * aspect)) // 2)

    if sys.stdout.isatty() and _kitty_capable():
        try:
            if pad:
                sys.stdout.write(f"\x1b[{pad}C")
            _kitty_draw(path, rows)
            sys.stdout.write("\n")
            sys.stdout.flush()
            return
        except Exception:  # noqa: BLE001
            pass
    if shutil.which("chafa"):
        subprocess.run(
            ["chafa", f"--size={avail_cols}x{rows}", str(path)], check=False
        )
        return
    if sys.platform == "darwin":
        subprocess.run(["open", str(path)], check=False)


# ----------------------------------------------------------------------------
# Segment 3: provider side
# ----------------------------------------------------------------------------


def cmd_provider() -> int:
    cfg = load_run_config()
    title_slide("The Provider Side", "How a server asks an agent to pay",
                [BLUE, PURPLE], "brand.blue")

    # Hook: the problem
    show(deck_panel(
        para("APIs today gate access with API keys and monthly bills. But how "
             "does an AI agent, with no account and no credit card, pay for a "
             "single API call? That is the problem x402 solves.", justify="center"),
        title="[brand.blue]The problem[/]", border="brand.blue"))

    # The 402 idea
    show(deck_panel(
        para("HTTP has always had a status code reserved for exactly this: "
             "402 Payment Required. For 30 years it sat unused. x402 finally "
             "gives it a job.", justify="center"),
        title="[brand.blue]402 Payment Required[/]", border="brand.blue"))

    # Our merchant
    show(deck_panel(
        para("Our merchant is a normal-looking API on AWS. A request with no "
             "payment does not get the data. It gets back a 402 and a "
             "machine-readable invoice telling the caller exactly how to pay.",
             justify="center"),
        title="[brand.blue]A normal API, with a price[/]", border="brand.blue"))

    # Architecture
    diagram = Align.center(Text.from_markup(
        "[key]Client / Agent[/key]\n"
        "     │\n"
        "     │  GET /report  [muted](no payment)[/]\n"
        "     ▼\n"
        "[key]CloudFront[/] + [brand.amber]Lambda@Edge[/]  [muted](viewer-request)[/]\n"
        "     │\n"
        "     ▼\n"
        "[warn]402[/]  +  payment terms  [muted](a JSON invoice)[/]",
        justify="left",
    ))
    show(deck_panel(
        Group(diagram, Text(""),
              para("The 402 is produced at the edge, before the request ever "
                   "reaches the origin. No payment, no origin call, no cost.",
                   justify="center")),
        title="[brand.amber]At the edge[/]", border="brand.amber"))

    # Real code: the edge handler's no-payment path
    code_slide(
        "apps/merchant/lib/edge-function/index.ts", "typescript", 70, 80,
        title="[brand.amber]The edge function: no payment, no data[/]",
        highlight={74, 79}, border="brand.amber",
        callout="A request with no X-PAYMENT header gets the 402 invoice "
                "immediately (line 79), built at the edge (line 74), before the "
                "origin is ever called.")

    # Live: hit the endpoint
    console.clear()
    console.print("\n")
    console.rule("[brand.blue]Calling the gated resource with NO payment[/]",
                 style="brand.blue")
    console.print()
    console.print(Align.center(Text(f"GET  {cfg.resource_url}", style="muted")))
    r = httpx.get(cfg.resource_url, timeout=20.0)
    big = "402  ·  Payment Required" if r.status_code == 402 else f"{r.status_code}"
    style = "warn" if r.status_code == 402 else "err"
    console.print(Align.center(deck_panel(
        Text(big, style=style, justify="center"),
        border="brand.amber", box_=box.DOUBLE, pad=(1, 4))))
    pause()

    body = r.json()
    terms = body["accepts"][0]
    amt = int(terms["maxAmountRequired"]) / 1_000_000

    table = Table(box=box.SIMPLE_HEAVY, show_edge=False, expand=False,
                  header_style=f"bold {BLUE}", pad_edge=False)
    table.add_column("Field", style="key", no_wrap=True)
    table.add_column("Value", style="val")
    table.add_column("What it means", style="muted")
    extra = terms.get("extra", {})
    table.add_row("scheme", terms["scheme"], "'exact': pay this amount and asset")
    table.add_row("network", terms["network"], "CAIP-2 id · eip155 = EVM, 42161 = Arbitrum One")
    table.add_row("price", terms["maxAmountRequired"], f"= ${amt:.2f} USDC (6 decimals)")
    table.add_row("asset", terms["asset"], "native USDC contract on Arbitrum One")
    table.add_row("payTo", terms["payTo"], "the merchant's payout address")
    table.add_row("extra", f"{extra.get('name', '')} v{extra.get('version', '')}",
                  "EIP-712 domain the agent's signature binds to")
    show(deck_panel(Align.center(table),
                    title="[brand.blue]The payment terms · a machine-readable invoice[/]"))

    # Real code: where that invoice comes from
    code_slide(
        "apps/merchant/lib/edge-function/build-requirements.ts", "typescript", 3, 16,
        title="[brand.blue]Where the invoice comes from[/]",
        highlight={5, 6, 7, 11, 13},
        callout="The exact fields you just saw, assembled from config: the scheme, "
                "the network, the price, the asset, and who gets paid.")

    # Raw response
    show(json_panel(body, "[brand.blue]The actual 402 response body[/]"))

    # Close
    show(deck_panel(
        para("Everything an agent needs to pay is in that JSON: which chain, "
             "which token, how much, and who to pay. No human, no checkout, no "
             "API key. The door is locked until payment. Next: the agent opens it.",
             justify="center"),
        title="[warn]Locked until payment[/]", border="brand.amber"),
        advance=False)
    return 0


# ----------------------------------------------------------------------------
# Segment 4: agent side
# ----------------------------------------------------------------------------


def cmd_agent() -> int:
    cfg = load_run_config()
    payment_manager = PaymentManager(
        payment_manager_arn=cfg.payment_manager_arn, region_name=cfg.region
    )
    title_slide("The Agent Side", "Pay the 402 and settle on Arbitrum One",
                [PURPLE, GREEN], "brand.purple")

    # Who the buyer is
    show(deck_panel(
        para("The buyer is an AI agent running on AWS Bedrock AgentCore. "
             "AgentCore gives it an embedded crypto wallet (backed by Coinbase "
             "CDP) and a spending budget, then lets it pay on its own.",
             justify="center"),
        title="[brand.purple]The autonomous buyer[/]", border="brand.purple"))

    # The question
    show(deck_panel(
        para("One question to answer first: how does a piece of software pay "
             "money on a blockchain, with no human clicking a checkout button?",
             justify="center"),
        title="[brand.purple]How does software pay?[/]", border="brand.purple"))

    # The normal way: transaction + gas
    show(deck_panel(
        Group(
            para("The usual way to move funds on a blockchain is to send a "
                 "transaction: an instruction to the network to move money from "
                 "one address to another."),
            Text(""),
            para("Every transaction costs a small network fee, called gas, paid "
                 "in the chain's native coin (on Ethereum and Arbitrum, that is "
                 "ETH). So to spend dollars, the sender also has to hold ETH."),
        ),
        title="[brand.purple]The normal way: a transaction + gas[/]",
        border="brand.purple"))

    # The friction
    show(deck_panel(
        para("For an agent making a $0.01 purchase, that is a lot of baggage: "
             "hold ETH, estimate gas, sign and broadcast a transaction, wait for "
             "it to confirm. We want something lighter.", justify="center"),
        title="[brand.purple]Too much for one cent[/]", border="brand.purple"))

    # Sign, don't send
    show(deck_panel(
        Group(
            para("x402's move: sign, do not send. Instead of broadcasting a "
                 "transaction, the agent's wallet cryptographically signs an "
                 "authorization."),
            Text(""),
            para("Think of a signed, tamper-proof check that says: pay $0.01 to "
                 "this address, once, before this deadline. It is just a signed "
                 "message. Nothing has touched the blockchain yet."),
        ),
        title="[brand.purple]x402: sign, don't send[/]", border="brand.purple"))

    # The facilitator does the on-chain part
    show(deck_panel(
        Group(
            para("So who actually puts it on the blockchain? A service called the "
                 "facilitator. It takes the signed authorization, verifies it, "
                 "and submits it to the chain, paying the gas itself."),
            Text(""),
            para("The payoff: the agent's wallet never needs ETH. The signature "
                 "is the payment, and it settles in seconds for a fraction of a "
                 "cent."),
        ),
        title="[brand.purple]The facilitator does the on-chain part[/]",
        border="brand.purple"))

    # Why it's safe
    show(deck_panel(
        para("Two things keep it safe. The authorization can be used only once: "
             "it carries a one-time number, so the same signature cannot be "
             "replayed. And it is cryptographically tied to this exact token and "
             "network, so it cannot be reused anywhere else.", justify="center"),
        title="[brand.purple]Why it is safe[/]", border="brand.purple"))

    # Keywords for the blockchain-curious
    show(deck_panel(
        Group(
            para("For the blockchain-curious, the building blocks are open "
                 "standards:", justify="center"),
            Text(""),
            Text("USDC's transferWithAuthorization  (EIP-3009)", style="val",
                 justify="center"),
            Text("signed as EIP-712 typed data", style="val", justify="center"),
            Text("a one-time nonce  ·  a validity deadline", style="val",
                 justify="center"),
        ),
        title="[brand.purple]Under the hood[/]", border="brand.purple"))

    flow = Align.center(Text.from_markup(
        "[key]Agent[/key]  ──GET──▶  [warn]402[/]\n"
        "   │\n"
        "   ▼  wallet signs the payment  [muted](no transaction, no gas)[/]\n"
        "[key]X-PAYMENT[/]  ──retry──▶  [brand.amber]Lambda@Edge[/]\n"
        "   │\n"
        "   ▼  [brand.cdp]facilitator[/]: check, then submit to the blockchain\n"
        "[ok]USDC moves on Arbitrum One[/]  ──▶  [key]200 + the data[/]",
        justify="left",
    ))
    show(deck_panel(
        Group(flow, Text(""),
              para("The signed authorization is base64-encoded into the X-PAYMENT "
                   "header on the retry. The facilitator's /verify checks the "
                   "signature and balance off-chain (instant); /settle broadcasts "
                   "the transferWithAuthorization on Arbitrum One.", justify="center")),
        title="[brand.purple]Pay and retry[/]", border="brand.purple"))

    # Real code: the agent's pay-and-retry
    code_slide(
        "apps/agent/src/x402_aws_agent/http_client.py", "python", 64, 91,
        title="[brand.purple]The agent's pay-and-retry, in one function[/]",
        highlight={78, 87}, border="brand.purple",
        callout="GET the resource; on a 402, ask AgentCore to sign a payment "
                "header (line 78), then retry the same request with that header "
                "attached (line 87).")

    # Real code: what the merchant does with the proof
    code_slide(
        "apps/merchant/lib/edge-function/facilitator.ts", "typescript", 50, 74,
        title="[brand.purple]What the merchant does with the proof[/]",
        highlight={56, 69}, border="brand.purple",
        callout="The edge function hands the signed payment to the CDP "
                "facilitator: /verify checks it off-chain (line 56), /settle "
                "submits it on Arbitrum One (line 69).")

    ids = Table(box=None, show_header=False, pad_edge=False)
    ids.add_column(style="key", no_wrap=True)
    ids.add_column(style="val")
    ids.add_row("PaymentSession ", short(cfg.payment_session_id))
    ids.add_row("Wallet instrument ", short(cfg.payment_instrument_id))
    show(deck_panel(
        Group(Align.center(ids), Text(""),
              para("Budgeted and time-limited. When you press Enter, the agent "
                   "really pays, on Arbitrum One mainnet.", justify="center")),
        title="[brand.purple]Ready to pay[/]", border="brand.purple"))

    # Live payment with a spinner
    console.clear()
    console.print("\n\n")
    try:
        with console.status(
            Text("Signing EIP-3009 authorization and settling on Arbitrum One…",
                 style="brand.amber"),
            spinner="dots",
        ):
            resp = pay(cfg, cfg.payment_session_id)
    except Exception as exc:  # noqa: BLE001
        show(deck_panel(
            Group(Text("Payment failed", style="err", justify="center"), Text(""),
                  para(str(exc), justify="center"), Text(""),
                  para("Recovery: run `make demo-preflight` to mint a fresh session "
                       "and re-test the path.", justify="center")),
            title="[err]Error[/]", border="err"), advance=False)
        return 1

    if resp.status_code == 200:
        show(deck_panel(Text("PAID  ✓", style="ok", justify="center"),
                        border="ok", box_=box.DOUBLE, pad=(2, 6)))
    else:
        show(deck_panel(Text(str(resp.status_code), style="err", justify="center"),
                        title="[err]Unexpected status[/]", border="err"), advance=False)
        return 1

    # The real 200 response (a small stub from the demo origin)
    show(json_panel(resp.json_body, "[ok]The real 200 response[/]", border="ok"))

    # A realistic, representative unlocked payload (built from the real values)
    real = resp.json_body
    p = real.get("payload", {})
    unlocked = {
        "resource": real.get("resource", "premium-market-data"),
        "asOf": real.get("asOf"),
        "requestId": real.get("requestId"),
        "payment": {
            "protocol": "x402",
            "network": "arbitrum-one",
            "amountUsd": 0.01,
            "settled": True,
        },
        "markets": [
            {"symbol": "BTC", "priceUsd": p.get("btc", 71234.56),
             "change24hPct": 1.02, "volumeUsd": 42330194883},
            {"symbol": "ETH", "priceUsd": p.get("eth", 4567.89),
             "change24hPct": 2.14, "volumeUsd": 18920334512},
            {"symbol": "ARB", "priceUsd": 1.27,
             "change24hPct": -0.83, "volumeUsd": 412903882},
        ],
        "access": "pay-per-call · no subscription, no API key",
    }
    syn = Syntax(json.dumps(unlocked, indent=2), "json", theme="monokai",
                 word_wrap=True, padding=(1, 3), background_color="default")
    show(deck_panel(
        Group(syn, Text(""),
              para("The demo origin returns a tiny stub. In production, this is "
                   "where your gated content lives. The agent now holds it, having "
                   "paid one cent, with no account and no API key.",
                   justify="center")),
        title="[ok]What you just unlocked (representative payload)[/]", border="ok"))

    # Verify on-chain via the wallet's Arbiscan page (always available)
    addr = wallet_address(payment_manager, cfg)
    if addr:
        link = Text(f"https://arbiscan.io/address/{addr}", style=f"bold {BLUE}",
                    justify="center")
        show(deck_panel(
            Group(Text("Settled on Arbitrum One", style="ok", justify="center"),
                  Text(""), link, Text(""),
                  para("The most recent USDC transfer on the agent's wallet is the "
                       "payment you just made. Public, on-chain, final in seconds, "
                       "for a fraction of a cent.", justify="center")),
            title="[ok]Verify it on-chain[/]", border="ok"), advance=False)
    return 0


# ----------------------------------------------------------------------------
# Optional: one-time setup recap (uses the real docs screenshots)
# ----------------------------------------------------------------------------


def cmd_setup() -> int:
    """Walk the one-time CDP + AWS setup, opening the real docs screenshots."""
    title_slide("Before the agent can pay",
                "the one-time setup, on CDP and AWS", [AMBER, BLUE], "brand.amber")

    steps = [
        ("01-cdp-create-api-key.png", "Coinbase Developer Platform: API key",
         "Create a Secret API key in CDP. The merchant authenticates to the CDP "
         "facilitator with it."),
        ("01-cdp-delegated-signing.png", "CDP: delegated signing",
         "Enable delegated signing so AgentCore can sign for the agent, within a "
         "budget you set."),
        ("03-iam-role-summary.png", "AWS: one IAM role",
         "Create one IAM role that AgentCore Payments assumes at runtime to "
         "manage the wallet."),
    ]
    for img, t, callout in steps:
        console.clear()
        console.rule(f"[brand.amber]{t}[/]", style="brand.amber")
        console.print()
        console.print(Text(callout, style="muted", justify="center"))
        console.print()
        show_screenshot(img)
        pause()

    show(deck_panel(
        para("That is the entire setup. From here, the merchant is live and the "
             "agent has a funded, budgeted wallet. Now the demo.", justify="center"),
        title="[brand.amber]Setup done[/]", border="brand.amber"), advance=False)
    return 0


# ----------------------------------------------------------------------------
# Pre-flight + the single entry point
# ----------------------------------------------------------------------------


def _step(n: int, label: str) -> None:
    console.print(f"\n[brand.amber]{n}[/]  [key]{label}[/]")


def _preflight() -> bool:
    cfg = load_run_config()
    pm = PaymentManager(payment_manager_arn=cfg.payment_manager_arn, region_name=cfg.region)

    _step(1, "Merchant is live and returns 402")
    code = httpx.get(cfg.resource_url, timeout=20.0).status_code
    if code != 402:
        console.print(f"   [err]✗ expected 402, got {code}, CloudFront down or mis-deployed[/]")
        return False
    console.print(f"   [ok]✓[/] {cfg.resource_url} → 402")

    _step(2, "Agent wallet is funded")
    addr = wallet_address(pm, cfg)
    bal = usdc_balance(addr) if addr else 0.0
    console.print(f"   [muted]wallet[/] [val]{addr}[/]")
    if bal <= 0.02:
        console.print(f"   [err]✗ only ${bal:.4f} USDC. Fund the wallet before the demo[/]")
        return False
    console.print(f"   [ok]✓[/] ${bal:.4f} USDC  [muted](~{int(bal / 0.01)} payments)[/]")

    _step(3, "Mint a fresh PaymentSession")
    with console.status("minting…", spinner="dots"):
        sid = mint_session(pm, cfg)
    write_session_to_env(sid)
    console.print(f"   [ok]✓[/] {sid}")

    _step(4, "Real end-to-end smoke test (one $0.01 payment)")
    try:
        with console.status("paying + settling on Arbitrum One…", spinner="dots"):
            resp = pay(cfg, sid)
    except Exception as exc:  # noqa: BLE001
        console.print(f"   [err]✗ smoke test failed: {exc}[/]")
        console.print("   [muted]If 'grant is not active': re-grant via "
                      "scripts/inspect_instrument.py[/]")
        return False
    if resp.status_code != 200:
        console.print(f"   [err]✗ got {resp.status_code}, expected 200[/]")
        return False
    tx = resp.json_body.get("txHash") or resp.json_body.get("tx_hash") or "(none)"
    console.print(f"   [ok]✓[/] settled · status 200 · tx {tx}")

    _step(5, "Mint a clean session for the live run")
    sid2 = mint_session(pm, cfg)
    write_session_to_env(sid2)
    console.print(f"   [ok]✓[/] {sid2}")
    return True


def _share_reminders() -> Group:
    return Group(
        Text("Before you share your screen:", style="warn", justify="center"),
        Text(""),
        Text("•  Close .env and cdp_api_key.json in your editor", style="muted", justify="center"),
        Text("•  Clear terminal scrollback  (Cmd+K)", style="muted", justify="center"),
        Text("•  Bump terminal font size for readability", style="muted", justify="center"),
        Text("•  Pre-open tabs: Arbiscan (wallet), CDP, AWS console", style="muted", justify="center"),
    )


def cmd_preflight() -> int:
    console.clear()
    console.print(Align.center(deck_panel(
        Text("PRE-FLIGHT  ·  dress rehearsal", style="warn", justify="center"),
        border="brand.amber", box_=box.DOUBLE, pad=(1, 4))))
    if not _preflight():
        return 1
    show(deck_panel(Group(Text("READY", style="ok", justify="center"), Text(""),
                          _share_reminders()),
                    title="[ok]Pre-flight passed[/]", border="ok"), advance=False)
    console.print(Align.center(Text("\nSingle entry point for the live run:  make demo\n",
                                    style="muted")))
    return 0


def cmd_demo() -> int:
    title_slide("Agentic payments, settled on Arbitrum One",
                "live demo · press Enter to advance", [BLUE, PURPLE], "brand.blue")

    show(deck_panel(
        para("First, pre-flight. Run this BEFORE you share your screen. It "
             "refreshes the payment session and makes one real $0.01 test payment "
             "to prove the whole path. If anything is wrong, you find out now.",
             justify="center"),
        title="[warn]Step 1 · pre-flight[/]", border="brand.amber"))

    console.clear()
    console.print("\n")
    console.print(Align.center(Rule("[brand.amber]Pre-flight[/]", style="brand.amber")))
    if not _preflight():
        show(deck_panel(para("Pre-flight failed. Fix the issue above, then run "
                             "`make demo` again.", justify="center"),
                        title="[err]Stop[/]", border="err"), advance=False)
        return 1

    show(deck_panel(Group(Text("SHARE YOUR SCREEN NOW", style="warn", justify="center"),
                          Text("pre-flight passed · the show begins next",
                               style="muted", justify="center"),
                          Text(""), _share_reminders()),
                    border="brand.amber", box_=box.DOUBLE),
         advance=False)
    pause("screen shared and ready?  Enter to begin the setup recap")

    rc = cmd_setup()
    if rc:
        return rc
    pause("Enter to begin SEGMENT 3 (provider)")
    rc = cmd_provider()
    if rc:
        return rc
    pause("Enter to begin SEGMENT 4: the agent pays, live")
    rc = cmd_agent()
    if rc:
        return rc

    show(deck_panel(
        para("That was the whole loop: a 402 invoice, an autonomous payment, and "
             "real settlement on Arbitrum One. Back to you for the wrap-up.",
             justify="center"),
        title="[brand.blue]Demo complete[/]", border="brand.blue"), advance=False)
    return 0


COMMANDS = {
    "demo": cmd_demo,
    "preflight": cmd_preflight,
    "setup": cmd_setup,
    "provider": cmd_provider,
    "agent": cmd_agent,
}


def main(argv: list[str] | None = None) -> int:
    global _AUTO
    args = list(sys.argv[1:] if argv is None else argv)
    if "--auto" in args:
        _AUTO = True
        args.remove("--auto")
    cmd = args[0] if args else ""
    if cmd not in COMMANDS:
        console.print(f"Usage: demo.py [{' | '.join(COMMANDS)}] [--auto]")
        return 2
    try:
        return COMMANDS[cmd]()
    except KeyboardInterrupt:
        console.print()
        return 0


if __name__ == "__main__":
    raise SystemExit(main())
