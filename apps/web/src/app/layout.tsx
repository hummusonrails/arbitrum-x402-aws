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
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
