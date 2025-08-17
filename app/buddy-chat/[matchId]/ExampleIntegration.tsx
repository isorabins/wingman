/**
 * Example Integration for Reputation System
 * Shows how to integrate reputation badges into existing chat page
 */

"use client";

import React from 'react';
import {
  Card,
  CardHeader,
  Flex,
  VStack,
  Text,
  Badge,
  Spacer,
  HStack,
  Avatar,
} from '@chakra-ui/react';
import { ReputationBadgeCompact } from '@/components/ReputationBadge';

// Example: Enhanced chat header with reputation
export function EnhancedChatHeader({ matchId, partnerId }: { matchId: string; partnerId: string }) {
  return (
    <Card>
      <CardHeader>
        <Flex align="center">
          <HStack spacing={3}>
            <Avatar size="md" name="Chat Partner" bg="brand.400" color="white" />
            <VStack align="start" spacing={1}>
              <Text fontSize="xl" fontWeight="bold">
                Buddy Chat
              </Text>
              <Text fontSize="sm" color="gray.600">
                Chat with your wingman partner
              </Text>
            </VStack>
          </HStack>
          <Spacer />
          <HStack spacing={3}>
            {/* Partner's Reputation Badge */}
            <VStack spacing={1} align="center">
              <ReputationBadgeCompact userId={partnerId} />
              <Text fontSize="xs" color="gray.500">
                Partner
              </Text>
            </VStack>
            
            {/* Existing Active Match Badge */}
            <Badge colorScheme="green" variant="outline">
              Active Match
            </Badge>
          </HStack>
        </Flex>
      </CardHeader>
    </Card>
  );
}

// Example: Simple integration in any component
export function SimpleReputationExample({ userId }: { userId: string }) {
  return (
    <HStack spacing={2}>
      <Text>User Reputation:</Text>
      <ReputationBadgeCompact userId={userId} />
    </HStack>
  );
}

export default EnhancedChatHeader;