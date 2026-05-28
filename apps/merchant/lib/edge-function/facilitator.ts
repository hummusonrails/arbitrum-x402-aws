import type {
  EdgeConfig,
  FacilitatorSettleResponse,
  FacilitatorVerifyResponse,
  PaymentRequirements,
} from "@x402-aws/shared";
import { mintJwt } from "./mint-jwt";

function buildHeaders(config: EdgeConfig, url: string, method: string): Record<string, string> {
  const headers: Record<string, string> = { "content-type": "application/json" };
  if (config.cdpApiKeyId && config.cdpPrivateKey) {
    const jwt = mintJwt({
      apiKeyId: config.cdpApiKeyId,
      privateKeyPem: config.cdpPrivateKey,
      method,
      url,
    });
    headers["authorization"] = `Bearer ${jwt}`;
  }
  return headers;
}

// The CDP facilitator's x402V2PaymentRequirements wants `amount`, not `maxAmountRequired`.
function toFacilitatorRequirements(requirements: PaymentRequirements): Record<string, unknown> {
  return { ...requirements, amount: requirements.maxAmountRequired };
}

async function callFacilitator<T>(
  url: string,
  config: EdgeConfig,
  paymentPayload: unknown,
  requirements: PaymentRequirements
): Promise<T> {
  const res = await fetch(url, {
    method: "POST",
    headers: buildHeaders(config, url, "POST"),
    body: JSON.stringify({
      x402Version: 2,
      paymentPayload,
      paymentRequirements: toFacilitatorRequirements(requirements),
    }),
  });
  if (!res.ok) {
    const text = await res.text();
    throw new Error(`Facilitator returned ${res.status}: ${text}`);
  }
  return (await res.json()) as T;
}

export function verifyPayment(
  config: EdgeConfig,
  paymentPayload: unknown,
  requirements: PaymentRequirements
): Promise<FacilitatorVerifyResponse> {
  return callFacilitator<FacilitatorVerifyResponse>(
    `${config.cdpFacilitatorUrl}/verify`,
    config,
    paymentPayload,
    requirements
  );
}

export function settlePayment(
  config: EdgeConfig,
  paymentPayload: unknown,
  requirements: PaymentRequirements
): Promise<FacilitatorSettleResponse> {
  return callFacilitator<FacilitatorSettleResponse>(
    `${config.cdpFacilitatorUrl}/settle`,
    config,
    paymentPayload,
    requirements
  );
}
