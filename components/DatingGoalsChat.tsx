"use client"

import { useRef, useEffect } from "react"
import {
  Box,
  Card,
  CardBody,
  Flex,
  HStack,
  VStack,
  Text,
  Spinner,
} from "@chakra-ui/react"
import { MessageCircle } from "lucide-react"
import { ConversationMessage } from "@/lib/dating-goals-api"

interface DatingGoalsChatProps {
  messages: ConversationMessage[];
  isLoading: boolean;
}

export function DatingGoalsChat({ messages, isLoading }: DatingGoalsChatProps) {
  const messagesEndRef = useRef<HTMLDivElement>(null)

  // Auto-scroll to bottom when new messages arrive
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" })
  }, [messages, isLoading])

  return (
    <VStack spacing={4} w="full" align="stretch" minH="400px">
      {messages.map((message) => (
        <Flex
          key={message.id}
          justify={message.role === 'user' ? 'flex-end' : 'flex-start'}
          w="full"
        >
          <Card
            maxW="85%"
            bg={message.role === 'user' ? 'brand.900' : 'white'}
            color={message.role === 'user' ? 'brand.50' : 'brand.900'}
            borderColor={message.role === 'user' ? 'brand.900' : 'gray.200'}
            borderWidth="1px"
            shadow="sm"
          >
            <CardBody p={4}>
              {message.role === 'assistant' && (
                <HStack spacing={2} mb={2}>
                  <MessageCircle size={16} color="var(--chakra-colors-brand-400)" />
                  <Text fontSize="sm" fontWeight="medium" color="brand.400">
                    Connell (Your Coach)
                  </Text>
                </HStack>
              )}
              <Text fontSize="sm" lineHeight="relaxed" whiteSpace="pre-wrap">
                {message.content}
              </Text>
              <Text 
                fontSize="xs" 
                color={message.role === 'user' ? 'brand.100' : 'gray.500'}
                mt={2}
              >
                {message.timestamp.toLocaleTimeString([], { 
                  hour: '2-digit', 
                  minute: '2-digit' 
                })}
              </Text>
            </CardBody>
          </Card>
        </Flex>
      ))}

      {isLoading && (
        <Flex justify="flex-start" w="full">
          <Card maxW="85%" bg="white" borderColor="gray.200" borderWidth="1px">
            <CardBody p={4}>
              <HStack spacing={2}>
                <Spinner size="sm" color="brand.400" />
                <Text fontSize="sm" color="gray.600">
                  Connell is thinking...
                </Text>
              </HStack>
            </CardBody>
          </Card>
        </Flex>
      )}

      <div ref={messagesEndRef} />
    </VStack>
  )
}

export default DatingGoalsChat