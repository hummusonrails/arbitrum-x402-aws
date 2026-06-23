import { Slide, Eyebrow, Title, Panel, LogoWall } from "@/components/ui";

export function AdoptionLogos() {
  const names = [
    "Cloudflare",
    "AWS",
    "Google Cloud",
    "Coinbase",
    "Vercel",
    "American Express",
    "Adyen",
    "Mastercard",
  ];
  const claims = [
    "Cloudflare integrated x402 at the edge.",
    "AWS published a financial-services guide built on x402.",
    "Google adopted x402 as a payment extension for AP2.",
  ];
  return (
    <Slide>
      <Eyebrow>Institutional adoption</Eyebrow>
      <Title>
        Not a science project.{" "}
        <span className="text-blue">The industry is shipping it.</span>
      </Title>
      <div className="mt-10 mb-8">
        <LogoWall names={names} />
      </div>
      <div className="grid grid-cols-3 gap-4">
        {claims.map((c) => (
          <Panel key={c}>
            <div className="text-white text-lg leading-snug">{c}</div>
          </Panel>
        ))}
      </div>
    </Slide>
  );
}
