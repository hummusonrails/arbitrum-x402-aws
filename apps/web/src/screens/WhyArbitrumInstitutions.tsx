import { Slide, Eyebrow, Title, Panel } from "@/components/ui";

export function WhyArbitrumInstitutions() {
  return (
    <Slide>
      <Eyebrow>Why Arbitrum · the ecosystem is already here</Eyebrow>
      <Title>
        High-quality assets and the{" "}
        <span className="text-blue">TradFi &times; DeFi convergence.</span>
      </Title>
      <div className="mt-5 flex justify-center">
        {/* eslint-disable-next-line @next/next/no-img-element */}
        <img
          src="/onchain-assets.png"
          alt="RWA and stablecoin issuers on Arbitrum: Franklin Templeton, BlackRock, WisdomTree, Invesco, Spiko, Robinhood, Tether, PayPal, Bitso, Circle, Paxos, M0"
          className="rounded-xl max-h-[42vh] w-auto"
        />
      </div>
      <div className="grid grid-cols-2 gap-6 mt-6">
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
      <div className="text-lightblue/70 text-sm mt-5">
        $893M tokenized RWAs (~7&times; YTD) and the deepest liquidity across both
        RWAs and DeFi &mdash; the natural convergence point, and the place to
        settle agent payments.
      </div>
    </Slide>
  );
}
