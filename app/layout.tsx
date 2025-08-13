import type { Metadata } from "next"
import { Inter } from "next/font/google"
import { Providers } from "./providers"

const inter = Inter({ subsets: ["latin"] })

export const metadata: Metadata = {
  title: "Wingman - Dating Confidence Assessment",
  description: "Discover your dating confidence type and get personalized challenges to build authentic social skills.",
  keywords: "dating confidence, social skills, personality assessment, wingman",
  openGraph: {
    title: "Wingman - Dating Confidence Assessment",
    description: "Discover your dating confidence type and get personalized challenges to build authentic social skills.",
    type: "website",
  },
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="en">
      <body className={inter.className}>
        <Providers>
          {children}
        </Providers>
      </body>
    </html>
  )
}