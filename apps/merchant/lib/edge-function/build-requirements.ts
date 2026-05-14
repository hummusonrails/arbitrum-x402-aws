import { EdgeConfig, PaymentRequirements } from "./types";

export function buildPaymentRequirements(config: EdgeConfig, resourceUrl: string): PaymentRequirements {
  return {
    scheme: "exact",
    network: config.caip2,
    maxAmountRequired: config.priceUsdc,
    resource: resourceUrl,
    description: "Premium Market Data Snapshot",
    mimeType: "application/json",
    payTo: config.recipientAddress,
    maxTimeoutSeconds: 300,
    asset: config.usdc,
    extra: { name: "USD Coin", version: "2" },
  };
}
