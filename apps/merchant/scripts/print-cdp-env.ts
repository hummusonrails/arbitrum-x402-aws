#!/usr/bin/env node
// Reads The CDP API Key JSON File And Prints Env Var Lines To Paste Into .env
// Usage  npx ts-node scripts/print-cdp-env.ts /path/to/cdp_api_key.json
//
// CDP gives you a JSON file when you create an API key in the portal.
// The file has two relevant fields  "name" (the key id) and "privateKey" (PEM).
// This script reads them and prints lines suitable for .env.

import { readFileSync, existsSync } from "node:fs";
import { resolve } from "node:path";
import { mintJwt } from "../lib/edge-function/mint-jwt";

const arg = process.argv[2];
if (!arg) {
  console.error("Usage: npx ts-node scripts/print-cdp-env.ts <path-to-cdp-key.json>");
  process.exit(1);
}

const filePath = resolve(arg);
if (!existsSync(filePath)) {
  console.error(`File not found: ${filePath}`);
  process.exit(1);
}

const raw = readFileSync(filePath, "utf8");
let parsed: Record<string, unknown>;
try {
  parsed = JSON.parse(raw);
} catch (err) {
  console.error(`Could not parse JSON: ${err}`);
  process.exit(1);
}

// CDP Sometimes Uses `id` And Sometimes `name` For The Key Identifier
const apiKeyId = (parsed.id ?? parsed.name) as string | undefined;
const privateKey = parsed.privateKey as string | undefined;

if (!apiKeyId || !privateKey) {
  console.error(
    "JSON file must contain `id` (or `name`) and `privateKey` fields. Got keys:",
    Object.keys(parsed)
  );
  process.exit(1);
}

// Verify The Key Actually Signs By Minting A Test JWT
try {
  const test = mintJwt({
    apiKeyId,
    privateKeyPem: privateKey,
    method: "POST",
    url: "https://api.cdp.coinbase.com/platform/v2/x402/verify",
  });
  console.error(`OK signed test JWT (${test.length} chars)`);
} catch (err) {
  console.error(`Failed to sign test JWT with this key: ${err}`);
  process.exit(1);
}

// Output Env Lines To Stdout So User Can Redirect Or Copy
const escapedKey = privateKey.replace(/\n/g, "\\n");
console.log(`CDP_API_KEY_ID=${apiKeyId}`);
console.log(`CDP_PRIVATE_KEY="${escapedKey}"`);
