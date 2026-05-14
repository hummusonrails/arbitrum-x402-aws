export interface EdgeConfig {
  caip2: string;
  usdc: string;
  recipientAddress: string;
  priceUsdc: string;
  cdpFacilitatorUrl: string;
  cdpApiKeyId: string;
  cdpPrivateKey: string;
}

// x402 v2 PaymentRequirements (the shape inside the 402 response's accepts[])
// Mirrors the AWS AgentCore docs naming for cross-stack readability.
export interface PaymentRequirements {
  scheme: "exact";
  network: string;
  maxAmountRequired: string;
  resource: string;
  description: string;
  mimeType: string;
  payTo: string;
  maxTimeoutSeconds: number;
  asset: string;
  extra: { name: string; version: string };
}

export interface FacilitatorVerifyResponse {
  isValid: boolean;
  invalidReason?: string;
}

export interface FacilitatorSettleResponse {
  success: boolean;
  txHash?: string;
  errorReason?: string;
}
