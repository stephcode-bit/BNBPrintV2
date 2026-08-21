import type { Metadata, Viewport } from "next";
import { Chakra_Petch, JetBrains_Mono, Manrope } from "next/font/google";
import { Toaster } from "react-hot-toast";
import "./globals.css";
import { QueryProvider } from "@/lib/query-provider";
import { WsProvider } from "@/lib/ws";
import Header from "@/components/Header";
import InstallPrompt from "@/components/InstallPrompt";

const chakra = Chakra_Petch({
  subsets: ["latin"],
  weight: ["500", "600", "700"],
  variable: "--font-display",
  display: "swap",
});

const manrope = Manrope({
  subsets: ["latin"],
  variable: "--font-body",
  display: "swap",
});

const mono = JetBrains_Mono({
  subsets: ["latin"],
  weight: ["400", "500", "600"],
  variable: "--font-mono-face",
  display: "swap",
});

export const metadata: Metadata = {
  title: "BNBPRINT — BNB Chain Runner Radar",
  description:
    "Real-time BNB Chain token discovery for bonding-curve launches (four.meme, GraFun & more). Spot runners early, dodge honeypots and rugs, before they finish bonding.",
  applicationName: "BNBPRINT",
  manifest: "/manifest.json",
  icons: {
    icon: [
      { url: "/favicon.ico" },
      { url: "/icons/icon-192.png", sizes: "192x192", type: "image/png" },
      { url: "/icons/icon-512.png", sizes: "512x512", type: "image/png" },
    ],
    apple: [{ url: "/icons/icon-192.png", sizes: "192x192", type: "image/png" }],
  },
  appleWebApp: {
    capable: true,
    statusBarStyle: "black-translucent",
    title: "BNBPRINT",
  },
  openGraph: {
    title: "BNBPRINT — BNB Chain Runner Radar",
    description: "Catch bonding-curve runners on BNB Chain before they migrate — with built-in rug/honeypot checks.",
    type: "website",
  },
};

export const viewport: Viewport = {
  themeColor: "#0B0E11",
  width: "device-width",
  initialScale: 1,
  maximumScale: 1,
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en" className={`${chakra.variable} ${manrope.variable} ${mono.variable}`}>
      <body className="font-sans antialiased">
        <QueryProvider>
          <WsProvider>
            <div className="min-h-dvh flex flex-col">
              <Header />
              <main className="flex-1 w-full max-w-[1400px] mx-auto px-4 sm:px-6 lg:px-8 py-6">
                {children}
              </main>
              <footer className="border-t border-bnb-border/60 py-6 text-center text-xs text-bnb-muted">
                <p>
                  BNBPRINT is a research tool, not financial advice. Bonding-curve tokens are extremely
                  high risk — always verify contracts yourself before trading.
                </p>
              </footer>
            </div>
            <InstallPrompt />
            <Toaster position="top-right" toastOptions={{ duration: 5000 }} />
          </WsProvider>
        </QueryProvider>
      </body>
    </html>
  );
}
