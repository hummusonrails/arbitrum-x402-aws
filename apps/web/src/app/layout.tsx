import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "x402 on Arbitrum — live walkthrough",
  description: "Companion display for the x402 on Arbitrum live demo.",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    // suppressHydrationWarning: browser extensions inject attributes (e.g.
    // data-peer-injected) onto html/body before React hydrates.
    <html lang="en" suppressHydrationWarning>
      <body suppressHydrationWarning>{children}</body>
    </html>
  );
}
