import { Slide, Eyebrow, Title, Lead, FlowSteps, Panel } from "@/components/ui";

export function LiveProvider() {
  const terms = [
    ["scheme", "exact"],
    ["network", "eip155:42161 (Arbitrum One)"],
    ["price", "10000 base units = $0.01 USDC"],
    ["asset", "native USDC on Arbitrum One"],
  ];
  return (
    <Slide>
      <Eyebrow>Live demo &middot; provider side</Eyebrow>
      <Title>
        The server answers <span className="text-blue">402.</span>
      </Title>
      <Lead>
        Watch the terminal. A gated CloudFront + Lambda@Edge endpoint returns HTTP
        402 with machine-readable payment terms &mdash; before the origin is ever
        called.
      </Lead>
      <div className="my-8">
        <FlowSteps active={2} />
      </div>
      <Panel>
        <div className="text-lightblue/70 text-sm uppercase tracking-wide mb-3">
          The 402 advertises the deal
        </div>
        <div className="grid grid-cols-2 gap-x-10 gap-y-2 font-mono text-base">
          {terms.map(([k, v]) => (
            <div key={k}>
              <span className="text-blue">{k}</span>
              <span className="text-white"> = {v}</span>
            </div>
          ))}
        </div>
      </Panel>
    </Slide>
  );
}
