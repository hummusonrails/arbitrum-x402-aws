# Part 5: Configure your `.env`

[← Part 4: Local setup](04-local-setup.md) · [Back to overview](README.md) · [Part 6: Deploy the merchant →](06-deploy-merchant.md)

Both stacks read a single `.env` file at the **repo root**. This part explains
every variable and exactly where its value comes from. Some values you have
already (from Parts 1–3); a few you'll fill in later (Parts 6 and 7). That's
expected, you'll come back to this file twice.

## 1. Create the file

From the repo root:

```bash
cp .env.example .env
```

Open `.env` in your editor. Below is every variable, grouped by when you set it.

## 2. Values you already have (from Parts 1–3)

### CDP API key: `CDP_API_KEY_ID` and `CDP_PRIVATE_KEY`

These come from the **Secret API key JSON file** you downloaded in
[Part 1](01-coinbase-cdp.md). Rather than copy/paste the multi-line PEM by hand,
use the helper script, which reads the JSON, smoke-tests that the key signs, and
prints two ready-to-paste lines:

```bash
pnpm --filter @x402-aws/merchant print-cdp-env /path/to/cdp_api_key.json
```

Output looks like:

```
CDP_API_KEY_ID=organizations/.../apiKeys/...
CDP_PRIVATE_KEY="-----BEGIN PRIVATE KEY-----\nMIG...\n-----END PRIVATE KEY-----\n"
```

Paste both lines into `.env`, replacing the empty placeholders.

> The script handles both key-id field names CDP uses (`id` and `name`) and
> escapes the PEM newlines so the value stays on one line. Keep the double
> quotes around `CDP_PRIVATE_KEY`.

### Wallet secret: `CDP_WALLET_SECRET`

The **Wallet Secret** you generated in [Part 1](01-coinbase-cdp.md) (Embedded
Wallets, with delegated signing enabled). Paste it directly:

```
CDP_WALLET_SECRET=your-wallet-secret-here
```

### Path to the key file: `CDP_API_KEY_FILE`

The agent's `setup-agent` step re-reads the same JSON to provision the wallet.
Point this at the file you downloaded. A relative path is resolved against the
**repo root** (not your current directory):

```
CDP_API_KEY_FILE=./cdp_api_key.json
```

> The simplest setup is to copy your downloaded key to the repo root as
> `cdp_api_key.json`. It's already covered by `.gitignore` patterns for secrets,
> but double-check it never gets committed.

### AgentCore region: `AGENTCORE_REGION`

Must be one of the AgentCore Payments preview regions: `us-east-1`,
`us-west-2`, `eu-central-1`, `ap-southeast-2`. Use the same region you set up
your IAM role and CLI in ([Part 2](02-aws-account-cli.md) /
[Part 3](03-aws-agentcore-iam.md)). The merchant always deploys to `us-east-1`,
so `us-east-1` is the simplest choice:

```
AGENTCORE_REGION=us-east-1
```

### Service role override: `AGENTCORE_SERVICE_ROLE_ARN` (optional)

Leave this commented out. The agent defaults to
`arn:aws:iam::<your-account>:role/AgentCorePaymentsResourceRetrievalRole`, the
exact role you created in [Part 3](03-aws-agentcore-iam.md). Only set this if you
named the role something else.

## 3. Values you choose

### Who gets paid: `RECIPIENT_ADDRESS`

The EVM address that **receives** the USDC on Arbitrum One. This is the
merchant's payout address. Use any Arbitrum One wallet you control (for example
your own MetaMask address). This is **not** the agent's wallet, the agent's
wallet is created later and *pays* this address.

```
RECIPIENT_ADDRESS=0xYourArbitrumOneAddress
```

> [!IMPORTANT]
> This is real USDC on mainnet. If you set the zero address, payments are lost.

### Price per request: `PRICE_USDC`

In USDC base units (6 decimals). The default `10000` = **$0.01**:

```
PRICE_USDC=10000
```

