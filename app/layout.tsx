import type React from "react"
import type { Metadata } from "next"
import Script from "next/script"
import "./globals.css"

export const metadata: Metadata = {
  title: "SL5 Compliance Heatmap - AI Lab Security Monitoring",
  description:
    "Track Security Level 5 (SL5) compliance of major AI labs with this heatmap. Data is derived from open-source public information, updated daily using advanced LLMs to provide the latest insights into frontier model security.",
  generator: "v0.dev",
}

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode
}>) {
  return (
    <html lang="en">
      <head>
        <Script src="https://www.googletagmanager.com/gtag/js?id=G-RQS3THEBNB" strategy="afterInteractive" />
        <Script id="google-analytics" strategy="afterInteractive">
          {`
            window.dataLayer = window.dataLayer || [];
            function gtag(){dataLayer.push(arguments);}
            gtag('js', new Date());
            gtag('config', 'G-RQS3THEBNB');
          `}
        </Script>
      </head>
      <body>{children}</body>
    </html>
  )
}
