import {
  Card,
  CardBody,
  CardHeader,
  VStack,
  HStack,
  Text,
  Badge,
  Box,
  Flex,
  Spacer,
  Heading,
  Divider,
  Avatar,
  Icon
} from '@chakra-ui/react'
import { CalendarDays, MapPin, Target, Users } from 'lucide-react'
import { SessionData } from '@/lib/sessions/getSession'

interface SessionMetadataProps {
  sessionData: SessionData
}

export default function SessionMetadata({ sessionData }: SessionMetadataProps) {
  const formatScheduledTime = (isoString: string) => {
    const date = new Date(isoString)
    return {
      date: date.toLocaleDateString('en-US', {
        weekday: 'long',
        year: 'numeric', 
        month: 'long',
        day: 'numeric'
      }),
      time: date.toLocaleTimeString('en-US', {
        hour: 'numeric',
        minute: '2-digit',
        hour12: true
      })
    }
  }

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'scheduled': return 'blue'
      case 'in_progress': return 'yellow'
      case 'completed': return 'green'
      case 'cancelled': return 'red'
      default: return 'gray'
    }
  }

  const getDifficultyColor = (difficulty: string) => {
    switch (difficulty) {
      case 'beginner': return 'green'
      case 'intermediate': return 'orange'
      case 'advanced': return 'red'
      default: return 'gray'
    }
  }

  const { date, time } = formatScheduledTime(sessionData.scheduled_time)
  const isScheduledTimePassed = new Date(sessionData.scheduled_time) < new Date()

  return (
    <Card role="region" aria-labelledby="session-metadata">
      <CardHeader>
        <Flex align="center">
          <VStack align="start" spacing={1}>
            <Heading id="session-metadata" size="lg">
              Wingman Session
            </Heading>
            <Text color="gray.600">
              {sessionData.venue_name}
            </Text>
          </VStack>
          <Spacer />
          <Badge 
            colorScheme={getStatusColor(sessionData.status)} 
            variant="outline"
            fontSize="sm"
            px={3}
            py={1}
          >
            {sessionData.status.replace('_', ' ').toUpperCase()}
          </Badge>
        </Flex>
      </CardHeader>

      <CardBody pt={0}>
        <VStack spacing={6} align="stretch">
          {/* Session Details */}
          <VStack spacing={3} align="stretch">
            <HStack spacing={3}>
              <Icon as={CalendarDays} color="gray.500" />
              <VStack align="start" spacing={0}>
                <Text fontWeight="semibold">{date}</Text>
                <Text fontSize="sm" color="gray.600">{time}</Text>
                {isScheduledTimePassed && (
                  <Badge colorScheme="green" size="sm" mt={1}>
                    Time has passed
                  </Badge>
                )}
              </VStack>
            </HStack>

            <HStack spacing={3}>
              <Icon as={MapPin} color="gray.500" />
              <Text>{sessionData.venue_name}</Text>
            </HStack>

            <HStack spacing={3}>
              <Icon as={Users} color="gray.500" />
              <Text>
                {sessionData.participants.user1.name} & {sessionData.participants.user2.name}
              </Text>
            </HStack>
          </VStack>

          <Divider />

          {/* Challenges Section */}
          <VStack spacing={4} align="stretch">
            <HStack spacing={2}>
              <Icon as={Target} color="gray.500" />
              <Heading size="md">Challenges</Heading>
            </HStack>

            {/* User 1 Challenge */}
            <Card variant="outline">
              <CardBody>
                <HStack spacing={4} align="start">
                  <Avatar 
                    name={sessionData.participants.user1.name} 
                    size="md"
                  />
                  <VStack align="start" spacing={2} flex={1}>
                    <HStack>
                      <Text fontWeight="semibold">
                        {sessionData.participants.user1.name}
                      </Text>
                      {sessionData.participants.user1.confirmed && (
                        <Badge colorScheme="green" variant="solid">
                          Confirmed
                        </Badge>
                      )}
                    </HStack>
                    
                    <Box>
                      <HStack spacing={2} mb={1}>
                        <Text fontWeight="medium">
                          {sessionData.participants.user1.challenge.title}
                        </Text>
                        <Badge 
                          colorScheme={getDifficultyColor(sessionData.participants.user1.challenge.difficulty)}
                          size="sm"
                        >
                          {sessionData.participants.user1.challenge.difficulty}
                        </Badge>
                        <Badge variant="outline" size="sm">
                          {sessionData.participants.user1.challenge.points} pts
                        </Badge>
                      </HStack>
                      <Text fontSize="sm" color="gray.600">
                        {sessionData.participants.user1.challenge.description}
                      </Text>
                    </Box>
                  </VStack>
                </HStack>
              </CardBody>
            </Card>

            {/* User 2 Challenge */}
            <Card variant="outline">
              <CardBody>
                <HStack spacing={4} align="start">
                  <Avatar 
                    name={sessionData.participants.user2.name} 
                    size="md"
                  />
                  <VStack align="start" spacing={2} flex={1}>
                    <HStack>
                      <Text fontWeight="semibold">
                        {sessionData.participants.user2.name}
                      </Text>
                      {sessionData.participants.user2.confirmed && (
                        <Badge colorScheme="green" variant="solid">
                          Confirmed
                        </Badge>
                      )}
                    </HStack>
                    
                    <Box>
                      <HStack spacing={2} mb={1}>
                        <Text fontWeight="medium">
                          {sessionData.participants.user2.challenge.title}
                        </Text>
                        <Badge 
                          colorScheme={getDifficultyColor(sessionData.participants.user2.challenge.difficulty)}
                          size="sm"
                        >
                          {sessionData.participants.user2.challenge.difficulty}
                        </Badge>
                        <Badge variant="outline" size="sm">
                          {sessionData.participants.user2.challenge.points} pts
                        </Badge>
                      </HStack>
                      <Text fontSize="sm" color="gray.600">
                        {sessionData.participants.user2.challenge.description}
                      </Text>
                    </Box>
                  </VStack>
                </HStack>
              </CardBody>
            </Card>
          </VStack>

          {/* Session Notes */}
          {sessionData.notes && (
            <>
              <Divider />
              <VStack align="start" spacing={2}>
                <Text fontWeight="semibold">Session Notes</Text>
                <Box 
                  bg="gray.50" 
                  p={3} 
                  borderRadius="md" 
                  w="full"
                  borderLeft="4px solid"
                  borderLeftColor="blue.400"
                >
                  <Text fontSize="sm">{sessionData.notes}</Text>
                </Box>
              </VStack>
            </>
          )}
        </VStack>
      </CardBody>
    </Card>
  )
}