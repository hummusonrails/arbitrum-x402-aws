import { describe, it, expect, vi, beforeEach } from "vitest";
import type { CloudFrontRequestEvent } from "aws-lambda";

vi.mock("./facilitator", () => ({
  verifyPayment: vi.fn(),
  settlePayment: vi.fn(),
}));

import { handler } from "./index";
import { verifyPayment, settlePayment } from "./facilitator";

function buildEvent(headers: Record<string, string> = {}): CloudFrontRequestEvent {
  const lowerHeaders: Record<string, { key: string; value: string }[]> = {};
  for (const [k, v] of Object.entries(headers)) {
    lowerHeaders[k.toLowerCase()] = [{ key: k, value: v }];
  }
  if (!lowerHeaders["host"]) {
    lowerHeaders["host"] = [{ key: "Host", value: "x.cloudfront.net" }];
  }
  return {
    Records: [
      {
        cf: {
          config: {
            distributionDomainName: "x.cloudfront.net",
            distributionId: "EXAMPLE",
            eventType: "viewer-request",
            requestId: "rid",
          },
          request: {
            clientIp: "1.2.3.4",
            method: "GET",
            uri: "/report",
            querystring: "",
            headers: lowerHeaders,
            origin: {
              custom: {
                domainName: "origin.example",
                port: 443,
                protocol: "https",
                path: "",
                sslProtocols: ["TLSv1.2"],
                readTimeout: 30,
                keepaliveTimeout: 5,
                customHeaders: {},
              },
            },
          },
        },
      } as any,
    ],
  };
}

beforeEach(() => {
  vi.resetAllMocks();
});

describe("edge handler", () => {
  it("returns 402 with payment terms when no X-PAYMENT header", async () => {
    const result = (await handler(buildEvent())) as any;
    expect(result.status).toBe("402");
    const body = JSON.parse(result.body);
    expect(body.x402Version).toBe(2);
    expect(body.accepts[0].network).toBeDefined();
    expect(body.accepts[0].asset).toBeDefined();
    expect(body.accepts[0].resource).toBe("https://x.cloudfront.net/report");
  });

  it("passes through to origin when verify and settle succeed", async () => {
    vi.mocked(verifyPayment).mockResolvedValue({ isValid: true });
    vi.mocked(settlePayment).mockResolvedValue({ success: true, txHash: "0xabc" });

    const payload = Buffer.from(JSON.stringify({ scheme: "exact", payload: { mock: true } })).toString("base64");
    const event = buildEvent({ "x-payment": payload });
    const result = (await handler(event)) as any;

    expect(result.method).toBe("GET");
    expect(result.uri).toBe("/report");
    expect(verifyPayment).toHaveBeenCalled();
    expect(settlePayment).toHaveBeenCalled();
  });

  it("returns 402 with reason when verify fails", async () => {
    vi.mocked(verifyPayment).mockResolvedValue({ isValid: false, invalidReason: "nonce-used" });

    const payload = Buffer.from(JSON.stringify({ scheme: "exact" })).toString("base64");
    const result = (await handler(buildEvent({ "x-payment": payload }))) as any;

    expect(result.status).toBe("402");
    expect(JSON.parse(result.body).error).toContain("nonce-used");
    expect(settlePayment).not.toHaveBeenCalled();
  });

  it("returns 502 when settlement fails", async () => {
    vi.mocked(verifyPayment).mockResolvedValue({ isValid: true });
    vi.mocked(settlePayment).mockResolvedValue({ success: false, errorReason: "rpc-error" });

    const payload = Buffer.from(JSON.stringify({ scheme: "exact" })).toString("base64");
    const result = (await handler(buildEvent({ "x-payment": payload }))) as any;
    expect(result.status).toBe("502");
  });

  it("returns 402 on malformed X-PAYMENT header", async () => {
    const result = (await handler(buildEvent({ "x-payment": "not-base64-json" }))) as any;
    expect(result.status).toBe("402");
    expect(JSON.parse(result.body).error).toContain("Malformed");
    expect(verifyPayment).not.toHaveBeenCalled();
  });

  it("returns 502 when facilitator network call throws", async () => {
    vi.mocked(verifyPayment).mockRejectedValue(new Error("timeout"));

    const payload = Buffer.from(JSON.stringify({ scheme: "exact" })).toString("base64");
    const result = (await handler(buildEvent({ "x-payment": payload }))) as any;
    expect(result.status).toBe("502");
  });
});
