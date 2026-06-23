import { Slide, Eyebrow, Title, Lead } from "@/components/ui";

export function Hook() {
  return (
    <Slide>
      <Eyebrow>The agent economy</Eyebrow>
      <Title className="text-7xl">
        Agents can reason and act.
        <br />
        They <span className="text-blue">cannot pay.</span>
      </Title>
      <Lead>
        Every other part of the agent stack has matured. Payment is the missing
        primitive. That is the gap x402 closes.
      </Lead>
    </Slide>
  );
}
