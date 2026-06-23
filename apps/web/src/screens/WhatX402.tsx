import { Slide, Eyebrow, Title, Lead, Panel, FlowSteps } from "@/components/ui";

export function WhatX402() {
  const pillars = [
    { t: "Wallet-based identity", d: "Pay as a wallet, not an account" },
    { t: "Dynamic recipients", d: "Per-request payTo routing" },
    { t: "Automatic discovery", d: "Services advertise their price" },
    { t: "Multi-rail support", d: "Many chains and facilitators" },
  ];
  return (
    <Slide>
      <Eyebrow>The solution</Eyebrow>
      <Title>
        x402: <span className="text-blue">internet-native payments</span>
      </Title>
      <Lead>
        An open standard built on the dormant HTTP 402 status code. The server
        answers with payment requirements; the client signs and pays in the very
        next request.
      </Lead>
      <div className="grid grid-cols-4 gap-4 mt-8 mb-8">
        {pillars.map((p) => (
          <Panel key={p.t}>
            <div className="text-blue text-lg font-semibold">{p.t}</div>
            <div className="text-lightblue/70 text-sm mt-2">{p.d}</div>
          </Panel>
        ))}
      </div>
      <FlowSteps />
    </Slide>
  );
}
