"use client"

import { useEffect, useState } from "react"
import { useAuth } from "../lib/auth-context"
import { Box, Badge, Text, VStack, HStack, Alert, AlertIcon } from "@chakra-ui/react"

export default function TestModeIndicator() {
  const { isTestMode, user } = useAuth()
  const [mounted, setMounted] = useState(false)

  useEffect(() => {
    setMounted(true)
  }, [])

  // Don't render on server or before hydration
  if (!mounted || !isTestMode) return null

  return (
    <Box
      position="fixed"
      top={4}
      right={4}
      zIndex={9999}
      bg="yellow.100"
      border="2px solid"
      borderColor="yellow.400"
      borderRadius="md"
      p={3}
      shadow="md"
    >
      <VStack spacing={2} align="start">
        <HStack>
          <Badge colorScheme="yellow" variant="solid">
            🧪 TEST MODE
          </Badge>
          <Text fontSize="xs" fontWeight="bold" color="yellow.800">
            Development Only
          </Text>
        </HStack>
        
        <VStack spacing={1} align="start" fontSize="xs" color="yellow.700">
          <Text><strong>Mock User ID:</strong> {user?.id}</Text>
          <Text><strong>Mock Email:</strong> {user?.email}</Text>
        </VStack>
        
        <Alert status="warning" size="sm" borderRadius="sm">
          <AlertIcon boxSize={3} />
          <Text fontSize="xs">
            Authentication bypassed for testing
          </Text>
        </Alert>
      </VStack>
    </Box>
  )
}