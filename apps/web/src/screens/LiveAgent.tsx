import { Slide, Eyebrow, Title, Lead, FlowSteps, Panel } from "@/components/ui";

export function LiveAgent() {
  const points = [
    "No ETH for gas",
    "The signature is the payment",
    "Settled in seconds, for a fraction of a cent",
  ];
  return (
    <Slide>
      <Eyebrow>Live demo &middot; agent side</Eyebrow>
      <Title>
        The agent pays <span className="text-blue">by signature.</span>
      </Title>
      <Lead>
        The agent signs an EIP-3009 authorization (gasless), the facilitator
        verifies and settles it on Arbitrum One, and the gated data comes back
        &mdash; all in one retry.
      </Lead>
      <div className="my-8">
        <FlowSteps active={5} />
      </div>
      <div className="grid grid-cols-3 gap-4">
        {points.map((p) => (
          <Panel key={p} className="text-center">
            <div className="text-white text-lg">{p}</div>
          </Panel>
        ))}
      </div>
    </Slide>
  );
}
