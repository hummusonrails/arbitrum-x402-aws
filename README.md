<!-- Banner -->
<p align="center">
  <img src=".github/banner.svg" alt="arbitrum-x402-aws" width="100%">
</p>

<!-- Badges -->
<p align="center">
  <a href="LICENSE"><img src="https://img.shields.io/badge/License-MIT-blue.svg?style=flat-square" alt="License: MIT"></a>
  <a href="https://nodejs.org/"><img src="https://img.shields.io/badge/Node-20.x-339933.svg?style=flat-square" alt="Node 20"></a>
  <a href="https://pnpm.io/"><img src="https://img.shields.io/badge/pnpm-9.x-F69220.svg?style=flat-square" alt="pnpm 9"></a>
  <a href="https://www.python.org/"><img src="https://img.shields.io/badge/Python-3.10+-3776AB.svg?style=flat-square" alt="Python 3.10+"></a>
  <a href="https://docs.astral.sh/uv/"><img src="https://img.shields.io/badge/uv-0.x-261230.svg?style=flat-square" alt="uv"></a>
  <a href="https://www.typescriptlang.org/"><img src="https://img.shields.io/badge/TypeScript-5.x-3178C6.svg?style=flat-square" alt="TypeScript 5"></a>
  <a href="https://aws.amazon.com/cdk/"><img src="https://img.shields.io/badge/AWS_CDK-2.x-FF9900.svg?style=flat-square" alt="AWS CDK 2"></a>
  <a href="https://aws.amazon.com/bedrock/agentcore/"><img src="https://img.shields.io/badge/Bedrock_AgentCore-preview-FF9900.svg?style=flat-square" alt="Bedrock AgentCore"></a>
  <a href="https://arbitrum.io/"><img src="https://img.shields.io/badge/Arbitrum-One-12AAFF.svg?style=flat-square" alt="Arbitrum One"></a>
  <a href="https://www.x402.org/"><img src="https://img.shields.io/badge/x402-v2-8B5CF6.svg?style=flat-square" alt="x402 v2"></a>
</p>

<p align="center">
  <strong>End-to-end x402 payments on Arbitrum One. AWS CloudFront + Lambda@Edge merchant, paid by an AWS Bedrock AgentCore Python agent. USDC settles on Arbitrum One via Coinbase CDP.</strong>
</p>

<p align="center">
  <strong>New to CDP or AWS AgentCore?</strong> The <a href="docs/getting-started/README.md">zero-knowledge Getting Started guide</a> walks you from no accounts to a paid request, click by click.
</p>

## What's in this repo

| App | Path | Language | Role |
|:----|:-----|:---------|:-----|
| Merchant | [`apps/merchant`](apps/merchant/README.md) | TypeScript (pnpm) | Returns HTTP 402, verifies + settles via CDP facilitator, serves gated JSON |
| Agent | [`apps/agent`](apps/agent/README.md) | Python (uv) | Holds embedded wallet via AgentCore, pays on 402, retries with proof |
| `@x402-aws/shared` | [`packages/shared`](packages/shared) | TypeScript (pnpm) | x402 v2 protocol types + Arbitrum constants |

## Architecture

```mermaid
graph LR
    subgraph AC[AWS AgentCore]
      A[Python Agent<br/>PaymentManager]
      W[Embedded Wallet<br/>Coinbase CDP]
      A --> W
    end
    subgraph AWS[AWS us-east-1]
      CF[CloudFront]
      LE[Lambda Edge<br/>402 Handler]
      AG[API Gateway]
      OL[Origin Lambda]
    end
    CDP[CDP Facilitator]
    L1[Arbitrum One USDC]

    A -->|GET /report| CF
    CF -.->|viewer-request| LE
    LE -->|verify+settle| CDP
    CDP -->|EIP 3009| L1
    LE -->|on payment| AG
    AG --> OL

    classDef aws fill:#FF9900,stroke:#fff,color:#0b1018
    classDef arb fill:#12AAFF,stroke:#fff,color:#0b1018
    classDef agent fill:#8B5CF6,stroke:#fff,color:#fff
    classDef cdp fill:#1652F0,stroke:#fff,color:#fff
    class CF,LE,AG,OL,AC aws
    class L1 arb
    class A,W agent
    class CDP cdp
```

