import { randomUUID } from "node:crypto";

export async function handler() {
  const body = {
    resource: "premium-market-data",
    asOf: new Date().toISOString(),
    requestId: randomUUID(),
    payload: {
      btc: 71234.56,
      eth: 4567.89,
    },
  };
  return {
    statusCode: 200,
    headers: { "content-type": "application/json" },
    body: JSON.stringify(body),
  };
}
