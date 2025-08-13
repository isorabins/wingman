"use client"

import {
  Box,
  Button,
  Container,
  Heading,
  Text,
  VStack,
  Card,
  CardBody,
  Badge,
  Icon,
} from "@chakra-ui/react"
import { Users, ArrowLeft } from "lucide-react"
import Link from "next/link"

export default function FindBuddyPage() {
  return (
    <Box minH="100vh" bg="brand.50">
      {/* Header */}
      <Box borderBottom="1px solid" borderColor="gray.200">
        <Container maxW="6xl" py={6} px={4}>
          <Link href="/">
            <Heading as="h1" size="lg" fontFamily="heading" color="brand.900">
              Wingman
            </Heading>
          </Link>
        </Container>
      </Box>

      {/* Main Content */}
      <Container maxW="4xl" py={12} px={4}>
        <VStack spacing={8} textAlign="center">
          <VStack spacing={6}>
            <Icon as={Users} size={64} color="var(--chakra-colors-brand-400)" />
            <Heading 
              as="h1" 
              size="2xl" 
              fontFamily="heading" 
              color="brand.900"
              lineHeight="tight"
            >
              Ready to Find Your{" "}
              <Text as="span" color="brand.400">Wingman Buddy</Text>
            </Heading>
            <Text 
              fontSize="xl" 
              color="gray.600" 
              maxW="3xl" 
              lineHeight="relaxed"
            >
              Your profile is complete! We'll match you with other users who share your confidence style and are within your travel radius.
            </Text>
          </VStack>

          <Card bg="brand.50" border="1px solid" borderColor="gray.200" w="full" maxW="2xl">
            <CardBody p={8}>
              <VStack spacing={4}>
                <Badge colorScheme="green" variant="solid" px={4} py={2} borderRadius="full">
                  Profile Complete
                </Badge>
                <Heading as="h2" size="md" color="brand.900">
                  What happens next?
                </Heading>
                <VStack spacing={2} align="start" w="full">
                  <Text color="gray.600" fontSize="sm">
                    • We'll match you with compatible wingman buddies
                  </Text>
                  <Text color="gray.600" fontSize="sm">
                    • You'll receive notifications when matches are found
                  </Text>
                  <Text color="gray.600" fontSize="sm">
                    • Start conversations and plan meetups with your matches
                  </Text>
                  <Text color="gray.600" fontSize="sm">
                    • Work together on confidence-building challenges
                  </Text>
                </VStack>
              </VStack>
            </CardBody>
          </Card>

          <VStack spacing={4}>
            <Button 
              size="lg"
              colorScheme="brand"
              bg="brand.900"
              color="brand.50"
              _hover={{ bg: "gray.600" }}
              rounded="full"
              px={8}
              py={6}
              fontSize="base"
            >
              View My Matches
            </Button>
            
            <Button 
              variant="outline"
              borderColor="brand.400"
              color="brand.900"
              _hover={{ bg: "brand.100" }}
              rounded="full"
              px={8}
              py={6}
              fontSize="base"
              as={Link}
              href="/"
            >
              <ArrowLeft size={16} style={{ marginRight: '8px' }} />
              Back to Home
            </Button>
          </VStack>
        </VStack>
      </Container>
    </Box>
  )
}