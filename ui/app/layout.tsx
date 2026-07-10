import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "OmniForge — Ask anything. Right agents. Right models.",
  description: "Self-contained multimodal multi-agent multi-LLM answer platform",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
