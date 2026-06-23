import { Slide, Eyebrow, Title, Lead, Stat } from "@/components/ui";

export function WhyArbitrum() {
  return (
    <Slide>
      <Eyebrow>Why Arbitrum · settlement economics</Eyebrow>
      <Title>
        Sub-cent payments need{" "}
        <span className="text-blue">cheap, predictable fees.</span>
      </Title>
      <Lead>
        An agent can&rsquo;t re-price mid-workflow when fees spike. Arbitrum keeps
        micro-payments viable &mdash; and cheap compute lets you verify, not just
        settle.
      </Lead>
      <div className="mt-6 flex justify-center">
        {/* eslint-disable-next-line @next/next/no-img-element */}
        <img
          src="/gas-predictability.png"
          alt="Gas price on Arbitrum One stays flat and predictable through demand spikes"
          className="rounded-xl max-h-[44vh] w-auto"
        />
      </div>
      <div className="flex items-center justify-around mt-6">
        <Stat value="98%" label="gas reduction at peak" sub="ArbOS Dia upgrade" />
        <Stat
          value="92.6%"
          label="cheaper compute on Stylus"
          sub="same algorithm, vs Solidity"
        />
      </div>
    </Slide>
  );
}
