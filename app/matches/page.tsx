/**
 * Matches Page
 * Displays user matches with reputation badges and filtering options
 */

"use client";

import React, { useState, useEffect } from 'react';
import {
  Box,
  Container,
  Heading,
  Text,
  VStack,
  HStack,
  Button,
  Badge,
  Flex,
  Spacer,
  SimpleGrid,
  Tabs,
  TabList,
  TabPanels,
  Tab,
  TabPanel,
  useToast,
  Spinner,
  Alert,
  AlertIcon,
  Select,
  Icon,
} from '@chakra-ui/react';
import { Users, ArrowLeft, Filter, Refresh } from 'lucide-react';
import Link from 'next/link';
import { useRouter } from 'next/navigation';
import MatchCard, { MatchCardSkeleton, MatchData } from '@/components/MatchCard';

export default function MatchesPage() {
  const [matches, setMatches] = useState<MatchData[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [actionLoading, setActionLoading] = useState<string | null>(null);
  const [reputationFilter, setReputationFilter] = useState<string>('all');
  const [currentUserId] = useState('test-user-123'); // In real app, get from auth context
  
  const toast = useToast();
  const router = useRouter();

  // Mock matches data - in real app, fetch from API
  const mockMatches: MatchData[] = [
    {
      id: 'match-1',
      status: 'pending',
      created_at: '2024-08-17T10:00:00Z',
      partner: {
        id: 'user-001',
        name: 'Alex Thompson',
        avatar_url: undefined,
        location: 'San Francisco, CA',
        experience_level: 'intermediate',
      },
      distance_miles: 2.3,
    },
    {
      id: 'match-2',
      status: 'accepted',
      created_at: '2024-08-16T15:30:00Z',
      partner: {
        id: 'user-002', 
        name: 'Jordan Rivera',
        avatar_url: undefined,
        location: 'Oakland, CA',
        experience_level: 'beginner',
      },
      distance_miles: 8.7,
    },
    {
      id: 'match-3',
      status: 'accepted',
      created_at: '2024-08-15T09:15:00Z',
      partner: {
        id: 'user-003',
        name: 'Sam Chen',
        avatar_url: undefined,
        location: 'Berkeley, CA', 
        experience_level: 'advanced',
      },
      distance_miles: 5.1,
    },
    {
      id: 'match-4',
      status: 'pending',
      created_at: '2024-08-14T20:45:00Z',
      partner: {
        id: 'user-004',
        name: 'Casey Martinez',
        avatar_url: undefined,
        location: 'Palo Alto, CA',
        experience_level: 'intermediate',
      },
      distance_miles: 12.4,
    },
  ];

  // Load matches
  useEffect(() => {
    const loadMatches = async () => {
      try {
        setIsLoading(true);
        setError(null);
        
        // Simulate API delay
        await new Promise(resolve => setTimeout(resolve, 1000));
        
        // In real app: const response = await fetch('/api/matches');
        setMatches(mockMatches);
      } catch (err) {
        setError('Failed to load matches');
        console.error('Error loading matches:', err);
      } finally {
        setIsLoading(false);
      }
    };

    loadMatches();
  }, []);

  // Handle match actions
  const handleAcceptMatch = async (matchId: string) => {
    try {
      setActionLoading(matchId);
      
      // Simulate API call
      await new Promise(resolve => setTimeout(resolve, 1000));
      
      // Update match status
      setMatches(prev => prev.map(match => 
        match.id === matchId 
          ? { ...match, status: 'accepted' as const }
          : match
      ));
      
      toast({
        title: 'Match Accepted!',
        description: 'You can now start chatting with your new wingman buddy.',
        status: 'success',
        duration: 4000,
        isClosable: true,
      });
    } catch (err) {
      toast({
        title: 'Error',
        description: 'Failed to accept match. Please try again.',
        status: 'error',
        duration: 4000,
        isClosable: true,
      });
    } finally {
      setActionLoading(null);
    }
  };

  const handleDeclineMatch = async (matchId: string) => {
    try {
      setActionLoading(matchId);
      
      // Simulate API call
      await new Promise(resolve => setTimeout(resolve, 1000));
      
      // Remove match from list
      setMatches(prev => prev.filter(match => match.id !== matchId));
      
      toast({
        title: 'Match Declined',
        description: 'We\'ll find you another match soon.',
        status: 'info',
        duration: 3000,
        isClosable: true,
      });
    } catch (err) {
      toast({
        title: 'Error',
        description: 'Failed to decline match. Please try again.',
        status: 'error',
        duration: 4000,
        isClosable: true,
      });
    } finally {
      setActionLoading(null);
    }
  };

  const handleStartChat = (matchId: string) => {
    router.push(`/buddy-chat/${matchId}`);
  };

  const handleViewProfile = (userId: string) => {
    router.push(`/profile/${userId}`);
  };

  // Filter matches by status
  const pendingMatches = matches.filter(match => match.status === 'pending');
  const acceptedMatches = matches.filter(match => match.status === 'accepted');

  // Render matches grid
  const renderMatches = (matchList: MatchData[]) => {
    if (matchList.length === 0) {
      return (
        <Box textAlign="center" py={8}>
          <Text color="gray.500" fontSize="lg">
            No matches found
          </Text>
          <Text color="gray.400" fontSize="sm" mt={2}>
            {matches.length === 0 ? 'Check back soon for new matches!' : 'All matches are in other categories.'}
          </Text>
        </Box>
      );
    }

    return (
      <SimpleGrid columns={{ base: 1, md: 2, lg: 3 }} spacing={6}>
        {matchList.map((match) => (
          <MatchCard
            key={match.id}
            match={match}
            currentUserId={currentUserId}
            onAccept={handleAcceptMatch}
            onDecline={handleDeclineMatch}
            onChat={handleStartChat}
            onViewProfile={handleViewProfile}
            isLoading={actionLoading === match.id}
          />
        ))}
      </SimpleGrid>
    );
  };

  return (
    <Box minH="100vh" bg="brand.50">
      {/* Header */}
      <Box borderBottom="1px solid" borderColor="gray.200" bg="white">
        <Container maxW="6xl" py={6} px={4}>
          <Flex align="center">
            <Link href="/">
              <Heading as="h1" size="lg" fontFamily="heading" color="brand.900">
                Wingman
              </Heading>
            </Link>
            <Spacer />
            <Button
              variant="ghost"
              leftIcon={<ArrowLeft size={16} />}
              as={Link}
              href="/"
            >
              Back to Home
            </Button>
          </Flex>
        </Container>
      </Box>

      {/* Main Content */}
      <Container maxW="6xl" py={8} px={4}>
        <VStack spacing={8} align="stretch">
          {/* Page Header */}
          <VStack spacing={4} textAlign="center">
            <Icon as={Users} size={48} color="brand.400" />
            <Heading as="h1" size="2xl" fontFamily="heading" color="brand.900">
              Your Matches
            </Heading>
            <Text fontSize="lg" color="gray.600" maxW="3xl">
              Connect with your wingman buddies and start practicing together
            </Text>
          </VStack>

          {/* Error State */}
          {error && (
            <Alert status="error" borderRadius="md">
              <AlertIcon />
              {error}
              <Spacer />
              <Button
                size="sm"
                leftIcon={<Refresh size={16} />}
                onClick={() => window.location.reload()}
              >
                Retry
              </Button>
            </Alert>
          )}

          {/* Loading State */}
          {isLoading ? (
            <SimpleGrid columns={{ base: 1, md: 2, lg: 3 }} spacing={6}>
              {Array.from({ length: 6 }, (_, i) => (
                <MatchCardSkeleton key={i} />
              ))}
            </SimpleGrid>
          ) : (
            /* Matches Content */
            <Tabs variant="enclosed" colorScheme="brand">
              <TabList>
                <Tab>
                  Pending Matches 
                  {pendingMatches.length > 0 && (
                    <Badge ml={2} colorScheme="yellow" variant="solid" borderRadius="full">
                      {pendingMatches.length}
                    </Badge>
                  )}
                </Tab>
                <Tab>
                  Active Matches
                  {acceptedMatches.length > 0 && (
                    <Badge ml={2} colorScheme="green" variant="solid" borderRadius="full">
                      {acceptedMatches.length}
                    </Badge>
                  )}
                </Tab>
              </TabList>

              <TabPanels>
                <TabPanel px={0}>
                  <VStack spacing={6} align="stretch">
                    <Box>
                      <Text fontSize="lg" fontWeight="semibold" color="brand.900" mb={2}>
                        Pending Match Requests
                      </Text>
                      <Text fontSize="sm" color="gray.600">
                        Review and respond to incoming match requests. Reputation badges show each user's session history.
                      </Text>
                    </Box>
                    {renderMatches(pendingMatches)}
                  </VStack>
                </TabPanel>

                <TabPanel px={0}>
                  <VStack spacing={6} align="stretch">
                    <Box>
                      <Text fontSize="lg" fontWeight="semibold" color="brand.900" mb={2}>
                        Active Partnerships
                      </Text>
                      <Text fontSize="sm" color="gray.600">
                        Start conversations and plan practice sessions with your accepted matches.
                      </Text>
                    </Box>
                    {renderMatches(acceptedMatches)}
                  </VStack>
                </TabPanel>
              </TabPanels>
            </Tabs>
          )}

          {/* Call to Action */}
          {!isLoading && matches.length === 0 && (
            <Box textAlign="center" py={8}>
              <VStack spacing={4}>
                <Text fontSize="lg" color="gray.600">
                  No matches yet? Complete your profile to get started!
                </Text>
                <HStack spacing={4}>
                  <Button
                    colorScheme="brand"
                    bg="brand.900"
                    color="brand.50"
                    _hover={{ bg: "gray.600" }}
                    as={Link}
                    href="/profile-setup"
                  >
                    Complete Profile
                  </Button>
                  <Button
                    variant="outline"
                    borderColor="brand.400"
                    color="brand.900"
                    _hover={{ bg: "brand.100" }}
                    as={Link}
                    href="/confidence-test"
                  >
                    Take Assessment
                  </Button>
                </HStack>
              </VStack>
            </Box>
          )}
        </VStack>
      </Container>
    </Box>
  );
}