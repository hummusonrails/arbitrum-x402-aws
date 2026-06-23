import { Slide, Eyebrow, Title, Panel, LogoWall } from "@/components/ui";

export function WhyArbitrumInstitutions() {
  const rwas = [
    "Franklin Templeton",
    "BlackRock",
    "WisdomTree",
    "Invesco",
    "Spiko",
    "Robinhood",
  ];
  const stables = ["Tether", "Circle", "PayPal", "Paxos", "Bitso", "M0"];
  return (
    <Slide>
      <Eyebrow>Why Arbitrum · the ecosystem is already here</Eyebrow>
      <Title>
        High-quality assets and the{" "}
        <span className="text-blue">TradFi &times; DeFi convergence.</span>
      </Title>
      <div className="mt-8 space-y-5">
        <div>
          <div className="text-blue font-semibold mb-2">
            RWAs &middot; $893M tokenized, ~7&times; YTD
          </div>
          <LogoWall names={rwas} />
        </div>
        <div>
          <div className="text-blue font-semibold mb-2">Stablecoins</div>
          <LogoWall names={stables} />
        </div>
      </div>
      <div className="grid grid-cols-2 gap-6 mt-8">
        <Panel>
          <div className="text-white font-semibold mb-1">TradFi → on-chain</div>
          <div className="text-lightblue/80 text-sm leading-snug">
            BlackRock, Robinhood, Franklin Templeton, Tether, and Circle bring
            siloed, permissioned assets on-chain.
          </div>
        </Panel>
        <Panel>
          <div className="text-white font-semibold mb-1">
            DeFi → institutional
          </div>
          <div className="text-lightblue/80 text-sm leading-snug">
            Hyperliquid, GMX, and leading Arbitrum DeFi build
            institutional-grade, transparent-yield infrastructure.
          </div>
        </Panel>
      </div>
      <div className="text-lightblue/70 text-sm mt-6">
        Arbitrum hosts the deepest liquidity across both RWAs and DeFi &mdash;
        the natural convergence point, and the place to settle agent payments.
      </div>
    </Slide>
  );
}
