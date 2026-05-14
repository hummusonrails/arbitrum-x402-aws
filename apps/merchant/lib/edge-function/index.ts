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

export async function handler(event: CloudFrontRequestEvent): Promise<CloudFrontRequestResult> {
  const config = getConfig();
  const request = event.Records[0].cf.request;
  const host = request.headers["host"]?.[0]?.value ?? "unknown";
  const resourceUrl = `https://${host}${request.uri}`;
  const requirements = buildPaymentRequirements(config, resourceUrl);

  const paymentHeader = request.headers["x-payment"]?.[0]?.value;

  if (!paymentHeader) {
    return jsonResponse("402", { x402Version: 2, accepts: [requirements], error: null });
  }

  let paymentPayload: unknown;
  try {
    const decoded = Buffer.from(paymentHeader, "base64").toString("utf8");
    paymentPayload = JSON.parse(decoded);
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
