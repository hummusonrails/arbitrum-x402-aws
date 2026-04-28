import { describe, it, expect } from "vitest";
import { generateKeyPairSync, verify } from "node:crypto";
import { mintJwt } from "./mint-jwt";

function newEcKeyPair() {
  return generateKeyPairSync("ec", { namedCurve: "P-256" });
}

function newEd25519KeyPair() {
  return generateKeyPairSync("ed25519");
}

function decodeBase64Url(input: string): Buffer {
  return Buffer.from(input, "base64url");
}

describe("mintJwt with EC P-256 key (ES256)", () => {
  it("produces a valid JWT bound to the URI with required claims", () => {
    const { publicKey, privateKey } = newEcKeyPair();
    const privateKeyPem = privateKey.export({ type: "pkcs8", format: "pem" }) as string;

    const token = mintJwt({
      apiKeyId: "test-key-id",
      privateKeyPem,
      method: "POST",
      url: "https://api.cdp.coinbase.com/platform/v2/x402/verify",
    });

    const parts = token.split(".");
    expect(parts).toHaveLength(3);

    const header = JSON.parse(decodeBase64Url(parts[0]).toString("utf8"));
    expect(header.alg).toBe("ES256");
    expect(header.kid).toBe("test-key-id");

    const payload = JSON.parse(decodeBase64Url(parts[1]).toString("utf8"));
    expect(payload.uri).toBe("POST api.cdp.coinbase.com/platform/v2/x402/verify");
    expect(payload.exp - payload.nbf).toBe(120);

    const signingInput = Buffer.from(`${parts[0]}.${parts[1]}`);
    const signature = decodeBase64Url(parts[2]);
    const ok = verify(
      "SHA256",
      signingInput,
      { key: publicKey, dsaEncoding: "ieee-p1363" },
      signature
    );
    expect(ok).toBe(true);
  });
});

describe("mintJwt with Ed25519 key (EdDSA)", () => {
  it("produces a valid JWT from a PEM Ed25519 private key", () => {
    const { publicKey, privateKey } = newEd25519KeyPair();
    const privateKeyPem = privateKey.export({ type: "pkcs8", format: "pem" }) as string;

    const token = mintJwt({
      apiKeyId: "test-key-id",
      privateKeyPem,
      method: "POST",
      url: "https://api.cdp.coinbase.com/platform/v2/x402/settle",
    });

    const parts = token.split(".");
    const header = JSON.parse(decodeBase64Url(parts[0]).toString("utf8"));
    expect(header.alg).toBe("EdDSA");

    const signingInput = Buffer.from(`${parts[0]}.${parts[1]}`);
    const signature = decodeBase64Url(parts[2]);
    const ok = verify(null, signingInput, publicKey, signature);
    expect(ok).toBe(true);
  });

  it("produces a valid JWT from a raw base64 32 byte Ed25519 seed", () => {
    const { publicKey, privateKey } = newEd25519KeyPair();
    const pkcs8Der = privateKey.export({ type: "pkcs8", format: "der" }) as Buffer;
    // Strip The 16 Byte PKCS8 Prefix To Get The Raw 32 Byte Seed
    const rawSeed = pkcs8Der.subarray(pkcs8Der.length - 32);
    const rawBase64 = rawSeed.toString("base64");

    const token = mintJwt({
      apiKeyId: "test-key-id",
      privateKeyPem: rawBase64,
      method: "POST",
      url: "https://api.cdp.coinbase.com/platform/v2/x402/verify",
    });

    const parts = token.split(".");
    const header = JSON.parse(decodeBase64Url(parts[0]).toString("utf8"));
    expect(header.alg).toBe("EdDSA");

    const signingInput = Buffer.from(`${parts[0]}.${parts[1]}`);
    const signature = decodeBase64Url(parts[2]);
    const ok = verify(null, signingInput, publicKey, signature);
    expect(ok).toBe(true);
  });

  it("includes a unique nonce per call", () => {
    const { privateKey } = newEd25519KeyPair();
    const privateKeyPem = privateKey.export({ type: "pkcs8", format: "pem" }) as string;

    const t1 = mintJwt({ apiKeyId: "k", privateKeyPem, method: "POST", url: "https://example.com/a" });
    const t2 = mintJwt({ apiKeyId: "k", privateKeyPem, method: "POST", url: "https://example.com/a" });

    const h1 = JSON.parse(decodeBase64Url(t1.split(".")[0]).toString("utf8"));
    const h2 = JSON.parse(decodeBase64Url(t2.split(".")[0]).toString("utf8"));
    expect(h1.nonce).not.toBe(h2.nonce);
  });
});
