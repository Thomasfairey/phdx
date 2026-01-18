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
      <body className={`${inter.className} antialiased bg-[#050505] text-[#E0E0E0]`}>
        {children}
      </body>
    </html>
  )
}