## End-to-end flow

```mermaid
sequenceDiagram
    autonumber
    participant A as Python Agent
    participant ACore as AgentCore<br/>PaymentManager
    participant CF as CloudFront
    participant LE as Lambda Edge
    participant CDP as CDP Facilitator
    participant L1 as Arbitrum One

    A->>CF: GET /report
    CF->>LE: viewer-request
    LE-->>A: 402 + accepts[]
    A->>ACore: generate_payment_header(402 body)
    Note over ACore: Check session budget,<br/>sign via embedded wallet
    ACore-->>A: X-PAYMENT header
    A->>CF: GET /report (X-PAYMENT)
    CF->>LE: viewer-request
    LE->>CDP: verify + settle
    CDP->>L1: transferWithAuthorization
    L1-->>CDP: tx hash
    CDP-->>LE: success + txHash
    LE-->>A: 200 + gated JSON + Arbiscan link
```

<!-- Featured -->
<p align="center">
  <a href="https://x.com/hummusonrails/status/2049363842283544939">
    <img src=".github/x402-on-arbitrum-meets-aws.jpg" alt="x402 on Arbitrum meets AWS, read the article on X" width="640">
  </a>
</p>
<p align="center">
  <sub><strong>Featured on X</strong> &middot; <a href="https://x.com/hummusonrails/status/2049363842283544939">The narrative behind this synthesis of x402, Arbitrum, and AWS &rarr;</a></sub>
</p>

## Quick Start

> This Quick Start assumes you already have CDP and AWS accounts, credentials, and tooling set up. If you don't, follow the [**Getting Started guide**](docs/getting-started/README.md) instead, it covers account creation, credentials, IAM, and every `.env` value with screenshots.

```bash
# 1. Install both stacks
make install

# 2. Configure
cp .env.example .env
$EDITOR .env   # set RECIPIENT_ADDRESS, AGENTCORE_*, etc.

# 3. Print CDP env for the merchant
pnpm --filter @x402-aws/merchant print-cdp-env /path/to/cdp_api_key.json
# Paste the printed lines into .env

# 4. Bootstrap CDK
pnpm --filter @x402-aws/merchant exec cdk bootstrap aws://$ACCOUNT_ID/us-east-1

# 5. Deploy the merchant
make deploy-merchant

# 6. Set RESOURCE_URL in .env from the merchant's DistributionDomainName output

# 7. Bootstrap the agent (creates AgentCore resources, prompts you to fund the wallet)
make setup-agent

# 8. Paste the printed PAYMENT_* IDs into .env

# 9. Run the agent
make run-agent
```

## Makefile

| Target | What it does |
|:-------|:-------------|
| `make install` | `pnpm install` + `uv sync` |
| `make test` | All tests across both stacks |
| `make synth` | CDK synth for the merchant |
| `make deploy-merchant` | CDK deploy |
| `make destroy-merchant` | CDK destroy |
| `make setup-agent` | Bootstrap AgentCore resources (one-time) |
| `make run-agent` | Run the agent against the merchant |
| `make teardown-agent` | Delete AgentCore resources |
| `make clean` | Remove all build artifacts and venvs |

## Tests

```bash
make test
```

26 tests: 17 in the merchant (vitest), 2 in `@x402-aws/shared` (vitest), 7 in the agent (pytest).

## Stack

| Layer | Tool |
|:------|:-----|
| Workspace | pnpm 9+ (apps/merchant, packages/*) + uv (apps/agent) + root Makefile |
| Merchant IaC | AWS CDK 2 (TypeScript) |
| CDN / edge | CloudFront + Lambda@Edge (Node 20, x86_64) |
| Origin | API Gateway HTTP API + Lambda (Node 20, ARM) |
| Settlement | CDP x402 facilitator |
| Agent runtime | Python 3.10+, `boto3`, `bedrock-agentcore[strands-agents]`, `httpx` |
| Wallet | AgentCore embedded wallet, Coinbase CDP |
| Chain | Arbitrum One (CAIP-2 `eip155:42161`) |
| Asset | Native USDC (`0xaf88d065e77c8cC2239327C5EDb3A432268e5831`) |

## Contributing

PRs welcome. Open an issue first for anything non-trivial.

## License

MIT. See [LICENSE](LICENSE).
