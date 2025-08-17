/**
 * Session Participants Component
 * Displays session participants with reputation badges and confirmation status
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
  Badge,
  Icon,
  Divider,
  useTheme,
} from '@chakra-ui/react';
import { CheckCircle, Clock, XCircle, User } from 'lucide-react';
import { ReputationBadgeCompact } from '@/components/ReputationBadge';

interface SessionParticipant {
  id: string;
  name: string;
  avatar_url?: string;
  confirmed: boolean;
  confirmed_at?: string;
}

interface SessionParticipantsProps {
  participants: SessionParticipant[];
  currentUserId: string;
  sessionStatus: 'scheduled' | 'confirmed' | 'completed' | 'cancelled';
}

export function SessionParticipants({
  participants,
  currentUserId,
  sessionStatus,
}: SessionParticipantsProps) {
  const theme = useTheme();

  const getConfirmationIcon = (confirmed: boolean, isCurrentUser: boolean) => {
    if (confirmed) {
      return <CheckCircle size={16} color={theme.colors.green[500]} />;
    }
    if (isCurrentUser && sessionStatus === 'scheduled') {
      return <Clock size={16} color={theme.colors.yellow[500]} />;
    }
    return <XCircle size={16} color={theme.colors.gray[400]} />;
  };

  const getConfirmationText = (confirmed: boolean, isCurrentUser: boolean) => {
    if (confirmed) return 'Confirmed';
    if (isCurrentUser && sessionStatus === 'scheduled') return 'Awaiting your confirmation';
    return 'Not confirmed';
  };

  const getConfirmationColor = (confirmed: boolean, isCurrentUser: boolean) => {
    if (confirmed) return 'green';
    if (isCurrentUser && sessionStatus === 'scheduled') return 'yellow';
    return 'gray';
  };

  return (
    <Card>
      <CardHeader>
        <HStack spacing={2}>
          <Icon as={User} size={20} color="brand.500" />
          <Text fontSize="lg" fontWeight="bold" color="brand.900">
            Session Participants
          </Text>
        </HStack>
      </CardHeader>

      <CardBody pt={0}>
        <VStack spacing={4} align="stretch">
          {participants.map((participant, index) => {
            const isCurrentUser = participant.id === currentUserId;
            const confirmed = participant.confirmed;

            return (
              <Box key={participant.id}>
                <Flex align="center" justify="space-between">
                  {/* Participant Info */}
                  <HStack spacing={3} flex={1}>
                    <Avatar
                      size="md"
                      name={participant.name}
                      src={participant.avatar_url}
                      bg="brand.400"
                      color="white"
                    />
                    <VStack align="start" spacing={1}>
                      <HStack spacing={2}>
                        <Text fontWeight="semibold" color="brand.900">
                          {participant.name}
                          {isCurrentUser && (
                            <Text as="span" fontSize="sm" color="gray.500" ml={1}>
                              (You)
                            </Text>
                          )}
                        </Text>
                        <ReputationBadgeCompact 
                          userId={participant.id}
                          size="sm"
                        />
                      </HStack>
                      
                      {/* Confirmation Status */}
                      <HStack spacing={2}>
                        {getConfirmationIcon(confirmed, isCurrentUser)}
                        <Text 
                          fontSize="sm" 
                          color={confirmed ? 'green.600' : isCurrentUser ? 'yellow.600' : 'gray.600'}
                        >
                          {getConfirmationText(confirmed, isCurrentUser)}
                        </Text>
                      </HStack>
                      
                      {/* Confirmation Time */}
                      {confirmed && participant.confirmed_at && (
                        <Text fontSize="xs" color="gray.500">
                          Confirmed {new Date(participant.confirmed_at).toLocaleString()}
                        </Text>
                      )}
                    </VStack>
                  </HStack>

                  {/* Status Badge */}
                  <Badge
                    colorScheme={getConfirmationColor(confirmed, isCurrentUser)}
                    variant="subtle"
                    size="sm"
                  >
                    {confirmed ? 'Ready' : 'Pending'}
                  </Badge>
                </Flex>

                {/* Divider between participants */}
                {index < participants.length - 1 && (
                  <Divider mt={4} />
                )}
              </Box>
            );
          })}

          {/* Session Status Summary */}
          <Box mt={4} p={3} bg="gray.50" borderRadius="md">
            <HStack justify="space-between">
              <Text fontSize="sm" fontWeight="medium" color="gray.700">
                Session Status:
              </Text>
              <Badge
                colorScheme={
                  sessionStatus === 'completed' ? 'green' :
                  sessionStatus === 'confirmed' ? 'blue' :
                  sessionStatus === 'scheduled' ? 'yellow' : 'red'
                }
                variant="solid"
                size="sm"
                textTransform="capitalize"
              >
                {sessionStatus}
              </Badge>
            </HStack>
            
            {sessionStatus === 'scheduled' && (
              <Text fontSize="xs" color="gray.600" mt={1}>
                Waiting for all participants to confirm attendance
              </Text>
            )}
            
            {sessionStatus === 'confirmed' && (
              <Text fontSize="xs" color="blue.600" mt={1}>
                All participants confirmed - session ready to proceed
              </Text>
            )}
          </Box>
        </VStack>
      </CardBody>
    </Card>
  );
}

export default SessionParticipants;