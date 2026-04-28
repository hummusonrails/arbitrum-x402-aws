# Agent (OWS CLI)

The agent is a single OWS CLI command. It performs the full x402 handshake (parse the 402 response, sign an EIP-3009 USDC authorization, retry with the `X-PAYMENT` header, and return the gated payload).

## Install OWS

```bash
curl -fsSL https://docs.openwallet.sh/install.sh | bash
```

Verify with `ows --version` (need v1.2.4 or newer).

## Create a demo wallet

```bash
ows wallet create x402-demo --show-mnemonic
```

Save the mnemonic somewhere safe. This is a hot key for demo use only, never reuse it for real funds.

Show the wallet's EVM address:

```bash
ows wallet info --wallet x402-demo
```

## Fund the wallet

This demo runs on Arbitrum One mainnet. Bridge approximately $0.50 of USDC to the wallet's EVM address on Arbitrum One. Each demo run costs around $0.01.

Bridge options:
- Arbitrum's official bridge: https://bridge.arbitrum.io

## Run the agent

From the agent directory:

```bash
bash run.sh
```

Or directly:

```bash
ows pay request "$RESOURCE_URL" --wallet x402-demo
```

`RESOURCE_URL` and `OWS_WALLET` come from the repo root `.env` file.

The first request returns 402, OWS signs the authorization, retries with the `X-PAYMENT` header, and prints the gated JSON. Open the printed Arbiscan link to confirm settlement on chain.

## What's happening under the hood

OWS does three things in a single command:

1. Sends the initial GET, receives 402, parses the payment terms (`network`, `asset`, `payTo`, `maxAmountRequired`).
2. Signs an EIP-3009 `transferWithAuthorization` typed data message using the wallet's encrypted private key. The key is decrypted inside the OWS Rust core, used for signing, then immediately wiped from memory. The caller never sees the raw key.
3. Retries the GET with the signed payload base64 encoded in the `X-PAYMENT` header.

The provider's edge function then verifies the payment with the CDP facilitator, settles it on Arbitrum One, and lets the request through to the origin.
