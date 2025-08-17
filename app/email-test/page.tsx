"use client"

import React, { useState } from "react"
import Link from "next/link"
import { ArrowLeft, Mail, Send, CheckCircle, AlertCircle } from "lucide-react"
import {
  Box,
  Button,
  Card,
  CardBody,
  Container,
  FormControl,
  FormLabel,
  Input,
  Heading,
  VStack,
  HStack,
  Text,
  Textarea,
  useToast,
  Alert,
  AlertIcon,
  AlertTitle,
  AlertDescription,
  Badge,
  Spinner,
} from "@chakra-ui/react"

interface EmailTestResult {
  success: boolean
  message: string
  emailId?: string
  timestamp?: string
}

interface EmailServiceStatus {
  available: boolean
  fallback_mode: boolean
  pending_emails_count: number
  resend_api_key_configured: boolean
  templates_available: number
  configuration?: {
    resend_api_key_set: boolean
    development_mode: boolean
    fallback_mode_reason?: string
  }
  setup_instructions?: {
    for_development: string
    for_production: string
    get_api_key: string
  }
}

export default function EmailTestPage() {
  const [email, setEmail] = useState("isorabins@gmail.com")
  const [subject, setSubject] = useState("Wingman Email Test - " + new Date().toLocaleString())
  const [message, setMessage] = useState(`Hello!

This is a test email from the Wingman platform to verify email functionality is working correctly.

Test Details:
- Timestamp: ${new Date().toISOString()}
- Environment: ${process.env.NODE_ENV || 'development'}
- Purpose: Feature testing and validation

Features being tested:
✅ Backend authentication bypassed for testing
✅ Photo upload with authenticated user context  
✅ Enhanced location services with timeout fixes
✅ Profile completion end-to-end flow
✅ Email notification system (this email!)

If you received this email, the email system is working correctly.

Best regards,
The Wingman Development Team`)
  
  const [isSubmitting, setIsSubmitting] = useState(false)
  const [testResult, setTestResult] = useState<EmailTestResult | null>(null)
  const [emailStatus, setEmailStatus] = useState<EmailServiceStatus | null>(null)
  const [statusLoading, setStatusLoading] = useState(true)
  const toast = useToast()

  // Fetch email service status on component mount
  React.useEffect(() => {
    fetchEmailStatus()
  }, [])

  const fetchEmailStatus = async () => {
    try {
      const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'
      const response = await fetch(`${apiUrl}/email/status`)
      
      if (response.ok) {
        const status = await response.json()
        setEmailStatus(status)
      } else {
        console.error('Failed to fetch email status:', response.status)
      }
    } catch (error) {
      console.error('Error fetching email status:', error)
    } finally {
      setStatusLoading(false)
    }
  }

  const handleSendEmail = async (e: React.FormEvent) => {
    e.preventDefault()
    
    if (!email || !subject || !message) {
      toast({
        title: "Please fill in all fields",
        status: "warning",
        duration: 3000,
      })
      return
    }

    setIsSubmitting(true)
    setTestResult(null)

    try {
      // Test the email endpoint (call backend API directly)
      const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'
      const response = await fetch(`${apiUrl}/api/email/test`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          to: email,
          subject: subject,
          message: message,
          test_mode: true
        }),
      })

      const result = await response.json()

      if (response.ok && result.success) {
        setTestResult({
          success: true,
          message: "Email sent successfully!",
          emailId: result.email_id,
          timestamp: new Date().toISOString()
        })
        
        toast({
          title: "Email sent successfully!",
          description: `Test email sent to ${email}`,
          status: "success",
          duration: 5000,
        })
      } else {
        throw new Error(result.message || `HTTP ${response.status}`)
      }
      
    } catch (error) {
      console.error('Email test error:', error)
      setTestResult({
        success: false,
        message: error instanceof Error ? error.message : "Failed to send email"
      })
      
      toast({
        title: "Email test failed",
        description: error instanceof Error ? error.message : "Please check the logs",
        status: "error",
        duration: 5000,
      })
    } finally {
      setIsSubmitting(false)
    }
  }

  return (
    <Box minH="100vh" bg="brand.50">
      {/* Header */}
      <Box borderBottom="1px solid" borderColor="gray.200">
        <Container maxW="4xl" py={6} px={4}>
          <HStack justify="space-between" align="center">
            <HStack spacing={4}>
              <Mail size={32} color="var(--chakra-colors-brand-400)" />
              <Heading as="h1" size="xl" fontFamily="heading" color="brand.900">
                Email Test
              </Heading>
            </HStack>
            <Button 
              variant="ghost" 
              color="gray.600" 
              _hover={{ color: "brand.900", bg: "gray.200" }}
              as={Link}
              href="/"
            >
              <ArrowLeft size={16} style={{ marginRight: '8px' }} />
              Back to Home
            </Button>
          </HStack>
        </Container>
      </Box>

      {/* Main Content */}
      <Container maxW="4xl" py={8} px={4}>
        <VStack spacing={8} align="stretch">
          
          {/* Info Card */}
          <Card bg="blue.50" border="1px solid" borderColor="blue.200">
            <CardBody p={6}>
              <VStack spacing={3} align="start">
                <HStack>
                  <AlertCircle size={20} color="var(--chakra-colors-blue-500)" />
                  <Text fontWeight="medium" color="blue.900">
                    Email Testing Information
                  </Text>
                </HStack>
                <Text fontSize="sm" color="blue.800">
                  This page tests the email notification system. You can send a test email to any address
                  to verify that the backend email service is working correctly.
                </Text>
                <HStack spacing={2} wrap="wrap">
                  <Badge colorScheme="blue" variant="solid">Development Only</Badge>
                  <Badge colorScheme="green" variant="solid">Test Mode</Badge>
                </HStack>
              </VStack>
            </CardBody>
          </Card>

          {/* Email Service Status */}
          <Card>
            <CardBody p={6}>
              <VStack spacing={4} align="start">
                <HStack>
                  <Mail size={20} color="var(--chakra-colors-brand-500)" />
                  <Text fontWeight="medium" color="brand.900">
                    Email Service Status
                  </Text>
                </HStack>
                
                {statusLoading ? (
                  <HStack>
                    <Spinner size="sm" />
                    <Text fontSize="sm" color="gray.600">Loading status...</Text>
                  </HStack>
                ) : emailStatus ? (
                  <VStack align="start" spacing={3} width="full">
                    <HStack spacing={4} wrap="wrap">
                      <Badge 
                        colorScheme={emailStatus.available ? "green" : "yellow"} 
                        variant="solid"
                      >
                        {emailStatus.available ? "Available" : "Fallback Mode"}
                      </Badge>
                      <Badge 
                        colorScheme={emailStatus.resend_api_key_configured ? "green" : "gray"} 
                        variant="outline"
                      >
                        API Key: {emailStatus.resend_api_key_configured ? "Configured" : "Not Set"}
                      </Badge>
                      <Badge colorScheme="blue" variant="outline">
                        {emailStatus.templates_available} Templates
                      </Badge>
                    </HStack>

                    {emailStatus.setup_instructions && (
                      <Alert status="info" borderRadius="md">
                        <AlertIcon />
                        <VStack align="start" spacing={2}>
                          <AlertTitle fontSize="sm">Configuration Needed</AlertTitle>
                          <AlertDescription fontSize="xs">
                            <VStack align="start" spacing={1}>
                              <Text><strong>Development:</strong> {emailStatus.setup_instructions.for_development}</Text>
                              <Text><strong>Production:</strong> {emailStatus.setup_instructions.for_production}</Text>
                              <Text><strong>Get API Key:</strong> {emailStatus.setup_instructions.get_api_key}</Text>
                            </VStack>
                          </AlertDescription>
                        </VStack>
                      </Alert>
                    )}

                    {emailStatus.pending_emails_count > 0 && (
                      <Alert status="warning" borderRadius="md">
                        <AlertIcon />
                        <AlertDescription fontSize="sm">
                          {emailStatus.pending_emails_count} emails pending in fallback queue
                        </AlertDescription>
                      </Alert>
                    )}
                  </VStack>
                ) : (
                  <Alert status="error" borderRadius="md">
                    <AlertIcon />
                    <AlertDescription fontSize="sm">
                      Could not fetch email service status
                    </AlertDescription>
                  </Alert>
                )}
              </VStack>
            </CardBody>
          </Card>

          {/* Email Form */}
          <Card>
            <CardBody p={8}>
              <form onSubmit={handleSendEmail}>
                <VStack spacing={6} align="stretch">
                  <Heading as="h2" size="md" color="brand.900">
                    Send Test Email
                  </Heading>

                  <FormControl>
                    <FormLabel>To Email Address</FormLabel>
                    <Input
                      type="email"
                      value={email}
                      onChange={(e) => setEmail(e.target.value)}
                      placeholder="recipient@example.com"
                      bg="white"
                    />
                  </FormControl>

                  <FormControl>
                    <FormLabel>Subject</FormLabel>
                    <Input
                      value={subject}
                      onChange={(e) => setSubject(e.target.value)}
                      placeholder="Email subject line"
                      bg="white"
                    />
                  </FormControl>

                  <FormControl>
                    <FormLabel>Message</FormLabel>
                    <Textarea
                      value={message}
                      onChange={(e) => setMessage(e.target.value)}
                      placeholder="Email message content"
                      rows={12}
                      bg="white"
                    />
                  </FormControl>

                  <Button
                    type="submit"
                    colorScheme="brand"
                    bg="brand.900"
                    color="brand.50"
                    _hover={{ bg: "gray.600" }}
                    size="lg"
                    isLoading={isSubmitting}
                    loadingText="Sending Email..."
                    disabled={!email || !subject || !message}
                  >
                    {isSubmitting ? (
                      <HStack>
                        <Spinner size="sm" />
                        <Text>Sending Email...</Text>
                      </HStack>
                    ) : (
                      <HStack>
                        <Send size={16} />
                        <Text>Send Test Email</Text>
                      </HStack>
                    )}
                  </Button>
                </VStack>
              </form>
            </CardBody>
          </Card>

          {/* Test Result */}
          {testResult && (
            <Card>
              <CardBody p={6}>
                <Alert
                  status={testResult.success ? "success" : "error"}
                  borderRadius="md"
                >
                  <AlertIcon />
                  <VStack align="start" spacing={2}>
                    <AlertTitle fontSize="md">
                      {testResult.success ? "Email Sent Successfully!" : "Email Test Failed"}
                    </AlertTitle>
                    <AlertDescription fontSize="sm">
                      {testResult.message}
                    </AlertDescription>
                    {testResult.success && testResult.emailId && (
                      <Text fontSize="xs" color="gray.600">
                        Email ID: {testResult.emailId} • Sent: {testResult.timestamp}
                      </Text>
                    )}
                  </VStack>
                </Alert>
              </CardBody>
            </Card>
          )}

          {/* Feature Status */}
          <Card bg="green.50" border="1px solid" borderColor="green.200">
            <CardBody p={6}>
              <VStack spacing={4} align="start">
                <HStack>
                  <CheckCircle size={20} color="var(--chakra-colors-green-500)" />
                  <Text fontWeight="medium" color="green.900">
                    Available Test Features
                  </Text>
                </HStack>
                
                <VStack align="start" spacing={2} fontSize="sm" color="green.800">
                  <Text>✅ <strong>Test Mode Authentication:</strong> Bypass auth with ?test=true</Text>
                  <Text>✅ <strong>Photo Upload Testing:</strong> Test with mock user ID (test-user-12345)</Text>
                  <Text>✅ <strong>Location Services:</strong> Enhanced timeout and fallback testing</Text>
                  <Text>✅ <strong>Profile Setup:</strong> End-to-end form testing with real validation</Text>
                  <Text>✅ <strong>Email Notifications:</strong> Send test emails to verify functionality</Text>
                </VStack>

                <Text fontSize="sm" color="green.700" fontStyle="italic">
                  All systems operational and ready for comprehensive testing!
                </Text>
              </VStack>
            </CardBody>
          </Card>
        </VStack>
      </Container>
    </Box>
  )
}