"use client";

import { useSync } from "@/lib/useSync";
import { SCREENS } from "@/screens";

export default function Page() {
  const step = useSync();
  const Screen = SCREENS[step] ?? SCREENS.idle;
  return <Screen />;
}
