import type { Metadata } from "next";
import { Geist, Geist_Mono } from "next/font/google";
import Link from "next/link";
import "./globals.css";

const geistSans = Geist({ variable: "--font-geist-sans", subsets: ["latin"] });
const geistMono = Geist_Mono({ variable: "--font-geist-mono", subsets: ["latin"] });

export const metadata: Metadata = {
  title: "OptimizeRoutes",
  description: "CVRP route optimisation dashboard",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en" className={`${geistSans.variable} ${geistMono.variable} h-full antialiased`}>
      <body className="min-h-full flex flex-col bg-gray-950 text-gray-100">
        <nav className="flex items-center gap-6 px-8 py-4 bg-gray-900 border-b border-gray-800 text-sm font-medium">
          <span className="text-blue-400 font-bold text-base">🚚 OptimizeRoutes</span>
          <Link href="/" className="hover:text-blue-400 transition-colors">Otimizar</Link>
          <Link href="/compare" className="hover:text-blue-400 transition-colors">Comparar</Link>
          <Link href="/simulate" className="hover:text-blue-400 transition-colors">Simulação</Link>
        </nav>
        <main className="flex-1">{children}</main>
      </body>
    </html>
  );
}
