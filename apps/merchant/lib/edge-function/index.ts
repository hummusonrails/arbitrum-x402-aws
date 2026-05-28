import type { CloudFrontRequestEvent, CloudFrontRequestResult } from "aws-lambda";
import { buildPaymentRequirements } from "./build-requirements";
import { verifyPayment, settlePayment } from "./facilitator";
import type { EdgeConfig } from "@x402-aws/shared";

declare const __EDGE_CONFIG__: EdgeConfig;

// Test Default Config Used When Bundle Define Is Absent
const DEFAULT_CONFIG: EdgeConfig = {
  caip2: "eip155:42161",
  usdc: "0xUSDC",
  recipientAddress: "0xRECIPIENT",
  priceUsdc: "10000",
  cdpFacilitatorUrl: "https://facilitator.example",
  cdpApiKeyId: "",
  cdpPrivateKey: "",
};

function getConfig(): EdgeConfig {
  return typeof __EDGE_CONFIG__ !== "undefined" ? __EDGE_CONFIG__ : DEFAULT_CONFIG;
}

function jsonResponse(status: string, body: unknown): CloudFrontRequestResult {
  const description =
    status === "402" ? "Payment Required" : status === "502" ? "Bad Gateway" : "OK";
  return {
    status,
    statusDescription: description,
    headers: {
      "content-type": [{ key: "Content-Type", value: "application/json" }],
    },
    body: JSON.stringify(body),
  };
}

// AgentCore returns the proof under PAYMENT-SIGNATURE; standard x402 clients use X-PAYMENT.
function readPaymentHeader(request: CloudFrontRequestEvent["Records"][0]["cf"]["request"]): string | undefined {
  return (
    request.headers["payment-signature"]?.[0]?.value ??
    request.headers["x-payment"]?.[0]?.value
  );
}

// AgentCore's generate_payment_header emits an envelope the CDP facilitator rejects:
// it nests requirements under `accepted` with `maxAmountRequired` and carries extra
// top-level `resource`/`extension` keys. The facilitator's x402V2PaymentPayload allows
// only {x402Version, accepted, payload} and the requirements need `amount`. Reshape it.
function toFacilitatorPayload(decoded: unknown): unknown {
  if (
    typeof decoded !== "object" ||
    decoded === null ||
    !("accepted" in decoded) ||
    typeof (decoded as Record<string, unknown>).accepted !== "object"
  ) {
    return decoded;
  }
  const env = decoded as Record<string, unknown>;
  const accepted = { ...(env.accepted as Record<string, unknown>) };
  if (accepted.amount === undefined && accepted.maxAmountRequired !== undefined) {
    accepted.amount = accepted.maxAmountRequired;
  }
  return {
    x402Version: env.x402Version,
    accepted,
    payload: env.payload,
  };
}

export async function handler(event: CloudFrontRequestEvent): Promise<CloudFrontRequestResult> {
  const config = getConfig();
  const request = event.Records[0].cf.request;
  const host = request.headers["host"]?.[0]?.value ?? "unknown";
  const resourceUrl = `https://${host}${request.uri}`;
  const requirements = buildPaymentRequirements(config, resourceUrl);

  const paymentHeader = readPaymentHeader(request);

  if (!paymentHeader) {
    return jsonResponse("402", { x402Version: 2, accepts: [requirements], error: null });
  }

  let paymentPayload: unknown;
  try {
    const decoded = Buffer.from(paymentHeader, "base64").toString("utf8");
    paymentPayload = toFacilitatorPayload(JSON.parse(decoded));
  } catch {
    return jsonResponse("402", {
      x402Version: 2,
      accepts: [requirements],
      error: "Malformed payment header",
    });
  }

  let verifyResult;
  try {
    verifyResult = await verifyPayment(config, paymentPayload, requirements);
  } catch (err) {
    return jsonResponse("502", { error: "Facilitator unavailable", detail: String(err) });
  }

  if (!verifyResult.isValid) {
    return jsonResponse("402", {
      x402Version: 2,
      accepts: [requirements],
      error: verifyResult.invalidReason ?? "Verification failed",
    });
  }

  let settleResult;
  try {
    settleResult = await settlePayment(config, paymentPayload, requirements);
  } catch (err) {
    return jsonResponse("502", { error: "Settlement failed", detail: String(err) });
  }

  if (!settleResult.success) {
    return jsonResponse("502", {
      error: "Settlement failed",
      detail: settleResult.errorReason,
    });
  }

  return request;
}
