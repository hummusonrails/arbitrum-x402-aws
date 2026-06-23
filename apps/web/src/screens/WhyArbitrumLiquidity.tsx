import { Slide, Eyebrow, Title, Stat, Panel } from "@/components/ui";

export function WhyArbitrumLiquidity() {
  return (
    <Slide>
      <Eyebrow>Why Arbitrum · the settlement substrate</Eyebrow>
      <Title>
        x402 settles in USDC.{" "}
        <span className="text-blue">
          Arbitrum has the deepest stablecoin liquidity among L2s.
        </span>
      </Title>
      <div className="grid grid-cols-3 gap-8 mt-6 items-center">
        <div className="col-span-2 flex justify-center">
          {/* eslint-disable-next-line @next/next/no-img-element */}
          <img
            src="/stablecoin-liquidity.png"
            alt="Stablecoin supply by Layer-2, with Arbitrum One leading"
            className="rounded-xl max-h-[50vh] w-auto"
          />
        </div>
        <div className="space-y-5">
          <Stat value="$8B+" label="stablecoin TVL" sub="across USDC and USDT" />
          <Stat value="5.1M+" label="stablecoin holders" />
          <Panel>
            <div className="text-white leading-snug">
              The currency x402 settles in is{" "}
              <span className="text-blue">already deepest here.</span>
            </div>
          </Panel>
        </div>
      </div>
      <div className="text-lightblue/60 text-sm mt-6">
        Stablecoin supply by chain. Source: growthepie (as of Dec 2025).
      </div>
    </Slide>
  );
}
