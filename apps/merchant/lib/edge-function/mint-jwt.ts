import { createPrivateKey, KeyObject, randomBytes, sign } from "node:crypto";

export interface MintJwtArgs {
  apiKeyId: string;
  privateKeyPem: string;
  method: string;
  url: string;
}

function base64url(buf: Buffer | string): string {
  return Buffer.from(buf).toString("base64url");
}

// Ed25519 PKCS8 DER Prefix For Wrapping A Raw 32 Byte Seed
const ED25519_PKCS8_PREFIX = Buffer.from("302e020100300506032b657004220420", "hex");

// Load Private Key Supporting PEM Or Raw Base64 And Detect Algorithm
function loadPrivateKey(input: string): { key: KeyObject; alg: "ES256" | "EdDSA" } {
  let key: KeyObject;

  if (input.includes("-----BEGIN")) {
    // Normalize Escaped Newlines That Sometimes Appear When Loading From Env
    const normalized = input.replace(/\\n/g, "\n");
    key = createPrivateKey(normalized);
  } else {
    // Assume Raw Base64 Ed25519 Seed (32 Bytes) Or Seed Plus Public Key (64 Bytes)
    const raw = Buffer.from(input.trim(), "base64");
    let seed: Buffer;
    if (raw.length === 32) {
      seed = raw;
    } else if (raw.length === 64) {
      seed = raw.subarray(0, 32);
    } else {
      throw new Error(
        `Could not parse private key. PEM not detected and raw base64 length is ${raw.length}, expected 32 or 64 bytes for Ed25519.`
      );
    }
    const pkcs8 = Buffer.concat([ED25519_PKCS8_PREFIX, seed]);
    key = createPrivateKey({ key: pkcs8, format: "der", type: "pkcs8" });
  }

  if (key.asymmetricKeyType === "ed25519") {
    return { key, alg: "EdDSA" };
  }
  if (key.asymmetricKeyType === "ec") {
    return { key, alg: "ES256" };
  }
  throw new Error(`Unsupported CDP private key type: ${key.asymmetricKeyType}`);
}

// Mint Short Lived JWT For CDP API Calls
// CDP Requires Per Request Tokens Bound To Method And URL With Two Minute Expiry
export function mintJwt(args: MintJwtArgs): string {
  const parsed = new URL(args.url);
  const uri = `${args.method.toUpperCase()} ${parsed.host}${parsed.pathname}`;

  const { key, alg } = loadPrivateKey(args.privateKeyPem);

  const header = {
    alg,
    typ: "JWT",
    kid: args.apiKeyId,
    nonce: randomBytes(16).toString("hex"),
  };

  const now = Math.floor(Date.now() / 1000);
  const payload = {
    sub: args.apiKeyId,
    iss: "cdp",
    aud: ["cdp_service"],
    nbf: now,
    exp: now + 120,
    uri,
  };

  const signingInput = `${base64url(JSON.stringify(header))}.${base64url(JSON.stringify(payload))}`;

  let signature: Buffer;
  if (alg === "EdDSA") {
    signature = sign(null, Buffer.from(signingInput), key);
  } else {
    signature = sign("SHA256", Buffer.from(signingInput), {
      key,
      dsaEncoding: "ieee-p1363",
    });
  }

  return `${signingInput}.${base64url(signature)}`;
}
