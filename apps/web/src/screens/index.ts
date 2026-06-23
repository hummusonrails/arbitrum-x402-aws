import type { ComponentType } from "react";
import { Idle } from "./Idle";
import { Hook } from "./Hook";
import { Gap } from "./Gap";
import { WhatX402 } from "./WhatX402";
import { AdoptionLogos } from "./AdoptionLogos";
import { AdoptionStats } from "./AdoptionStats";
import { Ecosystem } from "./Ecosystem";
import { WhyArbitrum } from "./WhyArbitrum";
import { LiveProvider } from "./LiveProvider";
import { LiveAgent } from "./LiveAgent";
import { Takeaways } from "./Takeaways";

export const SCREENS: Record<string, ComponentType> = {
  idle: Idle,
  hook: Hook,
  gap: Gap,
  "what-x402": WhatX402,
  "adoption-logos": AdoptionLogos,
  "adoption-stats": AdoptionStats,
  ecosystem: Ecosystem,
  "why-arbitrum": WhyArbitrum,
  "live-provider": LiveProvider,
  "live-agent": LiveAgent,
  takeaways: Takeaways,
};
