import { Slide, Eyebrow, Title, Lead, Bars, Stat, Panel } from "@/components/ui";

export function WhyArbitrum() {
  const stylus = [
    {
      label: "Solidity",
      value: 1_027_635,
      display: "1,027,635 gas",
      color: "#9DCCED",
    },
    { label: "Stylus", value: 76_048, display: "76,048 gas" },
  ];
  return (
    <Slide>
      <Eyebrow>Settlement economics</Eyebrow>
      <Title>
        Sub-cent payments need{" "}
        <span className="text-blue">cheap, predictable fees.</span>
      </Title>
      <Lead>
        An agent can&rsquo;t re-price mid-workflow when fees spike. Arbitrum keeps
        micro-payments viable &mdash; and cheap compute lets you verify, not just
        settle.
      </Lead>
      <div className="grid grid-cols-2 gap-8 mt-10 items-center">
        <Panel>
          <Stat
            value="98%"
            label="gas reduction at peak demand"
            sub="ArbOS Dia upgrade vs the old single-target pricing model"
          />
        </Panel>
        <div>
          <div className="text-white font-semibold mb-4">
            Same scoring algorithm,{" "}
            <span className="text-blue">92.6% cheaper</span> on Stylus
          </div>
          <Bars data={stylus} />
          <div className="text-lightblue/60 text-sm mt-3">
            Rust &rarr; WASM. Loop-heavy math executes at near-native speed.
          </div>
        </div>
      </div>
    </Slide>
  );
}
