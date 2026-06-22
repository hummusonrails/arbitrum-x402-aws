# Troubleshooting & teardown

[← Part 7: Run the agent](07-run-the-agent.md) · [Back to overview](README.md)

## Stop being billed: tear down

AgentCore payment resources (manager, connector, instrument, session) can incur
charges while they exist. When you're done, delete them:

```bash
make teardown-agent
```

This deletes the session, instrument, connectors, and manager created in
[Part 7](07-run-the-agent.md). Run it before re-running `make setup-agent` too,
to avoid orphaned resources.

To remove the merchant infrastructure from AWS:

```bash
make destroy-merchant
```

This destroys the CloudFormation stack (CloudFront, Lambdas, API Gateway). The
one-time `CDKToolkit` bootstrap stack and your IAM role are left in place; delete
those manually in the console if you want a completely clean account.

## Common issues

### The merchant returns 403 or hangs instead of 402

CloudFront + Lambda@Edge changes take **5–15 minutes** to propagate to all edge
locations after a deploy. Wait and retry the `curl` before assuming anything is
broken.

### `aws sts get-caller-identity` fails

Your CLI credentials aren't configured. Revisit
[Part 2, step 3](02-aws-account-cli.md). Confirm you're pointed at the right
profile (`AWS_PROFILE`) and region.

### `setup-agent` can't find / assume the role

- Confirm the role exists with the exact name
  `AgentCorePaymentsResourceRetrievalRole`
  (`aws iam get-role --role-name AgentCorePaymentsResourceRetrievalRole`), or set
  `AGENTCORE_SERVICE_ROLE_ARN` in `.env`.
- Confirm the **trust policy** allows `bedrock-agentcore.amazonaws.com` with your
  account in `aws:SourceAccount` and a `payment-manager/*` `SourceArn` for your
  region. See [Part 3](03-aws-agentcore-iam.md).
- Confirm `AGENTCORE_REGION` is one of `us-east-1`, `us-west-2`, `eu-central-1`,
  `ap-southeast-2`, and that your role ARN's region segment matches it.

### "Delegated signing grant is not active for the end user wallet"

The wallet your `.env` points to was never granted (or never funded), usually
because funding/granting happened on a *different* wallet than the one `.env`
points at (e.g. an earlier `--force-new` run, or hand-edited ids).

> `make setup-agent` reuses the existing wallet by default, so simply re-running
> it is safe. Only `--force-new` (or starting from an empty `.env`) creates a new
> wallet that needs its own funding + grant.

Fix it without creating yet another wallet:

1. See which wallet `.env` actually points at, its grant URL, and status:
   ```bash
   cd apps/agent && uv run python ../../scripts/inspect_instrument.py
   ```
2. Open the printed `redirectUrl` (WalletHub), log in with
   `AGENTCORE_LINKED_EMAIL`, and **grant delegated signing** for that wallet.
3. Fund the printed `walletAddress` with USDC on **Arbitrum One** (verify on
   [Arbiscan](https://arbiscan.io), not WalletHub).
4. Re-run `make run-agent`. If the session expired, mint a new one with
   `scripts/new_session.py` and update `PAYMENT_SESSION_ID` first.

> Tip: confirm the wallet is actually funded on-chain (provider-independent):
> ```bash
> curl -s -X POST https://arb1.arbitrum.io/rpc -H 'content-type: application/json' \
>   -d '{"jsonrpc":"2.0","id":1,"method":"eth_call","params":[{"to":"0xaf88d065e77c8cC2239327C5EDb3A432268e5831","data":"0x70a08231000000000000000000000000<WALLET_NO_0x>"},"latest"]}'
> ```
> A non-zero hex result = funded. (`0xaf88…5831` is native USDC on Arbitrum One.)

### "Failed to sign transaction" / signing errors during the run

This is the AgentCore ↔ CDP signing path. Two things to check:

- **Delegated signing must be enabled** in CDP (Embedded Wallets → Policies). See
  [Part 1, step 4](01-coinbase-cdp.md).
- **CDP SDK version.** This repo pins a `cdp-sdk` version known to sign correctly
  against Arbitrum (`apps/agent` deps). If you changed dependencies, re-sync with
  `make install` and don't downgrade `cdp-sdk`.

### Wallet shows no balance in Coinbase WalletHub

WalletHub's balance view focuses on **Base** and may not display funds held on
**Arbitrum One**, and may not offer a Send control. This is a display
limitation, not a missing-funds problem. Verify the real balance on
[Arbiscan](https://arbiscan.io) using the wallet address. Always fund **on the
Arbitrum One network**. See [Part 7, step 2](07-run-the-agent.md).

### Payment exceeds budget / session expired

- `AGENTCORE_MAX_SPEND_USD` caps spend per session; raise it in `.env` and re-run
  `make setup-agent` if needed.
- Sessions expire after `AGENTCORE_SESSION_EXPIRY_MINUTES`. If a run fails with an
  expired session, re-run `make setup-agent` to mint a fresh `PAYMENT_SESSION_ID`
  and update `.env`.

### USDC went to the wrong place

`RECIPIENT_ADDRESS` in `.env` is the merchant payout address and is inlined into
the deployment at synth time. If you change it, **redeploy** the merchant
(`make deploy-merchant`) so the edge function picks up the new address. Never
leave it as the zero address.

### Networks

The agent explicitly sends `network_preferences=["eip155:42161"]` so AgentCore's
defaults (which favor Solana and Base) do not interfere with settlement on
Arbitrum One.

## Still stuck?

- Merchant edge/origin behavior and CloudWatch log locations:
  [`apps/merchant/README.md`](../../apps/merchant/README.md).
- Agent internals and what each script does:
  [`apps/agent/README.md`](../../apps/agent/README.md).
- Open an issue in the repo with the failing command and its output (redact
  secrets and your account ID first).
