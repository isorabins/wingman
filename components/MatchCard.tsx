/**
 * Match Card Component
 * Displays match information with reputation badges and action buttons
 */

"use client";

import React from 'react';
import {
  Box,
  Card,
  CardBody,
  CardHeader,
  Flex,
  VStack,
  HStack,
  Text,
  Avatar,
  Button,
  Badge,
  Spacer,
  useTheme,
  Icon,
} from '@chakra-ui/react';
import { MapPin, Calendar, MessageCircle } from 'lucide-react';
import { ReputationBadgeCompact } from './ReputationBadge';

export interface MatchData {
  id: string;
  status: 'pending' | 'accepted' | 'declined';
  created_at: string;
  partner: {
    id: string;
    name: string;
    avatar_url?: string;
    location?: string;
    experience_level?: 'beginner' | 'intermediate' | 'advanced';
  };
  distance_miles?: number;
}

interface MatchCardProps {
  match: MatchData;
  currentUserId: string;
  onAccept?: (matchId: string) => void;
  onDecline?: (matchId: string) => void;
  onChat?: (matchId: string) => void;
  onViewProfile?: (userId: string) => void;
  isLoading?: boolean;
}

export function MatchCard({
  match,
  currentUserId,
  onAccept,
  onDecline,
  onChat,
  onViewProfile,
  isLoading = false,
}: MatchCardProps) {
  const theme = useTheme();

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'accepted':
        return 'green';
      case 'pending':
        return 'yellow';
      case 'declined':
        return 'red';
      default:
        return 'gray';
    }
  };

  const getExperienceColor = (level?: string) => {
    switch (level) {
      case 'beginner':
        return 'blue';
      case 'intermediate':
        return 'orange';
      case 'advanced':
        return 'purple';
      default:
        return 'gray';
    }
  };

  const formatDate = (dateString: string) => {
    const date = new Date(dateString);
    return date.toLocaleDateString(undefined, {
      month: 'short',
      day: 'numeric',
    });
  };

  const renderActionButtons = () => {
    if (match.status === 'pending') {
      return (
        <HStack spacing={2} width="100%">
          <Button
            size="sm"
            colorScheme="green"
            variant="solid"
            onClick={() => onAccept?.(match.id)}
            isLoading={isLoading}
            flex={1}
          >
            Accept
          </Button>
          <Button
            size="sm"
            colorScheme="red"
            variant="outline"
            onClick={() => onDecline?.(match.id)}
            isLoading={isLoading}
            flex={1}
          >
            Decline
          </Button>
        </HStack>
      );
    }

    if (match.status === 'accepted') {
      return (
        <HStack spacing={2} width="100%">
          <Button
            size="sm"
            colorScheme="blue"
            variant="solid"
            leftIcon={<MessageCircle size={16} />}
            onClick={() => onChat?.(match.id)}
            flex={1}
          >
            Chat
          </Button>
          <Button
            size="sm"
            variant="outline"
            onClick={() => onViewProfile?.(match.partner.id)}
          >
            Profile
          </Button>
        </HStack>
      );
    }

    return null;
  };

  return (
    <Card
      width="100%"
      maxW="400px"
      bg="white"
      shadow="md"
      borderRadius="xl"
      border="1px solid"
      borderColor="gray.200"
      _hover={{
        shadow: 'lg',
        transform: 'translateY(-2px)',
        transition: 'all 0.2s ease-in-out',
      }}
    >
      <CardHeader pb={2}>
        <Flex align="center" justify="space-between">
          <Badge
            colorScheme={getStatusColor(match.status)}
            variant="subtle"
            size="sm"
            textTransform="capitalize"
          >
            {match.status}
          </Badge>
          <Text fontSize="xs" color="gray.500">
            {formatDate(match.created_at)}
          </Text>
        </Flex>
      </CardHeader>

      <CardBody pt={0}>
        <VStack spacing={4} align="stretch">
          {/* Partner Info */}
          <Flex align="center" gap={3}>
            <Avatar
              size="lg"
              name={match.partner.name}
              src={match.partner.avatar_url}
              bg="brand.400"
              color="white"
            />
            <VStack align="start" spacing={1} flex={1}>
              <Flex align="center" gap={2} width="100%">
                <Text fontWeight="bold" fontSize="lg" color="brand.900">
                  {match.partner.name}
                </Text>
                <Spacer />
                <ReputationBadgeCompact 
                  userId={match.partner.id}
                  size="sm"
                />
              </Flex>
              <HStack spacing={3} fontSize="sm" color="gray.600">
                {match.partner.location && (
                  <HStack spacing={1}>
                    <Icon as={MapPin} size={14} />
                    <Text>{match.partner.location}</Text>
                  </HStack>
                )}
                {match.distance_miles && (
                  <Text>
                    {match.distance_miles.toFixed(1)} miles
                  </Text>
                )}
              </HStack>
            </VStack>
          </Flex>

          {/* Experience Level */}
          {match.partner.experience_level && (
            <Flex justify="center">
              <Badge
                colorScheme={getExperienceColor(match.partner.experience_level)}
                variant="outline"
                size="sm"
                textTransform="capitalize"
              >
                {match.partner.experience_level} Level
              </Badge>
            </Flex>
          )}

          {/* Action Buttons */}
          {renderActionButtons()}
        </VStack>
      </CardBody>
    </Card>
  );
}

/**
 * Skeleton loader for match cards
 */
export function MatchCardSkeleton() {
  return (
    <Card
      width="100%"
      maxW="400px"
      bg="white"
      shadow="md"
      borderRadius="xl"
      border="1px solid"
      borderColor="gray.200"
    >
      <CardHeader pb={2}>
        <Flex align="center" justify="space-between">
          <Box width="60px" height="20px" bg="gray.200" borderRadius="md" />
          <Box width="40px" height="16px" bg="gray.200" borderRadius="md" />
        </Flex>
      </CardHeader>
      <CardBody pt={0}>
        <VStack spacing={4} align="stretch">
          <Flex align="center" gap={3}>
            <Box width="64px" height="64px" bg="gray.200" borderRadius="full" />
            <VStack align="start" spacing={2} flex={1}>
              <Box width="120px" height="20px" bg="gray.200" borderRadius="md" />
              <Box width="80px" height="16px" bg="gray.200" borderRadius="md" />
            </VStack>
          </Flex>
          <Box width="100px" height="20px" bg="gray.200" borderRadius="md" mx="auto" />
          <HStack spacing={2}>
            <Box width="100%" height="32px" bg="gray.200" borderRadius="md" />
            <Box width="100%" height="32px" bg="gray.200" borderRadius="md" />
          </HStack>
        </VStack>
      </CardBody>
    </Card>
  );
}

export default MatchCard;