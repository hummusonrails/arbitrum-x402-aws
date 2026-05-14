# Agent (AWS Bedrock AgentCore + Python)

Python buyer agent for the x402 merchant in [`apps/merchant`](../merchant/README.md). Holds an embedded crypto wallet via AWS Bedrock AgentCore payments (Coinbase CDP), pays the merchant in USDC on Arbitrum One, and prints the gated JSON plus Arbiscan link.

## Prerequisites

- Python 3.10+
- [uv](https://docs.astral.sh/uv/) installed (`curl -LsSf https://astral.sh/uv/install.sh | sh`)
- AWS credentials configured (`aws sts get-caller-identity` works)
- A Coinbase CDP API key JSON file (downloaded from the CDP portal) with **Delegated signing** enabled at Embedded Wallets > Policies
- A CDP **Wallet Secret** (separate from the API key); set as `CDP_WALLET_SECRET` in `.env`
- The merchant deployed (run `make deploy-merchant` from the repo root) and `RESOURCE_URL` set in `.env`
- An AgentCore Payments service role named `AgentCorePaymentsResourceRetrievalRole` (or set `AGENTCORE_SERVICE_ROLE_ARN` in `.env` to override). See the [AWS IAM docs](https://docs.aws.amazon.com/bedrock-agentcore/latest/devguide/payments-iam-roles.html) for the trust policy and base permissions

## Install

```bash
cd apps/agent && uv sync
```

Or from the repo root: `make install`.

## Run

From the repo root:

```bash
# One-time bootstrap (creates manager, connector, instrument, session)
make setup-agent

# Follow the printed instructions to fund the wallet via Coinbase WalletHub,
# then paste the three PAYMENT_* IDs into the repo root .env.

# Per-demo run
make run-agent

# Cleanup
make teardown-agent
```

## What each script does

| Script | What it does |
|:-------|:-------------|
| `x402-aws-agent-setup` | Creates `PaymentCredentialProvider` from CDP creds; creates `PaymentManager` + `PaymentConnector`; creates `PaymentInstrument` (embedded ETHEREUM wallet); prints the Coinbase WalletHub redirect URL and waits for you to fund + grant permissions; creates a `PaymentSession` with the configured budget |
| `x402-aws-agent-run` | Reads the IDs from `.env`, GETs `RESOURCE_URL`, on 402 calls `PaymentManager.generate_payment_header()` and retries with the proof, prints the gated JSON |
| `x402-aws-agent-teardown` | Deletes session, instrument, connectors, and manager. Run before re-running setup or to stop being billed for resource provisioning |

## Tests

```bash
cd apps/agent && uv run pytest
```

7 tests: config validation, the x402 402-pay-retry HTTP flow against `httpx.MockTransport`.

## Why no Strands plugin?

This demo is a single deterministic GET. The Strands plugin shines when an LLM agent picks paid endpoints from a tool catalog; for a one-shot, scripted call, the lower-level `PaymentManager.generate_payment_header()` keeps the code transparent and inspectable. To upgrade later, install `bedrock-agentcore[strands-agents]` (already in deps), instantiate `AgentCorePaymentsPlugin`, and pass it to a Strands `Agent` with the `http_request` tool. See [AWS docs](https://docs.aws.amazon.com/bedrock-agentcore/latest/devguide/payments-process-payment.html).

## Network preferences

The merchant only accepts `eip155:42161` (Arbitrum One) in its `accepts` payload. The agent passes `network_preferences=["eip155:42161"]` explicitly so AgentCore's default preference list (which prioritizes Solana mainnet and Base) does not interfere.

## File layout

```
src/x402_aws_agent/
├── __init__.py
├── config.py           # .env loader + validation
├── http_client.py      # The 402-pay-retry flow (isolated, unit-tested)
├── setup.py            # Bootstrap CLI
├── run.py              # Per-demo CLI
└── teardown.py         # Cleanup CLI

tests/
├── test_config.py      # 4 tests
└── test_http_client.py # 3 tests
```
