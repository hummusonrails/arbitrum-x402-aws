# Provider (AWS CDK)

CloudFront with a Lambda@Edge function on `viewer-request` in front of an API Gateway HTTP API backed by a Lambda. The edge function returns HTTP 402 with payment terms, calls the CDP facilitator's `/verify` and `/settle` endpoints on retry, and passes the request through to the origin on successful settlement.

## Prerequisites

- Node 20+
- AWS account with credentials configured (`aws configure` or env vars)
- CDK bootstrapped in `us-east-1`: `npx cdk bootstrap aws://<account>/us-east-1`
- A CDP API key from https://portal.cdp.coinbase.com (download the JSON file)
- A funded recipient address on Arbitrum One
- `.env` filled from `.env.example` at the repo root

## Deploy

From the repo root:

```bash
cd provider
npm install
npx cdk deploy
```

The stack outputs `DistributionDomainName`. Set this as `RESOURCE_URL=https://<domain>/report` in `.env` for the agent.

## Setting up CDP auth

CDP uses JWT-based authentication where the JWT is **bound to the specific request URL and method**, signed with an EC private key, and **expires in 2 minutes**. This means tokens cannot be pre-minted and pasted into `.env`. Instead, the edge function receives the API key ID and the EC private key (PEM) and mints a fresh JWT for each `/verify` and `/settle` call using `node:crypto`.

### Get a CDP API key

1. Sign in at https://portal.cdp.coinbase.com
2. Create a new API key. Don't check any extra permission scopes (x402 doesn't need them).
3. Download the JSON file. It contains `name` (the key id) and `privateKey` (PEM).
4. Save the file somewhere safe. You can't redownload it.

### Populate `.env` from the JSON file

A helper script reads the JSON and prints `.env`-ready lines:

```bash
cd provider
npx ts-node scripts/print-cdp-env.ts /path/to/cdp_api_key.json
```

Output looks like:

```
CDP_API_KEY_ID=organizations/.../apiKeys/...
CDP_PRIVATE_KEY="-----BEGIN PRIVATE KEY-----\nMIG...\n-----END PRIVATE KEY-----\n"
```

Paste those two lines into the repo root `.env`. The script also smoke-tests that the key signs correctly before printing.

### How tokens flow at runtime

1. CDK synth inlines `cdpApiKeyId` and `cdpPrivateKey` from `.env` into the Lambda@Edge bundle (via esbuild's `define`).
2. Per request, the edge function calls `mintJwt(...)` with the verify or settle URL.
3. The signed JWT is sent as `Authorization: Bearer <jwt>` to CDP.
4. The token is valid for 120 seconds. Each call mints a new one. No rotation needed.

## Iterating on the edge function

Lambda@Edge has a 5 to 15 minute propagation window after deploy. To keep the dev loop short:

1. Edit `lib/edge-function/index.ts` (or its helpers).
2. Run `npm test` to verify the handler logic.
3. Only run `npx cdk deploy` when the unit tests pass.
4. Expect a coffee break before the next live test.

## Smoke test after deploy

```bash
# Expect 402 with payment terms
curl -i https://<DistributionDomainName>/report

# Expect 200 with the gated JSON after the agent pays
ows pay request https://<DistributionDomainName>/report --wallet x402-demo
```

Open the printed Arbiscan link to confirm the on chain settlement.

## Settlement timing trade off

This implementation calls `/verify` then `/settle` in `viewer-request` before passing through to the origin (Option A in the design doc). Production deployments should split this across `viewer-request` (verify) and `viewer-response` (settle) so that settlement only happens after successful delivery (Option B). The relevant call site is `handler` in `lib/edge-function/index.ts` immediately after the `verifyPayment` success branch.

## Secrets

`CDP_API_KEY_ID` and `CDP_PRIVATE_KEY` from `.env` are loaded at synth time via dotenv and inlined into the edge bundle. Lambda@Edge cannot read env vars at runtime so this is the standard workaround. The inlined values are visible to anyone with `lambda:GetFunction` on this AWS account. The EC private key in the bundle is the most sensitive material in the deployment, so apply IAM least privilege to who can read Lambda code.

## CloudWatch logs

Edge function logs land in the CloudWatch region nearest the edge that handled the request, not us-east-1. Origin Lambda logs land in us-east-1. Use the `EdgeFunctionArn` stack output to look up the function in the right region.

## Tests

```bash
npm test
```

Runs the vitest suite covering the origin handler, the edge `buildPaymentRequirements` builder, the facilitator client, and all six branches of the edge handler (no header, valid payment, verify failure, settle failure, malformed header, facilitator network error).
