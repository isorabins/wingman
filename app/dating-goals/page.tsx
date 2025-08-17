"use client"

import { useState, useEffect, useRef } from "react"
import Link from "next/link"
import { ArrowLeft, Heart, Send } from "lucide-react"
import {
  Box,
  Button,
  Container,
  Flex,
  Heading,
  HStack,
  Text,
  VStack,
  useToast,
  Textarea,
  Alert,
  AlertIcon,
  AlertTitle,
  AlertDescription,
} from "@chakra-ui/react"
import { useAuth } from "@/lib/auth-context"
import {
  datingGoalsApi,
  DatingGoalsApiError,
  ConversationMessage,
  createConversationMessage,
} from "@/lib/dating-goals-api"
import { DatingGoalsChat } from "@/components/DatingGoalsChat"
import { TopicProgress } from "@/components/TopicProgress"
import { GoalsCompletion } from "@/components/GoalsCompletion"

interface DatingGoalsState {
  messages: ConversationMessage[];
  threadId?: string;
  isComplete: boolean;
  topicNumber?: number;
  completionPercentage: number;
  isLoading: boolean;
  isStarted: boolean;
}

export default function DatingGoalsPage() {
  const { user } = useAuth()
  const toast = useToast()
  const inputRef = useRef<HTMLTextAreaElement>(null)

  const [conversationState, setConversationState] = useState<DatingGoalsState>({
    messages: [],
    isComplete: false,
    completionPercentage: 0,
    isLoading: false,
    isStarted: false,
  })

  const [currentMessage, setCurrentMessage] = useState("")
  const [error, setError] = useState<string | null>(null)


  // Load existing conversation on mount
  useEffect(() => {
    if (user?.id) {
      loadExistingGoals()
    }
  }, [user?.id])

  const loadExistingGoals = async () => {
    if (!user?.id) return

    try {
      setConversationState(prev => ({ ...prev, isLoading: true }))
      const goalsData = await datingGoalsApi.getGoalsData(user.id)
      
      if (goalsData.success && goalsData.goals_data) {
        // If user has existing goals data, show completion message
        setConversationState(prev => ({
          ...prev,
          isComplete: true,
          completionPercentage: 100,
          isStarted: true,
          isLoading: false,
          messages: [
            createConversationMessage(
              'assistant',
              `Welcome back! I can see you've already completed your dating goals exploration. Your goals include: ${goalsData.goals || 'building authentic confidence'}. 

Would you like to review your goals, make updates, or proceed to find your wingman buddy?`,
              4
            )
          ]
        }))
      } else {
        setConversationState(prev => ({ ...prev, isLoading: false }))
      }
    } catch (error) {
      console.warn('No existing goals found, starting fresh')
      setConversationState(prev => ({ ...prev, isLoading: false }))
      setError(null)
    }
  }

  const startConversation = async () => {
    if (!user?.id) {
      toast({
        title: "Authentication required",
        description: "Please sign in to continue",
        status: "warning",
        duration: 3000,
        isClosable: true,
      })
      return
    }

    try {
      setConversationState(prev => ({ ...prev, isLoading: true }))
      setError(null)
      
      const response = await datingGoalsApi.startConversation(user.id)
      
      const assistantMessage = createConversationMessage(
        'assistant',
        response.message,
        response.topic_number
      )

      setConversationState(prev => ({
        ...prev,
        messages: [assistantMessage],
        threadId: response.thread_id,
        isComplete: response.is_complete,
        topicNumber: response.topic_number,
        completionPercentage: response.completion_percentage,
        isLoading: false,
        isStarted: true,
      }))

      // Focus input for immediate interaction
      setTimeout(() => inputRef.current?.focus(), 100)
      
    } catch (error) {
      const errorMessage = error instanceof DatingGoalsApiError 
        ? error.message 
        : 'Failed to start conversation'
      
      setError(errorMessage)
      setConversationState(prev => ({ ...prev, isLoading: false }))
      
      toast({
        title: "Error starting conversation",
        description: errorMessage,
        status: "error",
        duration: 5000,
        isClosable: true,
      })
    }
  }

  const sendMessage = async () => {
    if (!currentMessage.trim() || !user?.id || conversationState.isLoading) {
      return
    }

    try {
      const userMessage = createConversationMessage('user', currentMessage.trim())
      
      setConversationState(prev => ({
        ...prev,
        messages: [...prev.messages, userMessage],
        isLoading: true,
      }))
      
      setCurrentMessage("")
      setError(null)

      const response = await datingGoalsApi.continueConversation(
        user.id,
        userMessage.content,
        conversationState.threadId || ""
      )

      const assistantMessage = createConversationMessage(
        'assistant',
        response.message,
        response.topic_number
      )

      setConversationState(prev => ({
        ...prev,
        messages: [...prev.messages, assistantMessage],
        threadId: response.thread_id,
        isComplete: response.is_complete,
        topicNumber: response.topic_number,
        completionPercentage: response.completion_percentage,
        isLoading: false,
      }))

    } catch (error) {
      const errorMessage = error instanceof DatingGoalsApiError 
        ? error.message 
        : 'Failed to send message'
      
      setError(errorMessage)
      setConversationState(prev => ({ ...prev, isLoading: false }))
      
      toast({
        title: "Error sending message",
        description: errorMessage,
        status: "error",
        duration: 5000,
        isClosable: true,
      })
    }
  }

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      sendMessage()
    }
  }

  const resetConversation = async () => {
    if (!user?.id) return

    try {
      setConversationState(prev => ({ ...prev, isLoading: true }))
      await datingGoalsApi.resetGoals(user.id)
      
      setConversationState({
        messages: [],
        isComplete: false,
        completionPercentage: 0,
        isLoading: false,
        isStarted: false,
      })
      
      setError(null)
      
      toast({
        title: "Conversation reset",
        description: "You can start fresh with your dating goals",
        status: "info",
        duration: 3000,
        isClosable: true,
      })
      
    } catch (error) {
      const errorMessage = error instanceof DatingGoalsApiError 
        ? error.message 
        : 'Failed to reset conversation'
      
      setError(errorMessage)
      setConversationState(prev => ({ ...prev, isLoading: false }))
      
      toast({
        title: "Error resetting conversation",
        description: errorMessage,
        status: "error",
        duration: 5000,
        isClosable: true,
      })
    }
  }

  // Welcome screen when not started
  if (!conversationState.isStarted && !conversationState.isLoading) {
    return (
      <Box minH="100vh" bg="brand.50">
        {/* Header */}
        <Box borderBottom="1px solid" borderColor="gray.200">
          <Container maxW="6xl" py={6} px={4}>
            <Flex justify="space-between" align="center">
              <Link href="/">
                <Heading as="h1" size="lg" fontFamily="heading" color="brand.900">
                  Wingman
                </Heading>
              </Link>
              <Button 
                variant="ghost" 
                color="gray.600" 
                _hover={{ color: "brand.900", bg: "gray.200" }}
                as={Link}
                href="/confidence-test"
              >
                <ArrowLeft size={16} style={{ marginRight: '8px' }} />
                Back to Assessment
              </Button>
            </Flex>
          </Container>
        </Box>

        {/* Main Content */}
        <Container maxW="4xl" py={12} px={4}>
          <VStack spacing={8} textAlign="center">
            <VStack spacing={6}>
              <Heart size={64} color="var(--chakra-colors-brand-400)" />
              <Heading 
                as="h1" 
                size="2xl" 
                fontFamily="heading" 
                color="brand.900"
                lineHeight="tight"
              >
                Define Your{" "}
                <Text as="span" color="brand.400">Dating Goals</Text>
              </Heading>
              <Text 
                fontSize="xl" 
                color="gray.600" 
                maxW="3xl" 
                lineHeight="relaxed"
              >
                Work with your AI coach to clarify your dating objectives, 
                preferred venues, and comfort levels for wingman activities.
              </Text>
            </VStack>

            <VStack spacing={4} w="full" maxW="4xl">
              <Text fontSize="lg" fontWeight="medium" color="brand.900">
                Your coach will guide you through:
              </Text>
              <HStack spacing={6} wrap="wrap" justify="center">
                <Text fontSize="sm" color="gray.600">• Core dating goals</Text>
                <Text fontSize="sm" color="gray.600">• Venue preferences</Text>
                <Text fontSize="sm" color="gray.600">• Comfort boundaries</Text>
                <Text fontSize="sm" color="gray.600">• Wingman strategy</Text>
              </HStack>
            </VStack>

            {error && (
              <Alert status="error" rounded="md" maxW="md">
                <AlertIcon />
                <AlertTitle>Error:</AlertTitle>
                <AlertDescription>{error}</AlertDescription>
              </Alert>
            )}

            <VStack spacing={2}>
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
                onClick={startConversation}
                isLoading={conversationState.isLoading}
                loadingText="Starting conversation..."
              >
                Start Goal Setting
              </Button>
              <Text color="gray.600" fontSize="sm">
                Personalized 4-topic conversation • Takes 5-10 minutes
              </Text>
            </VStack>
          </VStack>
        </Container>
      </Box>
    )
  }

  // Main conversation interface
  return (
    <Box minH="100vh" bg="brand.50">
      {/* Header */}
      <Box borderBottom="1px solid" borderColor="gray.200">
        <Container maxW="6xl" py={4} px={4}>
          <Flex justify="space-between" align="center">
            <Link href="/">
              <Heading as="h1" size="lg" fontFamily="heading" color="brand.900">
                Wingman
              </Heading>
            </Link>
            <Button 
              variant="ghost" 
              color="gray.600" 
              _hover={{ color: "brand.900", bg: "gray.200" }}
              size="sm"
              onClick={resetConversation}
            >
              Reset Goals
            </Button>
          </Flex>
        </Container>
      </Box>

      {/* Progress Bar */}
      <TopicProgress 
        topicNumber={conversationState.topicNumber}
        completionPercentage={conversationState.completionPercentage}
        isComplete={conversationState.isComplete}
      />

      {/* Main Chat Area */}
      <Container maxW="4xl" py={6} px={4} flex="1">
        <VStack spacing={6} minH="70vh">
          {/* Messages */}
          <DatingGoalsChat 
            messages={conversationState.messages}
            isLoading={conversationState.isLoading}
          />

          {/* Completion Actions */}
          {conversationState.isComplete && (
            <GoalsCompletion onReviseGoals={resetConversation} />
          )}

          {/* Input Area */}
          {!conversationState.isComplete && conversationState.isStarted && (
            <Box w="full" bg="white" p={4} borderRadius="lg" borderWidth="1px" borderColor="gray.200">
              {error && (
                <Alert status="error" rounded="md" mb={4} size="sm">
                  <AlertIcon />
                  <AlertDescription fontSize="sm">{error}</AlertDescription>
                </Alert>
              )}
              
              <HStack spacing={3}>
                <Textarea
                  ref={inputRef}
                  value={currentMessage}
                  onChange={(e) => setCurrentMessage(e.target.value)}
                  onKeyPress={handleKeyPress}
                  placeholder="Share your thoughts with your coach..."
                  bg="brand.50"
                  borderColor="gray.200"
                  _focus={{ borderColor: "brand.400", bg: "white" }}
                  resize="none"
                  rows={2}
                  disabled={conversationState.isLoading}
                />
                <Button
                  colorScheme="brand"
                  bg="brand.900"
                  color="brand.50"
                  _hover={{ bg: "gray.600" }}
                  onClick={sendMessage}
                  disabled={!currentMessage.trim() || conversationState.isLoading}
                  isLoading={conversationState.isLoading}
                  size="lg"
                  p={3}
                >
                  <Send size={18} />
                </Button>
              </HStack>
              
              <Text fontSize="xs" color="gray.500" mt={2}>
                Press Enter to send • Shift+Enter for new line
              </Text>
            </Box>
          )}
        </VStack>
      </Container>
    </Box>
  )
}