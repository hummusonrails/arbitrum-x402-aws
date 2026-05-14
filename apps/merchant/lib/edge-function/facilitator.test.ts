import { describe, it, expect, vi, beforeEach } from "vitest";

vi.mock("./mint-jwt", () => ({
  mintJwt: vi.fn(() => "fake.jwt.token"),
}));

import { verifyPayment, settlePayment } from "./facilitator";
import { mintJwt } from "./mint-jwt";
import { EdgeConfig, PaymentRequirements } from "./types";

const config: EdgeConfig = {
  caip2: "eip155:42161",
  usdc: "0xUSDC",
  recipientAddress: "0xRECIPIENT",
  priceUsdc: "10000",
  cdpFacilitatorUrl: "https://api.cdp.coinbase.com/platform/v2/x402",
  cdpApiKeyId: "test-key-id",
  cdpPrivateKey: "-----BEGIN PRIVATE KEY-----\nfake\n-----END PRIVATE KEY-----",
};

const requirements: PaymentRequirements = {
  scheme: "exact",
  network: "eip155:42161",
  maxAmountRequired: "10000",
  resource: "https://x.cloudfront.net/report",
  description: "Premium Market Data Snapshot",
  mimeType: "application/json",
  payTo: "0xRECIPIENT",
  maxTimeoutSeconds: 300,
  asset: "0xUSDC",
  extra: { name: "USD Coin", version: "2" },
};

const paymentPayload = { mock: "payload" };

beforeEach(() => {
  vi.restoreAllMocks();
  vi.mocked(mintJwt).mockReturnValue("fake.jwt.token");
});

describe("verifyPayment", () => {
  it("mints a JWT bound to the verify URL and POSTs with the bearer header", async () => {
    const fetchMock = vi.fn().mockResolvedValue({
      ok: true,
      json: async () => ({ isValid: true }),
    });
    vi.stubGlobal("fetch", fetchMock);

    const result = await verifyPayment(config, paymentPayload, requirements);

    expect(result).toEqual({ isValid: true });
    expect(mintJwt).toHaveBeenCalledWith({
      apiKeyId: "test-key-id",
      privateKeyPem: config.cdpPrivateKey,
      method: "POST",
      url: "https://api.cdp.coinbase.com/platform/v2/x402/verify",
    });
    expect(fetchMock).toHaveBeenCalledWith(
      "https://api.cdp.coinbase.com/platform/v2/x402/verify",
      expect.objectContaining({
        method: "POST",
        headers: expect.objectContaining({
          "content-type": "application/json",
          authorization: "Bearer fake.jwt.token",
        }),
        body: JSON.stringify({ paymentPayload, paymentRequirements: requirements }),
      })
    );
  });

  it("omits auth header and skips JWT minting when credentials are empty", async () => {
    const fetchMock = vi.fn().mockResolvedValue({ ok: true, json: async () => ({ isValid: true }) });
    vi.stubGlobal("fetch", fetchMock);

    await verifyPayment(
      { ...config, cdpApiKeyId: "", cdpPrivateKey: "" },
      paymentPayload,
      requirements
    );

    expect(mintJwt).not.toHaveBeenCalled();
    const headers = (fetchMock.mock.calls[0][1] as RequestInit).headers as Record<string, string>;
    expect(headers.authorization).toBeUndefined();
  });

  it("returns isValid false with reason when facilitator says so", async () => {
    vi.stubGlobal("fetch", vi.fn().mockResolvedValue({
      ok: true,
      json: async () => ({ isValid: false, invalidReason: "expired" }),
    }));

    const result = await verifyPayment(config, paymentPayload, requirements);
    expect(result).toEqual({ isValid: false, invalidReason: "expired" });
  });

  it("throws on non 2xx response", async () => {
    vi.stubGlobal("fetch", vi.fn().mockResolvedValue({
      ok: false,
      status: 500,
      text: async () => "facilitator down",
    }));

    await expect(verifyPayment(config, paymentPayload, requirements)).rejects.toThrow();
  });
});

describe("settlePayment", () => {
  it("mints a JWT bound to the settle URL", async () => {
    const fetchMock = vi.fn().mockResolvedValue({
      ok: true,
      json: async () => ({ success: true, txHash: "0xabc" }),
    });
    vi.stubGlobal("fetch", fetchMock);

    const result = await settlePayment(config, paymentPayload, requirements);
    expect(result).toEqual({ success: true, txHash: "0xabc" });
    expect(mintJwt).toHaveBeenCalledWith(
      expect.objectContaining({
        method: "POST",
        url: "https://api.cdp.coinbase.com/platform/v2/x402/settle",
      })
    );
    expect(fetchMock).toHaveBeenCalledWith(
      "https://api.cdp.coinbase.com/platform/v2/x402/settle",
      expect.objectContaining({ method: "POST" })
    );
  });
});
