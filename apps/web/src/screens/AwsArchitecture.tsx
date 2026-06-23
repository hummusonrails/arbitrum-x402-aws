import { Slide, Eyebrow } from "@/components/ui";

export function AwsArchitecture() {
  return (
    <Slide footer={false}>
      <Eyebrow>Reference architecture</Eyebrow>
      <div className="text-white text-3xl font-bold mb-4">
        The full loop, on AWS:{" "}
        <span className="text-blue">agent side + provider side</span>
      </div>
      <div className="bg-white rounded-xl p-4 flex justify-center">
        {/* eslint-disable-next-line @next/next/no-img-element */}
        <img
          src="/aws-architecture.png"
          alt="x402 payment flow between an AI agent and a CloudFront-protected provider on AWS"
          className="max-h-[66vh] w-auto object-contain"
        />
      </div>
      <div className="text-lightblue/70 text-sm mt-4">
        Agent side: Amazon Bedrock AgentCore (Strands + Claude, CDP wallet).
        Provider side: CloudFront + WAF + Lambda@Edge + the x402 facilitator.
        Validated against the aws-samples repos. AWS&rsquo;s reference settles on
        Base; our live demo settles on Arbitrum One.
      </div>
    </Slide>
  );
}
