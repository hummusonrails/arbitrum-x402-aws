import { Slide, Eyebrow, Title, Bars, Stat, Panel } from "@/components/ui";

export function AdoptionStats() {
  const byChain = [
    { label: "Base", value: 72_000_000, display: "72M" },
    { label: "Solana", value: 47_000_000, display: "47M" },
    { label: "Polygon", value: 10_000_000, display: "10M" },
    { label: "BNB", value: 740_000, display: "740K" },
    { label: "Avalanche", value: 4_800, display: "4.8K" },
    { label: "Arbitrum", value: 522, display: "522", color: "#9DCCED" },
  ];
  return (
    <Slide>
      <Eyebrow>x402 adoption today</Eyebrow>
      <Title>
        Real volume &mdash; and{" "}
        <span className="text-blue">wide open on Arbitrum.</span>
      </Title>
      <div className="grid grid-cols-3 gap-8 mt-8 items-center">
        <div className="col-span-2">
          <Bars data={byChain} />
        </div>
        <div className="space-y-6">
          <Stat value="98.8%" label="of EVM dollar volume is USDC on Base" />
          <Panel className="text-center">
            <div className="text-white text-lg">
              Arbitrum: <span className="text-blue font-bold">522</span> txns
            </div>
            <div className="text-lightblue/70 text-sm mt-1">
              The greenfield is the point.
            </div>
          </Panel>
        </div>
      </div>
      <div className="text-lightblue/60 text-sm mt-8">
        Transactions by chain since Oct 2025; activity peaked Oct&ndash;Nov 2025.
        Source: Dune (hashed_official/x402), figures as of Apr 2026.
      </div>
    </Slide>
  );
}
