"use client"

import { useState, useEffect, useRef } from "react"
import { useParams } from "next/navigation"
import { Send, MapPin, Coffee, BookOpen, ShoppingBag, Trees } from "lucide-react"
import {
  Box,
  Button,
  Card,
  CardBody,
  CardHeader,
  Container,
  Flex,
  FormControl,
  HStack,
  IconButton,
  Input,
  Spacer,
  Text,
  VStack,
  useToast,
  Badge,
  Collapse,
  useDisclosure,
  Divider,
  Skeleton,
  Avatar,
} from "@chakra-ui/react"

interface ChatMessage {
  id: string;
  match_id: string;
  sender_id: string;
  message_text: string;
  created_at: string;
}

interface ChatResponse {
  messages: ChatMessage[];
  has_more: boolean;
  next_cursor?: string;
}

interface SendMessageResponse {
  success: boolean;
  message_id: string;
  created_at: string;
}

export default function BuddyChatPage() {
  const params = useParams()
  const matchId = params.matchId as string
  const [messages, setMessages] = useState<ChatMessage[]>([])
  const [messageInput, setMessageInput] = useState("")
  const [isLoading, setIsLoading] = useState(true)
  const [isSending, setIsSending] = useState(false)
  const [currentUserId, setCurrentUserId] = useState<string>("")
  const messagesEndRef = useRef<HTMLDivElement>(null)
  const pollingRef = useRef<NodeJS.Timeout | null>(null)
  const toast = useToast()
  
  // Venue suggestions
  const { isOpen: venueOpen, onToggle: toggleVenue } = useDisclosure()
  
  const venueCategories = [
    {
      icon: Coffee,
      title: "Coffee Shops",
      description: "Relaxed atmosphere for conversation",
      examples: ["Local coffee shop", "Café with outdoor seating", "Bookstore café"]
    },
    {
      icon: BookOpen, 
      title: "Bookstores",
      description: "Quiet spaces with conversation starters",
      examples: ["Independent bookstore", "Library reading area", "Used book shop"]
    },
    {
      icon: ShoppingBag,
      title: "Malls",
      description: "Busy environments for practice",
      examples: ["Food court", "Shopping center", "Department store"]
    },
    {
      icon: Trees,
      title: "Parks",
      description: "Outdoor spaces for natural interactions",
      examples: ["Local park", "Walking trail", "Public garden"]
    }
  ]

  // Scroll to bottom of messages
  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" })
  }

  // Fetch messages from API
  const fetchMessages = async () => {
    try {
      const response = await fetch(`/api/chat/messages/${matchId}`, {
        headers: {
          "X-Test-User-ID": currentUserId || "test-user-123" // For development
        }
      })
      
      if (!response.ok) {
        throw new Error("Failed to fetch messages")
      }
      
      const data: ChatResponse = await response.json()
      setMessages(data.messages)
      setTimeout(scrollToBottom, 100) // Delay to ensure DOM update
    } catch (error) {
      console.error("Error fetching messages:", error)
      toast({
        title: "Error loading messages",
        description: "Could not load chat messages. Please try again.",
        status: "error",
        duration: 3000,
        isClosable: true,
      })
    } finally {
      setIsLoading(false)
    }
  }

  // Send message
  const sendMessage = async () => {
    if (!messageInput.trim() || isSending) return
    
    const messageText = messageInput.trim()
    if (messageText.length < 2 || messageText.length > 2000) {
      toast({
        title: "Invalid message length",
        description: "Message must be between 2 and 2000 characters",
        status: "warning",
        duration: 3000,
        isClosable: true,
      })
      return
    }
    
    setIsSending(true)
    
    try {
      const response = await fetch("/api/chat/send", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "X-Test-User-ID": currentUserId || "test-user-123" // For development
        },
        body: JSON.stringify({
          match_id: matchId,
          message: messageText
        })
      })
      
      if (!response.ok) {
        const errorData = await response.json()
        throw new Error(errorData.detail || "Failed to send message")
      }
      
      const data: SendMessageResponse = await response.json()
      
      // Clear input and fetch updated messages
      setMessageInput("")
      await fetchMessages()
      
    } catch (error: any) {
      console.error("Error sending message:", error)
      toast({
        title: "Error sending message",
        description: error.message || "Could not send message. Please try again.",
        status: "error",
        duration: 3000,
        isClosable: true,
      })
    } finally {
      setIsSending(false)
    }
  }

  // Handle Enter key press
  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault()
      sendMessage()
    }
  }

  // Set up polling for new messages
  useEffect(() => {
    // Initial load
    fetchMessages()
    
    // Set up polling every 5 seconds
    pollingRef.current = setInterval(fetchMessages, 5000)
    
    // Cleanup on unmount
    return () => {
      if (pollingRef.current) {
        clearInterval(pollingRef.current)
      }
    }
  }, [matchId])

  // Format message timestamp
  const formatTime = (timestamp: string) => {
    const date = new Date(timestamp)
    return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
  }

  // Determine if message is from current user
  const isOwnMessage = (senderId: string) => {
    return senderId === currentUserId
  }

  return (
    <Container maxW="4xl" py={8}>
      <VStack spacing={6} align="stretch">
        {/* Header */}
        <Card>
          <CardHeader>
            <Flex align="center">
              <VStack align="start" spacing={1}>
                <Text fontSize="xl" fontWeight="bold">
                  Buddy Chat
                </Text>
                <Text fontSize="sm" color="gray.600">
                  Chat with your wingman partner
                </Text>
              </VStack>
              <Spacer />
              <Badge colorScheme="green" variant="outline">
                Active Match
              </Badge>
            </Flex>
          </CardHeader>
        </Card>

        {/* Main Chat Area */}
        <Card flex={1}>
          <CardBody p={0}>
            <Flex direction="column" h="500px">
              {/* Messages Area */}
              <Box flex={1} overflowY="auto" p={4}>
                <VStack spacing={3} align="stretch">
                  {isLoading ? (
                    // Loading skeletons
                    Array.from({ length: 3 }, (_, i) => (
                      <Skeleton key={i} height="60px" borderRadius="md" />
                    ))
                  ) : messages.length === 0 ? (
                    // Empty state
                    <Box textAlign="center" py={8}>
                      <Text color="gray.500" mb={2}>
                        No messages yet
                      </Text>
                      <Text fontSize="sm" color="gray.400">
                        Start the conversation by sending a message below
                      </Text>
                    </Box>
                  ) : (
                    // Messages
                    messages.map((message) => {
                      const isOwn = isOwnMessage(message.sender_id)
                      return (
                        <Flex
                          key={message.id}
                          justify={isOwn ? "flex-end" : "flex-start"}
                        >
                          <Box
                            maxW="70%"
                            bg={isOwn ? "blue.500" : "gray.100"}
                            color={isOwn ? "white" : "black"}
                            px={3}
                            py={2}
                            borderRadius="lg"
                            borderBottomLeftRadius={isOwn ? "lg" : "sm"}
                            borderBottomRightRadius={isOwn ? "sm" : "lg"}
                          >
                            <Text fontSize="sm">{message.message_text}</Text>
                            <Text
                              fontSize="xs"
                              opacity={0.7}
                              mt={1}
                              textAlign="right"
                            >
                              {formatTime(message.created_at)}
                            </Text>
                          </Box>
                        </Flex>
                      )
                    })
                  )}
                  <div ref={messagesEndRef} />
                </VStack>
              </Box>

              {/* Message Input */}
              <Box p={4} borderTop="1px" borderColor="gray.200">
                <FormControl>
                  <HStack spacing={2}>
                    <Input
                      value={messageInput}
                      onChange={(e) => setMessageInput(e.target.value)}
                      onKeyPress={handleKeyPress}
                      placeholder="Type your message..."
                      disabled={isSending}
                      maxLength={2000}
                    />
                    <IconButton
                      aria-label="Send message"
                      icon={<Send size={18} />}
                      onClick={sendMessage}
                      isLoading={isSending}
                      disabled={!messageInput.trim() || isSending}
                      colorScheme="blue"
                    />
                  </HStack>
                  <Text fontSize="xs" color="gray.500" mt={1}>
                    {messageInput.length}/2000 characters
                  </Text>
                </FormControl>
              </Box>
            </Flex>
          </CardBody>
        </Card>

        {/* Venue Suggestions Panel */}
        <Card>
          <CardHeader>
            <Button
              variant="ghost"
              onClick={toggleVenue}
              leftIcon={<MapPin size={18} />}
              w="full"
              justifyContent="flex-start"
            >
              Venue Suggestions
            </Button>
          </CardHeader>
          <Collapse in={venueOpen}>
            <CardBody pt={0}>
              <VStack spacing={4} align="stretch">
                {venueCategories.map((category) => {
                  const IconComponent = category.icon
                  return (
                    <Box key={category.title}>
                      <HStack spacing={3} mb={2}>
                        <IconComponent size={20} />
                        <VStack align="start" spacing={0}>
                          <Text fontWeight="semibold">{category.title}</Text>
                          <Text fontSize="sm" color="gray.600">
                            {category.description}
                          </Text>
                        </VStack>
                      </HStack>
                      <VStack align="start" spacing={1} pl={8}>
                        {category.examples.map((example) => (
                          <Text key={example} fontSize="sm" color="gray.500">
                            • {example}
                          </Text>
                        ))}
                      </VStack>
                      <Divider mt={3} />
                    </Box>
                  )
                })}
                <Box bg="blue.50" p={3} borderRadius="md">
                  <Text fontSize="sm" color="blue.800">
                    💡 <strong>Tip:</strong> Choose venues where you feel comfortable and can easily start conversations. Remember, the goal is to practice together!
                  </Text>
                </Box>
              </VStack>
            </CardBody>
          </Collapse>
        </Card>
      </VStack>
    </Container>
  )
}