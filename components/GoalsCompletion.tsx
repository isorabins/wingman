"use client"

import Link from "next/link"
import {
  Card,
  CardBody,
  VStack,
  HStack,
  Text,
  Button,
} from "@chakra-ui/react"
import { Target } from "lucide-react"

interface GoalsCompletionProps {
  onReviseGoals: () => void;
}

export function GoalsCompletion({ onReviseGoals }: GoalsCompletionProps) {
  return (
    <Card bg="green.50" borderColor="green.200" borderWidth="1px" w="full">
      <CardBody p={6}>
        <VStack spacing={4}>
          <HStack spacing={2}>
            <Target size={20} color="green" />
            <Text fontSize="lg" fontWeight="medium" color="green.700">
              Dating Goals Complete!
            </Text>
          </HStack>
          <Text fontSize="sm" color="green.600" textAlign="center">
            Great work! Your dating goals have been saved and will help match you 
            with the perfect wingman buddy. Your coach now understands your objectives
            and can provide better guidance.
          </Text>
          <VStack spacing={3}>
            <HStack spacing={3} wrap="wrap" justify="center">
              <Button 
                size="sm"
                colorScheme="green"
                bg="green.600"
                color="white"
                _hover={{ bg: "green.700" }}
                rounded="full"
                px={6}
                as={Link}
                href="/find-buddy"
              >
                Find My Wingman
              </Button>
              <Button 
                size="sm"
                variant="outline"
                borderColor="green.400"
                color="green.700"
                _hover={{ bg: "green.100" }}
                rounded="full"
                px={6}
                onClick={onReviseGoals}
              >
                Revise Goals
              </Button>
            </HStack>
            <Text fontSize="xs" color="green.600" textAlign="center" maxW="md">
              Your goals will be used to find compatible wingman partners and 
              guide future coaching conversations.
            </Text>
          </VStack>
        </VStack>
      </CardBody>
    </Card>
  )
}

export default GoalsCompletion