### Agent identity and wallet linkage

| Variable | What to set | Notes |
|:---------|:------------|:------|
| `AGENTCORE_USER_ID` | any stable string | Identifies the wallet owner, e.g. `x402-aws-demo-user` |
| `AGENTCORE_PROVIDER` | `CoinbaseCDP` | This demo wires up Coinbase CDP |
| `AGENTCORE_LINKED_EMAIL` | your email | Linked to the embedded wallet; you'll log into Coinbase WalletHub with it in [Part 7](07-run-the-agent.md) |
| `AGENTCORE_MAX_SPEND_USD` | `1.00` | Per-run spending cap (USD) |
| `AGENTCORE_SESSION_EXPIRY_MINUTES` | `60` | How long a payment session stays valid |

```
AGENTCORE_USER_ID=x402-aws-demo-user
AGENTCORE_PROVIDER=CoinbaseCDP
AGENTCORE_LINKED_EMAIL=you@example.com
AGENTCORE_MAX_SPEND_USD=1.00
AGENTCORE_SESSION_EXPIRY_MINUTES=60
```

## 4. Values you'll fill in later (leave blank for now)

| Variable | Filled in | Source |
|:---------|:----------|:-------|
| `RESOURCE_URL` | [Part 6](06-deploy-merchant.md) | The merchant's `DistributionDomainName` + `/report` |
| `PAYMENT_MANAGER_ARN` | [Part 7](07-run-the-agent.md) | Printed by `make setup-agent` |
| `PAYMENT_INSTRUMENT_ID` | [Part 7](07-run-the-agent.md) | Printed by `make setup-agent` |
| `PAYMENT_SESSION_ID` | [Part 7](07-run-the-agent.md) | Printed by `make setup-agent` |

Leave these as-is for now:

```
RESOURCE_URL=https://example.cloudfront.net/report
PAYMENT_MANAGER_ARN=
PAYMENT_INSTRUMENT_ID=
PAYMENT_SESSION_ID=
```

## 5. Sanity check

At this point `.env` should have **no empty values** in the "already have" and
"you choose" sections. The four "later" values can stay blank/placeholder.

Here's what a complete file looks like at this stage (values are illustrative
placeholders, use your own). The `RESOURCE_URL` and `PAYMENT_*` lines get their
real values in Parts 6 and 7:

```dotenv
# --- CDP (Part 1) ---
CDP_API_KEY_ID=organizations/11111111-1111-1111-1111-111111111111/apiKeys/22222222-2222-2222-2222-222222222222
CDP_PRIVATE_KEY="-----BEGIN PRIVATE KEY-----\nMIGHAgEAMBMGByqGSM49Ag...REDACTED...\n-----END PRIVATE KEY-----\n"
CDP_WALLET_SECRET=your-wallet-secret-here
CDP_API_KEY_FILE=./cdp_api_key.json

# --- Merchant (Parts 5–6) ---
RECIPIENT_ADDRESS=0xYourArbitrumOnePayoutAddress
PRICE_USDC=10000
RESOURCE_URL=https://example.cloudfront.net/report   # set in Part 6

# --- AgentCore (Parts 1–3) ---
AGENTCORE_REGION=us-east-1
AGENTCORE_USER_ID=x402-aws-demo-user
AGENTCORE_PROVIDER=CoinbaseCDP
AGENTCORE_LINKED_EMAIL=you@example.com
AGENTCORE_MAX_SPEND_USD=1.00
AGENTCORE_SESSION_EXPIRY_MINUTES=60
# AGENTCORE_SERVICE_ROLE_ARN=        # optional override; leave commented

# --- Filled in by setup-agent (Part 7) ---
PAYMENT_MANAGER_ARN=
PAYMENT_INSTRUMENT_ID=
PAYMENT_SESSION_ID=
```

---

**Next:** [Part 6 deploys the merchant](06-deploy-merchant.md) and gives you the
`RESOURCE_URL` to paste back into this file.
