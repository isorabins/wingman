'use client'

import { useState } from 'react'
import { useRouter } from 'next/navigation'
import {
  Card,
  CardBody,
  CardHeader,
  VStack,
  HStack,
  Button,
  Text,
  Textarea,
  FormControl,
  FormLabel,
  useToast,
  Badge,
  Box,
  Heading,
  Flex,
  Spacer,
  Icon,
  Divider
} from '@chakra-ui/react'
import { CheckCircle, Clock, Trophy, FileText } from 'lucide-react'
import { SessionData } from '@/lib/sessions/getSession'
import { useAuth } from '@/lib/auth-context'

interface ClientActionsProps {
  sessionId: string
  sessionData: SessionData
}

export default function ClientActions({ sessionId, sessionData }: ClientActionsProps) {
  const [notes, setNotes] = useState(sessionData.notes || '')
  const [isUpdatingNotes, setIsUpdatingNotes] = useState(false)
  const [isConfirming, setIsConfirming] = useState(false)
  const { user } = useAuth()
  const router = useRouter()
  const toast = useToast()

  // Determine if current user can interact with this session
  const isParticipant = user && (
    user.id === sessionData.participants.user1.id || 
    user.id === sessionData.participants.user2.id
  )

  // Check if scheduled time has passed
  const isScheduledTimePassed = new Date(sessionData.scheduled_time) < new Date()
  
  // Determine which user is the current user and their buddy
  const getCurrentUserData = () => {
    if (!user) return null
    
    if (user.id === sessionData.participants.user1.id) {
      return {
        currentUser: sessionData.participants.user1,
        buddy: sessionData.participants.user2,
        side: 'user1' as const
      }
    } else if (user.id === sessionData.participants.user2.id) {
      return {
        currentUser: sessionData.participants.user2,
        buddy: sessionData.participants.user1,
        side: 'user2' as const
      }
    }
    
    return null
  }

  const userData = getCurrentUserData()

  // Handle notes update
  const handleNotesUpdate = async () => {
    if (!isParticipant) return

    setIsUpdatingNotes(true)
    try {
      // TODO: Implement API call to update notes
      toast({
        title: 'Notes updated',
        description: 'Your session notes have been saved.',
        status: 'success',
        duration: 3000,
        isClosable: true,
      })
      
      // Refresh the page data
      router.refresh()
    } catch (error) {
      toast({
        title: 'Error updating notes',
        description: 'Could not save your notes. Please try again.',
        status: 'error',
        duration: 3000,
        isClosable: true,
      })
    } finally {
      setIsUpdatingNotes(false)
    }
  }

  // Handle buddy confirmation
  const handleConfirmation = async () => {
    if (!isParticipant || !userData) return

    setIsConfirming(true)
    try {
      // TODO: Implement API call to confirm buddy completion
      toast({
        title: 'Confirmation recorded',
        description: `You've confirmed that ${userData.buddy.name} completed their challenge.`,
        status: 'success',
        duration: 3000,
        isClosable: true,
      })
      
      // Refresh the page data
      router.refresh()
    } catch (error) {
      toast({
        title: 'Error recording confirmation',
        description: 'Could not record your confirmation. Please try again.',
        status: 'error',
        duration: 3000,
        isClosable: true,
      })
    } finally {
      setIsConfirming(false)
    }
  }

  // Don't render if user is not a participant
  if (!isParticipant || !userData) {
    return (
      <Card>
        <CardBody>
          <Text textAlign="center" color="gray.500">
            You don't have permission to interact with this session.
          </Text>
        </CardBody>
      </Card>
    )
  }

  return (
    <VStack spacing={6} align="stretch">
      {/* Confirmation Actions */}
      <Card>
        <CardHeader>
          <Flex align="center">
            <HStack spacing={2}>
              <Icon as={CheckCircle} color="green.500" />
              <Heading size="md">Challenge Confirmations</Heading>
            </HStack>
            <Spacer />
            {isScheduledTimePassed ? (
              <Badge colorScheme="green" variant="outline">
                Session time has passed
              </Badge>
            ) : (
              <Badge colorScheme="yellow" variant="outline">
                <Icon as={Clock} mr={1} />
                Waiting for session time
              </Badge>
            )}
          </Flex>
        </CardHeader>

        <CardBody pt={0}>
          <VStack spacing={4} align="stretch">
            {/* Your confirmation status */}
            <Box>
              <Text fontWeight="semibold" mb={2}>
                Your Challenge: {userData.currentUser.challenge.title}
              </Text>
              {userData.buddy.confirmed ? (
                <HStack spacing={2}>
                  <Icon as={CheckCircle} color="green.500" />
                  <Text color="green.600">
                    {userData.buddy.name} has confirmed you completed your challenge!
                  </Text>
                </HStack>
              ) : (
                <HStack spacing={2}>
                  <Icon as={Clock} color="gray.400" />
                  <Text color="gray.600">
                    Waiting for {userData.buddy.name} to confirm your completion
                  </Text>
                </HStack>
              )}
            </Box>

            <Divider />

            {/* Buddy confirmation action */}
            <Box>
              <Text fontWeight="semibold" mb={2}>
                Buddy's Challenge: {userData.buddy.challenge.title}
              </Text>
              
              {userData.currentUser.confirmed ? (
                <HStack spacing={2}>
                  <Icon as={CheckCircle} color="green.500" />
                  <Text color="green.600">
                    You've confirmed {userData.buddy.name} completed their challenge
                  </Text>
                </HStack>
              ) : (
                <VStack align="start" spacing={3}>
                  <Text fontSize="sm" color="gray.600">
                    Confirm that {userData.buddy.name} successfully completed their challenge
                  </Text>
                  
                  <Button
                    colorScheme="green"
                    onClick={handleConfirmation}
                    isLoading={isConfirming}
                    isDisabled={!isScheduledTimePassed}
                    leftIcon={<CheckCircle size={18} />}
                  >
                    I confirm {userData.buddy.name} completed their challenge
                  </Button>
                  
                  {!isScheduledTimePassed && (
                    <Text fontSize="xs" color="gray.500">
                      This button will be enabled after the scheduled session time
                    </Text>
                  )}
                </VStack>
              )}
            </Box>

            {/* Reputation Preview */}
            <Box bg="blue.50" p={3} borderRadius="md">
              <HStack spacing={2} mb={1}>
                <Icon as={Trophy} color="blue.500" />
                <Text fontSize="sm" fontWeight="semibold" color="blue.800">
                  Reputation Impact
                </Text>
              </HStack>
              <Text fontSize="sm" color="blue.700">
                Completing this session will give you{' '}
                <strong>+{sessionData.reputation_preview[userData.side + '_delta' as keyof typeof sessionData.reputation_preview]} points</strong>
              </Text>
            </Box>
          </VStack>
        </CardBody>
      </Card>

      {/* Session Notes */}
      <Card>
        <CardHeader>
          <HStack spacing={2}>
            <Icon as={FileText} color="gray.500" />
            <Heading size="md">Session Notes</Heading>
          </HStack>
        </CardHeader>

        <CardBody pt={0}>
          <VStack spacing={3} align="stretch">
            <FormControl>
              <FormLabel fontSize="sm">
                Add notes about your session experience
              </FormLabel>
              <Textarea
                value={notes}
                onChange={(e) => setNotes(e.target.value)}
                placeholder="How did the session go? What did you learn? Any tips for your buddy?"
                rows={4}
                maxLength={2000}
              />
              <Text fontSize="xs" color="gray.500" mt={1}>
                {notes.length}/2000 characters
              </Text>
            </FormControl>

            <Button
              onClick={handleNotesUpdate}
              isLoading={isUpdatingNotes}
              isDisabled={notes === (sessionData.notes || '')}
              size="sm"
              alignSelf="flex-start"
            >
              Save Notes
            </Button>
          </VStack>
        </CardBody>
      </Card>
    </VStack>
  )
}