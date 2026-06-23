import { QRCodeSVG } from "qrcode.react";
import { Slide, Eyebrow, Title, Panel } from "@/components/ui";

const REPO_QR =
  "https://github.com/hummusonrails/arbitrum-x402-aws?utm_source=linkedin-webinar&utm_medium=event&utm_campaign=arbitrum-x-aws-collaboration";

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
      <div className="grid grid-cols-3 gap-5 mt-8">
        {cols.map((c) => (
          <Panel key={c}>
            <div className="text-white text-lg leading-snug">{c}</div>
          </Panel>
        ))}
      </div>
      <div className="flex flex-wrap gap-3 mt-6">
        {useCases.map((u) => (
          <span
            key={u}
            className="px-4 py-2 rounded-lg border border-blue/40 text-blue font-semibold"
          >
            {u}
          </span>
        ))}
      </div>
      <div className="mt-6 font-mono text-lightblue text-lg">
        github.com/hummusonrails/arbitrum-x402-aws
      </div>
      <div className="flex-1 flex flex-col items-center justify-center mt-4 gap-3">
        <div className="bg-white p-3 rounded-xl">
          <QRCodeSVG
            value={REPO_QR}
            size={200}
            bgColor="#FFFFFF"
            fgColor="#213147"
            level="M"
          />
        </div>
        <div className="text-lightblue/70 text-sm">Scan to explore the repo</div>
      </div>
    </Slide>
  );
}
