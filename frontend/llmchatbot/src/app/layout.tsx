import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "EcoBot | Waste Management Assistant",
  description: "AI-powered waste disposal and recycling guidance chatbot.",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
