import { NextResponse } from "next/server";
import { readFileSync } from "node:fs";
import path from "node:path";

export const dynamic = "force-dynamic";

// The CLI (scripts/demo.py) writes <repo-root>/.demo-sync.json on every advance.
// The web dev server runs from apps/web, so the repo root is two levels up.
const SYNC_FILE = path.join(process.cwd(), "..", "..", ".demo-sync.json");

export async function GET() {
  try {
    const raw = readFileSync(SYNC_FILE, "utf8");
    const data = JSON.parse(raw);
    return NextResponse.json({ step: data.step ?? "idle", ts: data.ts ?? 0 });
  } catch {
    return NextResponse.json({ step: "idle", ts: 0 });
  }
}
