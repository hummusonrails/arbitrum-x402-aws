import React from "react";

/** Full-screen branded slide frame with the geometric hex background + footer. */
export function Slide({
  children,
  footer = true,
}: {
  children: React.ReactNode;
  footer?: boolean;
}) {
  return (
    <div className="hex-bg h-screen w-screen overflow-hidden flex flex-col px-16 py-10">
      <div className="flex-1 flex flex-col justify-center w-full max-w-6xl mx-auto animate-fadeup min-h-0">
        {children}
      </div>
      {footer && (
        <div className="w-full max-w-6xl mx-auto flex items-center justify-between text-lightblue/60 text-sm pt-4">
          <span className="font-mono">x402 on Arbitrum One</span>
          {/* eslint-disable-next-line @next/next/no-img-element */}
          <img
            src="/arbitrum-logomark.svg"
            alt="Arbitrum"
            className="h-6 opacity-80"
          />
        </div>
      )}
    </div>
  );
}

export function Eyebrow({ children }: { children: React.ReactNode }) {
  return (
    <div className="text-blue text-sm font-semibold tracking-[0.25em] uppercase mb-4">
      {children}
    </div>
  );
}

export function Title({
  children,
  className = "",
}: {
  children: React.ReactNode;
  className?: string;
}) {
  return (
    <h1
      className={`text-white font-bold leading-[1.05] tracking-tight text-5xl ${className}`}
    >
      {children}
    </h1>
  );
}

export function Lead({ children }: { children: React.ReactNode }) {
  return (
    <p className="text-lightblue text-2xl mt-6 leading-relaxed max-w-4xl">
      {children}
    </p>
  );
}

export function Panel({
  children,
  className = "",
}: {
  children: React.ReactNode;
  className?: string;
}) {
  return (
    <div
      className={`rounded-xl border border-lightblue/25 bg-navy-alt/60 p-6 ${className}`}
    >
      {children}
    </div>
  );
}

export function Stat({
  value,
  label,
  sub,
}: {
  value: React.ReactNode;
  label: React.ReactNode;
  sub?: React.ReactNode;
}) {
  return (
    <div className="text-center">
      <div className="text-blue text-5xl font-bold">{value}</div>
      <div className="text-white text-lg mt-2">{label}</div>
      {sub && <div className="text-lightblue/70 text-sm mt-1">{sub}</div>}
    </div>
  );
}

export type Bar = {
  label: string;
  value: number;
  display?: string;
  color?: string;
};

/** Linear horizontal bar chart. Label | bar | value. */
export function Bars({ data }: { data: Bar[] }) {
  const max = Math.max(...data.map((d) => d.value), 1);
  return (
    <div className="space-y-3 w-full">
      {data.map((d) => (
        <div key={d.label} className="flex items-center gap-4">
          <div className="w-32 shrink-0 text-right text-lightblue text-base">
            {d.label}
          </div>
          <div className="flex-1 bg-navy-alt/50 rounded h-7">
            <div
              className="h-full rounded transition-all"
              style={{
                width: `${Math.max(0.5, (d.value / max) * 100)}%`,
                background: d.color ?? "#12AAFF",
              }}
            />
          </div>
          <div className="w-36 shrink-0 text-white text-base font-semibold">
            {d.display ?? d.value.toLocaleString()}
          </div>
        </div>
      ))}
    </div>
  );
}

const FLOW = [
  { n: 1, t: "API request", d: "Client requests a resource" },
  { n: 2, t: "402 response", d: "Payment required" },
  { n: 3, t: "Payment details", d: "Amount, recipient, network" },
  { n: 4, t: "Signed payment", d: "Client signs (EIP-3009)" },
  { n: 5, t: "Verify + settle", d: "Facilitator settles on-chain" },
  { n: 6, t: "Access granted", d: "Content delivered" },
];

/** The 6-step x402 flow. Pass `active` (1-6) to highlight the current step. */
export function FlowSteps({ active }: { active?: number }) {
  return (
    <div className="grid grid-cols-6 gap-3 w-full">
      {FLOW.map((s) => {
        const on = active === s.n;
        return (
          <div
            key={s.n}
            className={`rounded-lg border p-4 transition-colors ${
              on
                ? "border-blue bg-blue/15"
                : "border-lightblue/20 bg-navy-alt/40"
            }`}
          >
            <div
              className={`text-2xl font-bold ${on ? "text-blue" : "text-lightblue"}`}
            >
              {s.n}
            </div>
            <div className="text-white text-sm font-semibold mt-2 leading-tight">
              {s.t}
            </div>
            <div className="text-lightblue/70 text-xs mt-1 leading-tight">
              {s.d}
            </div>
          </div>
        );
      })}
    </div>
  );
}

/** Wordmark "logo wall" (company names as branded pills). */
export function LogoWall({ names }: { names: string[] }) {
  return (
    <div className="flex flex-wrap gap-3">
      {names.map((n) => (
        <span
          key={n}
          className="px-5 py-3 rounded-lg border border-lightblue/25 bg-navy-alt/50 text-white text-xl font-semibold"
        >
          {n}
        </span>
      ))}
    </div>
  );
}
