#!/usr/bin/env node
import * as path from "node:path";
import * as dotenv from "dotenv";
// Load .env From Repo Root Not Provider Directory
dotenv.config({ path: path.resolve(__dirname, "..", "..", "..", ".env") });

import * as cdk from "aws-cdk-lib";
import { ProviderStack } from "../lib/provider-stack";
import { NETWORK } from "../lib/networks";

const app = new cdk.App();

const recipientAddress =
  process.env.RECIPIENT_ADDRESS ?? "0x0000000000000000000000000000000000000000";
if (recipientAddress === "0x0000000000000000000000000000000000000000") {
  console.warn(
    "WARNING: RECIPIENT_ADDRESS is not set in .env. Using zero address placeholder. " +
      "This is fine for `cdk bootstrap` and `cdk synth`, but set a real address before " +
      "running `cdk deploy` for the actual demo, otherwise USDC payments go to address(0)."
  );
}

const priceUsdc =
  (app.node.tryGetContext("priceUsdc") as string) ?? process.env.PRICE_USDC ?? "10000";

const cdpApiKeyId = process.env.CDP_API_KEY_ID ?? "";
const cdpPrivateKey = process.env.CDP_PRIVATE_KEY ?? "";

if (!cdpApiKeyId || !cdpPrivateKey) {
  console.warn(
    "WARNING: CDP_API_KEY_ID or CDP_PRIVATE_KEY is not set in .env. " +
      "The edge function will not be able to authenticate to the CDP facilitator. " +
      "Fine for `cdk bootstrap` and `cdk synth`, but set both before `cdk deploy` for the demo."
  );
}

new ProviderStack(app, "X402ProviderStack", {
  env: { region: "us-east-1" },
  network: NETWORK,
  recipientAddress,
  priceUsdc,
  cdpApiKeyId,
  cdpPrivateKey,
});
