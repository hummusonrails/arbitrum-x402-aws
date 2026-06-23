import { Slide, Eyebrow, Title, Lead, Panel } from "@/components/ui";

export function Gap() {
  const humanGated = [
    { t: "Accounts & logins", d: "Sign up, remember a password" },
    { t: "API keys & 2FA", d: "Provision, rotate, approve a prompt" },
    { t: "Manual checkout", d: "Type a card, tap a fingerprint" },
  ];
  return (
    <Slide>
      <Eyebrow>The gap</Eyebrow>
      <Title className="text-6xl">
        Traditional payments assume a{" "}
        <span className="text-blue">human at checkout.</span>
      </Title>
      <Lead>
        Cards, logins, 2FA, fingerprint taps. Every rail is built around a person
        pressing the button. An agent hits a wall designed for humans.
      </Lead>
      <div className="grid grid-cols-3 gap-4 mt-10">
        {humanGated.map((h) => (
          <Panel key={h.t}>
            <div className="text-white text-xl font-semibold">{h.t}</div>
            <div className="text-lightblue/70 mt-2">{h.d}</div>
            <div className="text-blue text-sm font-semibold mt-4 tracking-wide uppercase">
              Built for humans
            </div>
          </Panel>
        ))}
      </div>
    </Slide>
  );
}
