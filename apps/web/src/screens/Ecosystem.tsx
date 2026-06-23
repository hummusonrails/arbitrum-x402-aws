import { Slide, Eyebrow, Title, Panel } from "@/components/ui";

export function Ecosystem() {
  const standards = [
    {
      name: "x402",
      origin: "Coinbase → Linux Foundation project",
      footprint: "Base, Solana, Polygon, + Arbitrum",
      note: "Native to Ethereum L2s. Neutral board forming now.",
      accent: true,
    },
    {
      name: "MPP",
      origin: "Tempo × Stripe",
      footprint: "Card, Lightning, Stripe, Tempo chain, Solana, Stellar",
      note: "No Ethereum L2s as first-class methods.",
      accent: false,
    },
    {
      name: "APP",
      origin: "OKX-led",
      footprint: "Settles on OKX X Layer",
      note: "Wire-compatible with both x402 and MPP.",
      accent: false,
    },
  ];
  return (
    <Slide>
      <Eyebrow>The landscape</Eyebrow>
      <Title>
        Three emerging{" "}
        <span className="text-blue">agent-payment standards</span>
      </Title>
      <div className="grid grid-cols-3 gap-5 mt-10">
        {standards.map((s) => (
          <Panel
            key={s.name}
            className={s.accent ? "border-blue/60 bg-blue/10" : ""}
          >
            <div
              className={`text-3xl font-bold ${s.accent ? "text-blue" : "text-white"}`}
            >
              {s.name}
            </div>
            <div className="text-white mt-4 font-semibold">{s.origin}</div>
            <div className="text-lightblue mt-3 leading-snug">
              {s.footprint}
            </div>
            <div className="text-lightblue/70 text-sm mt-4 leading-snug">
              {s.note}
            </div>
          </Panel>
        ))}
      </div>
    </Slide>
  );
}
