'use client'

import { useEffect } from 'react'
import { 
  Container, 
  VStack, 
  Card, 
  CardBody, 
  Text, 
  Button, 
  Heading,
  Alert,
  AlertIcon,
  AlertTitle,
  AlertDescription
} from '@chakra-ui/react'

interface ErrorPageProps {
  error: Error & { digest?: string }
  reset: () => void
}

export default function SessionError({ error, reset }: ErrorPageProps) {
  useEffect(() => {
    // Log the error to console for debugging
    console.error('Session page error:', error)
  }, [error])

  const getErrorMessage = () => {
    if (error.message.includes('404') || error.message.includes('not found')) {
      return {
        title: 'Session Not Found',
        description: 'The session you\'re looking for doesn\'t exist or you don\'t have permission to view it.'
      }
    }
    
    if (error.message.includes('403') || error.message.includes('unauthorized')) {
      return {
        title: 'Access Denied',
        description: 'You don\'t have permission to view this session. Only matched participants can access session details.'
      }
    }
    
    return {
      title: 'Session Error',
      description: 'Something went wrong while loading the session. Please try again.'
    }
  }

  const errorInfo = getErrorMessage()

  return (
    <Container maxW="4xl" py={8}>
      <VStack spacing={6} align="stretch">
        <Card>
          <CardBody>
            <VStack spacing={4} align="center" textAlign="center">
              <Heading size="lg" color="red.500">
                Oops! Something went wrong
              </Heading>
              
              <Alert status="error" borderRadius="md">
                <AlertIcon />
                <VStack align="start" spacing={1}>
                  <AlertTitle>{errorInfo.title}</AlertTitle>
                  <AlertDescription>
                    {errorInfo.description}
                  </AlertDescription>
                </VStack>
              </Alert>

              <VStack spacing={3}>
                <Button 
                  colorScheme="blue" 
                  onClick={reset}
                  size="lg"
                >
                  Try Again
                </Button>
                
                <Button 
                  variant="ghost"
                  onClick={() => window.history.back()}
                >
                  Go Back
                </Button>
              </VStack>

              {process.env.NODE_ENV === 'development' && (
                <Card bg="gray.50" w="full" mt={4}>
                  <CardBody>
                    <Text fontSize="sm" fontFamily="mono" color="gray.600">
                      <strong>Debug Info:</strong><br />
                      {error.message}
                      {error.digest && <><br />Digest: {error.digest}</>}
                    </Text>
                  </CardBody>
                </Card>
              )}
            </VStack>
          </CardBody>
        </Card>
      </VStack>
    </Container>
  )
}