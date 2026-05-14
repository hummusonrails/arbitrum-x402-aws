import { describe, expect, it } from "vitest";
import { NETWORK, type PaymentRequirements } from "./index";

describe("@x402-aws/shared", () => {
  it("exports Arbitrum One network constants", () => {
    expect(NETWORK.chainId).toBe(42161);
    expect(NETWORK.caip2).toBe("eip155:42161");
    expect(NETWORK.usdc).toBe("0xaf88d065e77c8cC2239327C5EDb3A432268e5831");
    expect(NETWORK.arbiscanTxBase).toBe("https://arbiscan.io/tx/");
    expect(NETWORK.cdpFacilitatorUrl).toBe(
      "https://api.cdp.coinbase.com/platform/v2/x402"
    );
  });

  it("PaymentRequirements shape compiles with x402 v2 fields", () => {
    const req: PaymentRequirements = {
      scheme: "exact",
      network: "eip155:42161",
      maxAmountRequired: "10000",
      resource: "https://example.com/report",
      description: "test",
      mimeType: "application/json",
      payTo: "0x0000000000000000000000000000000000000000",
      maxTimeoutSeconds: 300,
      asset: "0xaf88d065e77c8cC2239327C5EDb3A432268e5831",
      extra: { name: "USD Coin", version: "2" },
    };
    expect(req.scheme).toBe("exact");
  });
});
