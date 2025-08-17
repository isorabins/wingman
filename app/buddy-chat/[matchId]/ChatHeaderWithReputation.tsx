/**
 * Enhanced Chat Header with Reputation Badges
 * Displays chat partner information with reputation indicators
 */

"use client";

import React, { useState, useEffect } from 'react';
import {
  Box,
  Flex,
  VStack,
  HStack,
  Text,
  Badge,
  Avatar,
  Spacer,
  Skeleton,
  useToast,
} from '@chakra-ui/react';
import { ReputationBadgeCompact } from '@/components/ReputationBadge';

interface MatchParticipant {
  id: string;
  name?: string;
  avatar_url?: string;
}

interface MatchInfo {
  id: string;
  user1_id: string;
  user2_id: string;
  status: string;
  participants?: {
    user1: MatchParticipant;
    user2: MatchParticipant;
  };
}

interface ChatHeaderWithReputationProps {
  matchId: string;
  currentUserId?: string;
}

export function ChatHeaderWithReputation({ 
  matchId, 
  currentUserId = "test-user-123" 
}: ChatHeaderWithReputationProps) {
  const [matchInfo, setMatchInfo] = useState<MatchInfo | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const toast = useToast();

  // Fetch match information
  useEffect(() => {
    const fetchMatchInfo = async () => {
      try {
        setIsLoading(true);
        setError(null);
        
        // This would normally fetch from a match info API
        // For now, using mock data structure
        const response = await fetch(`/api/matches/${matchId}`, {
          headers: {
            'X-Test-User-ID': currentUserId,
          },
        }).catch(() => {
          // Fallback mock data for demo
          return {
            ok: true,
            json: () => Promise.resolve({
              id: matchId,
              user1_id: "user-1",
              user2_id: "user-2", 
              status: "accepted",
              participants: {
                user1: { id: "user-1", name: "Alex" },
                user2: { id: "user-2", name: "Jordan" }
              }
            })
          };
        });

        if (response.ok) {
          const data = await response.json();
          setMatchInfo(data);
        } else {
          throw new Error('Failed to fetch match info');
        }
      } catch (err) {
        console.error('Error fetching match info:', err);
        setError('Failed to load match information');
        
        // Show fallback data for demo
        setMatchInfo({
          id: matchId,
          user1_id: "demo-user-1",
          user2_id: "demo-user-2",
          status: "accepted",
          participants: {
            user1: { id: "demo-user-1", name: "Demo Partner" },
            user2: { id: "demo-user-2", name: "You" }
          }
        });
      } finally {
        setIsLoading(false);
      }
    };

    if (matchId) {
      fetchMatchInfo();
    }
  }, [matchId, currentUserId]);

  // Get chat partner info
  const getChatPartner = (): MatchParticipant | null => {
    if (!matchInfo?.participants) return null;
    
    const { user1, user2 } = matchInfo.participants;
    return user1.id === currentUserId ? user2 : user1;
  };

  const chatPartner = getChatPartner();

  if (isLoading) {
    return (
      <Flex align="center" p={4}>
        <HStack spacing={3}>
          <Skeleton width="40px" height="40px" borderRadius="full" />
          <VStack align="start" spacing={1}>
            <Skeleton width="120px" height="20px" />
            <Skeleton width="80px" height="16px" />
          </VStack>
        </HStack>
        <Spacer />
        <HStack spacing={2}>
          <Skeleton width="60px" height="24px" borderRadius="full" />
          <Skeleton width="80px" height="24px" borderRadius="full" />
        </HStack>
      </Flex>
    );
  }

  return (
    <Flex align="center" p={4}>
      <HStack spacing={3}>
        <Avatar 
          size="md" 
          name={chatPartner?.name || "Chat Partner"}
          src={chatPartner?.avatar_url}
          bg="brand.400"
          color="white"
        />
        <VStack align="start" spacing={1}>
          <Text fontSize="xl" fontWeight="bold" color="brand.900">
            {chatPartner?.name || "Chat Partner"}
          </Text>
          <Text fontSize="sm" color="gray.600">
            Your wingman partner
          </Text>
        </VStack>
      </HStack>
      
      <Spacer />
      
      <HStack spacing={3}>
        {/* Partner's Reputation Badge */}
        {chatPartner && (
          <VStack spacing={1} align="center">
            <ReputationBadgeCompact userId={chatPartner.id} />
            <Text fontSize="xs" color="gray.500">
              Partner
            </Text>
          </VStack>
        )}
        
        {/* Match Status Badge */}
        <Badge 
          colorScheme={matchInfo?.status === 'accepted' ? 'green' : 'yellow'} 
          variant="outline"
          size="md"
        >
          {matchInfo?.status === 'accepted' ? 'Active Match' : 'Pending'}
        </Badge>
      </HStack>
    </Flex>
  );
}

export default ChatHeaderWithReputation;