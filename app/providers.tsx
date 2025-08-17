"use client"

import { ChakraProvider } from "@chakra-ui/react"
import { AuthProvider } from "../lib/auth-context"
import { theme } from "./theme"

export function Providers({ children }: { children: React.ReactNode }) {
  return (
    <ChakraProvider theme={theme}>
      <AuthProvider>
        {children}
      </AuthProvider>
    </ChakraProvider>
  )
}