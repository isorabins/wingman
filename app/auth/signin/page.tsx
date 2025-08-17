"use client"

import { useState } from 'react'
import { useRouter } from 'next/navigation'
import { useAuth } from '../../../lib/auth-context'
import {
  Box,
  Button,
  Card,
  CardBody,
  CardHeader,
  Container,
  FormControl,
  FormLabel,
  Heading,
  Input,
  Text,
  VStack,
  Alert,
  AlertIcon,
  useToast
} from '@chakra-ui/react'

export default function SignInPage() {
  const [email, setEmail] = useState('')
  const [loading, setLoading] = useState(false)
  const [emailSent, setEmailSent] = useState(false)
  const { signIn } = useAuth()
  const router = useRouter()
  const toast = useToast()

  const handleSignIn = async (e: React.FormEvent) => {
    e.preventDefault()
    
    if (!email.trim()) {
      toast({
        title: "Email required",
        description: "Please enter your email address",
        status: "error",
        duration: 3000,
        isClosable: true,
      })
      return
    }

    setLoading(true)

    try {
      const { error } = await signIn(email)

      if (error) {
        toast({
          title: "Sign in failed",
          description: error.message,
          status: "error",
          duration: 5000,
          isClosable: true,
        })
      } else {
        setEmailSent(true)
        toast({
          title: "Magic link sent!",
          description: "Check your email for a sign-in link",
          status: "success",
          duration: 5000,
          isClosable: true,
        })
      }
    } catch (error: any) {
      toast({
        title: "Something went wrong",
        description: error.message || "Please try again",
        status: "error",
        duration: 5000,
        isClosable: true,
      })
    } finally {
      setLoading(false)
    }
  }

  if (emailSent) {
    return (
      <Container maxW="md" py={16}>
        <Card>
          <CardHeader>
            <Heading size="lg" textAlign="center" color="brand.500">
              Check Your Email
            </Heading>
          </CardHeader>
          <CardBody>
            <VStack spacing={4}>
              <Alert status="success">
                <AlertIcon />
                We've sent you a magic link at {email}
              </Alert>
              <Text textAlign="center" color="gray.600">
                Click the link in your email to sign in and complete your profile setup.
              </Text>
              <Button
                variant="ghost"
                onClick={() => setEmailSent(false)}
                size="sm"
              >
                Try a different email
              </Button>
            </VStack>
          </CardBody>
        </Card>
      </Container>
    )
  }

  return (
    <Container maxW="md" py={16}>
      <Card>
        <CardHeader>
          <VStack spacing={2}>
            <Heading size="lg" textAlign="center" color="brand.500">
              Welcome to Wingman
            </Heading>
            <Text textAlign="center" color="gray.600">
              Sign in to complete your profile and find your wingman buddy
            </Text>
          </VStack>
        </CardHeader>
        <CardBody>
          <form onSubmit={handleSignIn}>
            <VStack spacing={6}>
              <FormControl isRequired>
                <FormLabel>Email Address</FormLabel>
                <Input
                  type="email"
                  placeholder="Enter your email"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  size="lg"
                />
              </FormControl>
              
              <Button
                type="submit"
                colorScheme="brand"
                size="lg"
                width="100%"
                isLoading={loading}
                loadingText="Sending magic link..."
              >
                Send Magic Link
              </Button>

              <Text fontSize="sm" color="gray.500" textAlign="center">
                We'll send you a secure link to sign in without a password
              </Text>
            </VStack>
          </form>
        </CardBody>
      </Card>
    </Container>
  )
}