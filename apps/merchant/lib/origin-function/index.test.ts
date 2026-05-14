import { describe, it, expect } from "vitest";
import { handler } from "./index";

describe("origin handler", () => {
  it("returns gated JSON with resource fields", async () => {
    const result = await handler();
    expect(result.statusCode).toBe(200);
    const body = JSON.parse(result.body);
    expect(body.resource).toBe("premium-market-data");
    expect(typeof body.asOf).toBe("string");
    expect(typeof body.requestId).toBe("string");
    expect(body.payload).toMatchObject({
      btc: expect.any(Number),
      eth: expect.any(Number),
    });
  });
});
