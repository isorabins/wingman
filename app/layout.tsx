import type { Metadata } from "next"
import { Inter } from "next/font/google"
import { Providers } from "./providers"
import { Suspense } from "react"
import { LazyTestModeIndicator } from "../components/LazyComponents"
import PerformanceTracker from "../components/PerformanceTracker"
import { WebVitalsReporter } from "../components/WebVitalsReporter"

const inter = Inter({ 
  subsets: ["latin"],
  display: 'swap', // Optimize font loading
  preload: true
})

export const metadata: Metadata = {
  title: "Wingman - Dating Confidence Assessment",
  description: "Discover your dating confidence type and get personalized challenges to build authentic social skills.",
  keywords: "dating confidence, social skills, personality assessment, wingman",
  openGraph: {
    title: "Wingman - Dating Confidence Assessment",
    description: "Discover your dating confidence type and get personalized challenges to build authentic social skills.",
    type: "website",
  },
  // Performance optimizations
  viewport: {
    width: 'device-width',
    initialScale: 1,
    viewportFit: 'cover'
  }
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="en">
      <head>
        {/* Resource hints for performance */}
        <link rel="dns-prefetch" href="https://fonts.googleapis.com" />
        <link rel="dns-prefetch" href="https://fonts.gstatic.com" />
        <link rel="preconnect" href="https://api.supabase.co" />
        <link rel="preconnect" href="https://supabase.co" />
        
        {/* Critical CSS will be inlined by Next.js */}
        
        {/* Preload important resources */}
        <link rel="preload" href="/api/static/confidence-test/questions.v1.json" as="fetch" crossOrigin="anonymous" />
        
        {/* Performance optimization hints */}
        <meta name="performance-budget" content="js:250kb,css:50kb,images:500kb" />
        <meta name="optimization-target" content="lighthouse-90" />
      </head>
      <body className={inter.className}>
        <Providers>
          <PerformanceTracker />
          <WebVitalsReporter />
          {children}
          <Suspense fallback={null}>
            <LazyTestModeIndicator />
          </Suspense>
        </Providers>
      </body>
    </html>
  )
}