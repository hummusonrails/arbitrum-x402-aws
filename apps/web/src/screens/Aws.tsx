import { Slide, Eyebrow, Title, Lead, Panel, Stat } from "@/components/ui";

export function Aws() {
  const features = [
    {
      t: "Native x402 execution",
      d: "The agent hits a 402; AgentCore evaluates the terms, authorizes the USDC micropayment, and resubmits — no extra agent code.",
    },
    {
      t: "Managed wallets",
      d: "Scoped wallets auto-provisioned; you never touch private keys. Providers: Coinbase CDP and Stripe (Privy).",
    },
    {
      t: "Policy-based spending",
      d: "Per-agent and per-session budgets with expiry — the same guardrails finance teams put on human procurement.",
    },
    {
      t: "Discovery + full audit trail",
      d: "x402 Bazaar MCP exposes 10,000+ pay-per-use endpoints via the Gateway; every payment is logged with the agent's reasoning (CloudWatch + X-Ray).",
    },
  ];
  return (
    <Slide>
      <Eyebrow>AWS · Bedrock AgentCore Payments (Preview)</Eyebrow>
      <Title>
        AWS made agent payments a{" "}
        <span className="text-blue">managed service.</span>
      </Title>
      <Lead>
        This demo runs on it. AgentCore Payments brings native, managed x402
        micropayments to agents — wallets, spending policy, and a full audit trail
        — turning months of payment plumbing into a few lines of code.
      </Lead>
      <div className="grid grid-cols-2 gap-4 mt-8">
        {features.map((f) => (
          <Panel key={f.t}>
            <div className="text-blue text-lg font-semibold">{f.t}</div>
            <div className="text-lightblue/80 text-sm mt-2 leading-snug">
              {f.d}
            </div>
          </Panel>
        ))}
      </div>
      <div className="flex items-center justify-around mt-8">
        <Stat value="$3–5T" label="agentic commerce by 2030" sub="McKinsey" />
        <Stat
          value="~$0.0001"
          label="per transaction"
          sub="sub-2-second settlement"
        />
        <Stat value="months → days" label="payment integration effort" />
      </div>
    </Slide>
  );
}
