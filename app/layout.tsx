import type { Metadata } from 'next'
import './globals.css'

export const metadata: Metadata = {
  title: 'SL5 Compliance Heatmap - AI Lab Security Monitoring',
  description: 'Track Security Level 5 (SL5) compliance of major AI labs with this heatmap. Data is derived from open-source public information, updated daily using advanced LLMs to provide the latest insights into frontier model security.',
  generator: 'v0.dev',
}

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode
}>) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  )
}
