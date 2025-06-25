import type { Metadata } from "next";
import { Inter, Roboto } from "next/font/google";
import "./globals.css";

const roboto = Roboto({
  weight: ['300', '400', '500', '700'],
  subsets: ['latin'],
  display: 'swap',
  variable: '--font-roboto',
});

export const metadata: Metadata = {
  title: "KI-Wissenssystem",
  description: "Intelligente Wissensverwaltung mit KI-Unterstützung",
  keywords: ["KI", "Wissenssystem", "Chat", "Graph", "Dokumenten-Upload"],
  authors: [{ name: "KI-Wissenssystem Team" }],
  creator: "KI-Wissenssystem",
  publisher: "KI-Wissenssystem",
  robots: "index, follow",
  viewport: {
    width: 'device-width',
    initialScale: 1,
    maximumScale: 1,
  },
  themeColor: [
    { media: "(prefers-color-scheme: light)", color: "#6750A4" },
    { media: "(prefers-color-scheme: dark)", color: "#D0BCFF" }
  ],
  manifest: '/manifest.json',
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="de" className={roboto.variable} suppressHydrationWarning>
      <head>
        {/* Material Symbols Icons */}
        <link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Material+Symbols+Outlined:opsz,wght,FILL,GRAD@20..48,100..700,0..1,-50..200" />
        
        {/* Material Web Components - Stabiles CDN */}
        <script type="module" src="https://unpkg.com/@material/web@2.0.0/all.js"></script>
        
        {/* Preconnect für Performance */}
        <link rel="preconnect" href="https://fonts.googleapis.com" />
        <link rel="preconnect" href="https://fonts.gstatic.com" crossOrigin="anonymous" />
        
        {/* PWA Meta Tags */}
        <meta name="application-name" content="KI-Wissenssystem" />
        <meta name="apple-mobile-web-app-capable" content="yes" />
        <meta name="apple-mobile-web-app-status-bar-style" content="default" />
      </head>
      <body className="app-container" suppressHydrationWarning>
        <main className="app-container">
          {children}
        </main>
      </body>
    </html>
  );
}
