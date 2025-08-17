/**
 * Chat Interface Loading Skeleton
 * Matches buddy chat layout with messages and venue suggestions
 */

import React from 'react';
import {
  Box,
  Card,
  CardBody,
  CardHeader,
  Container,
  Flex,
  Skeleton,
  SkeletonText,
  VStack,
  HStack,
  Badge,
  Divider,
} from '@chakra-ui/react';

export const ChatSkeleton: React.FC = () => {
  return (
    <Container maxW="4xl" py={8}>
      <VStack spacing={6} align="stretch">
        {/* Chat Header */}
        <Card>
          <CardHeader>
            <Flex align="center">
              <VStack align="start" spacing={1}>
                <Skeleton height="24px" width="120px" />
                <Skeleton height="14px" width="180px" />
              </VStack>
              <Box ml="auto">
                <Skeleton>
                  <Badge>Active</Badge>
                </Skeleton>
              </Box>
            </Flex>
          </CardHeader>
        </Card>

        {/* Main Chat Area */}
        <Card flex={1}>
          <CardBody p={0}>
            <Flex direction="column" h="500px">
              {/* Messages Area */}
              <Box flex={1} overflowY="hidden" p={4}>
                <VStack spacing={3} align="stretch">
                  {/* Message bubbles */}
                  {[1, 2, 3, 4, 5].map((msg) => (
                    <Flex
                      key={msg}
                      justify={msg % 2 === 0 ? "flex-end" : "flex-start"}
                    >
                      <Box
                        maxW="70%"
                        p={3}
                        borderRadius="lg"
                        bg={msg % 2 === 0 ? "blue.100" : "gray.100"}
                      >
                        <SkeletonText 
                          noOfLines={Math.ceil(Math.random() * 3)} 
                          spacing={1} 
                        />
                        <Skeleton height="10px" width="40px" mt={2} />
                      </Box>
                    </Flex>
                  ))}
                </VStack>
              </Box>

              {/* Message Input */}
              <Box p={4} borderTop="1px" borderColor="gray.200">
                <HStack spacing={2}>
                  <Skeleton height="40px" flex={1} borderRadius="md" />
                  <Skeleton boxSize="40px" borderRadius="md" />
                </HStack>
                <Skeleton height="12px" width="120px" mt={1} />
              </Box>
            </Flex>
          </CardBody>
        </Card>

        {/* Venue Suggestions Panel */}
        <Card>
          <CardHeader>
            <Skeleton height="20px" width="140px" />
          </CardHeader>
          <CardBody pt={0}>
            <VStack spacing={4} align="stretch">
              {[1, 2, 3, 4].map((venue) => (
                <Box key={venue}>
                  <HStack spacing={3} mb={2}>
                    <Skeleton boxSize="20px" />
                    <VStack align="start" spacing={0}>
                      <Skeleton height="16px" width="100px" />
                      <Skeleton height="12px" width="160px" />
                    </VStack>
                  </HStack>
                  <VStack align="start" spacing={1} pl={8}>
                    {[1, 2, 3].map((example) => (
                      <Skeleton 
                        key={example} 
                        height="12px" 
                        width={`${80 + example * 15}px`} 
                      />
                    ))}
                  </VStack>
                  <Divider mt={3} />
                </Box>
              ))}
              
              {/* Tip Box */}
              <Box bg="blue.50" p={3} borderRadius="md">
                <HStack spacing={2}>
                  <Skeleton boxSize="16px" />
                  <Skeleton height="14px" width="200px" />
                </HStack>
              </Box>
            </VStack>
          </CardBody>
        </Card>
      </VStack>
    </Container>
  );
};

export default ChatSkeleton;