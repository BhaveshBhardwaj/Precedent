import type { Metadata } from "next";
import { Inter } from "next/font/google";
import "./globals.css";
import Navbar from "./components/Navbar";

const inter = Inter({
  subsets: ["latin"],
  variable: "--font-inter",
});

export const metadata: Metadata = {
  title: "Precedent — Institutional Memory for On-Call",
  description:
    "An institutional memory graph for on-call engineers. Surfacing historical root causes before you reinvent the wheel.",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" className="dark">
      <body className={`${inter.variable} font-sans antialiased bg-zinc-950 text-zinc-100 min-h-screen`}>
        <Navbar />
        <main className="max-w-4xl mx-auto px-4 pt-20 pb-12">
          {children}
        </main>
      </body>
    </html>
  );
}
