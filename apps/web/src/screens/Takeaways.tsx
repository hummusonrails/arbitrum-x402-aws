import { Slide, Eyebrow, Title, Panel } from "@/components/ui";

export function Takeaways() {
  const cols = [
    "No accounts. No API keys. No subscriptions. One status code, one header.",
    "Verifiable intent, cryptographic audit trails, payment-agnostic settlement.",
    "Fees low enough for micropayments. The infrastructure for agent economics.",
  ];
  const useCases = [
    "Pay-per-use APIs",
    "Agent-to-agent marketplaces",
    "Autonomous commerce",
    "M2M / IoT billing",
  ];
  return (
    <Slide>
      <Eyebrow>Takeaways</Eyebrow>
      <Title>
        Build <span className="text-blue">open, composable</span> AI agent
        economies.
      </Title>
      <div className="grid grid-cols-3 gap-5 mt-10">
        {cols.map((c) => (
          <Panel key={c}>
            <div className="text-white text-lg leading-snug">{c}</div>
          </Panel>
        ))}
      </div>
      <div className="flex flex-wrap gap-3 mt-8">
        {useCases.map((u) => (
          <span
            key={u}
            className="px-4 py-2 rounded-lg border border-blue/40 text-blue font-semibold"
          >
            {u}
          </span>
        ))}
      </div>
      <div className="text-lightblue mt-8 font-mono">
        github.com/hummusonrails/arbitrum-x402-aws
      </div>
    </Slide>
  );
}
