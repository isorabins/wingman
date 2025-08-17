"use client"

import {
  Box,
  Container,
  VStack,
  HStack,
  Progress,
  Badge,
  Text,
} from "@chakra-ui/react"
import { getTopicTitle, formatCompletionPercentage } from "@/lib/dating-goals-api"

interface TopicProgressProps {
  topicNumber?: number;
  completionPercentage: number;
  isComplete: boolean;
}

export function TopicProgress({ 
  topicNumber, 
  completionPercentage, 
  isComplete 
}: TopicProgressProps) {
  if (isComplete) {
    return (
      <Box bg="green.50" borderBottom="1px solid" borderColor="green.200" py={4}>
        <Container maxW="4xl" px={4}>
          <VStack spacing={3}>
            <HStack justify="center" spacing={3}>
              <Badge colorScheme="green" variant="solid" rounded="full" px={3} py={1}>
                Goals Complete! 🎉
              </Badge>
            </HStack>
            <Progress 
              value={100} 
              w="full" 
              h={2} 
              colorScheme="green"
              rounded="full"
              role="progressbar"
              aria-valuenow={100}
              aria-valuemin={0}
              aria-valuemax={100}
              aria-label="Dating goals complete"
            />
          </VStack>
        </Container>
      </Box>
    )
  }

  if (!topicNumber) {
    return null
  }

  return (
    <Box bg="white" borderBottom="1px solid" borderColor="gray.200" py={4}>
      <Container maxW="4xl" px={4}>
        <VStack spacing={3}>
          <HStack justify="center" spacing={3}>
            <Badge colorScheme="brand" variant="solid" rounded="full" px={3} py={1}>
              {getTopicTitle(topicNumber)}
            </Badge>
            <Text fontSize="sm" color="gray.600">
              {formatCompletionPercentage(completionPercentage)} complete
            </Text>
          </HStack>
          <Progress 
            value={completionPercentage} 
            w="full" 
            h={2} 
            colorScheme="brand"
            rounded="full"
            role="progressbar"
            aria-valuenow={completionPercentage}
            aria-valuemin={0}
            aria-valuemax={100}
            aria-label={`Dating goals progress: ${formatCompletionPercentage(completionPercentage)} complete`}
          />
        </VStack>
      </Container>
    </Box>
  )
}

export default TopicProgress