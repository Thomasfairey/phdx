<<<<<<< HEAD
import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "PHDx - Command Center",
  description: "PhD Thesis Command Center",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <head>
        <link
          href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=Merriweather:ital,wght@0,300;0,400;0,700;1,400&display=swap"
          rel="stylesheet"
        />
      </head>
      <body className="antialiased bg-[#050505] text-[#E0E0E0]">
        {children}
      </body>
    </html>
  );
=======
import type { Metadata } from 'next'
import { Inter } from 'next/font/google'
import './globals.css'

const inter = Inter({ subsets: ['latin'] })

export const metadata: Metadata = {
  title: 'PHDx - PhD Thesis Command Center',
  description: 'Your intelligent companion for PhD thesis writing and research management',
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="en">
      <body className={inter.className}>{children}</body>
    </html>
  )
>>>>>>> 6b91e3229396369fe9d66a545436309a7815bc21
}
