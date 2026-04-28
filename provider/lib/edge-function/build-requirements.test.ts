import { describe, it, expect } from "vitest";
import { buildPaymentRequirements } from "./build-requirements";
import { EdgeConfig } from "./types";

const config: EdgeConfig = {
  caip2: "eip155:42161",
  usdc: "0xUSDC",
  recipientAddress: "0xRECIPIENT",
  priceUsdc: "10000",
  cdpFacilitatorUrl: "https://facilitator.example",
  cdpAuthHeader: "",
};

describe("buildPaymentRequirements", () => {
  it("returns exact scheme with the configured network and asset", () => {
    const req = buildPaymentRequirements(config, "https://x.cloudfront.net/report");
    expect(req.scheme).toBe("exact");
    expect(req.network).toBe("eip155:42161");
    expect(req.asset).toBe("0xUSDC");
    expect(req.payTo).toBe("0xRECIPIENT");
    expect(req.maxAmountRequired).toBe("10000");
    expect(req.resource).toBe("https://x.cloudfront.net/report");
    expect(req.extra).toMatchObject({ name: "USD Coin", version: "2" });
    expect(req.mimeType).toBe("application/json");
    expect(req.maxTimeoutSeconds).toBe(300);
  });
});
