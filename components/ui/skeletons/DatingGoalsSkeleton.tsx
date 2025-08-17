/**
 * Dating Goals Page Loading Skeleton
 * Matches the AI conversation interface layout
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
  Avatar,
  Divider,
} from '@chakra-ui/react';

export const DatingGoalsSkeleton: React.FC = () => {
  return (
    <Container maxW="4xl" py={8}>
      <VStack spacing={6} align="stretch">
        {/* Header */}
        <Card>
          <CardHeader>
            <VStack spacing={3} textAlign="center">
              <Skeleton height="36px" width="300px" />
              <SkeletonText noOfLines={2} spacing={2} textAlign="center" />
            </VStack>
          </CardHeader>
        </Card>

        {/* Progress Indicator */}
        <Card>
          <CardBody>
            <VStack spacing={4}>
              <HStack spacing={4} width="full" justify="center">
                {[1, 2, 3, 4].map((step) => (
                  <React.Fragment key={step}>
                    <VStack spacing={2}>
                      <Skeleton boxSize="40px" borderRadius="full" />
                      <Skeleton height="12px" width="60px" />
                    </VStack>
                    {step < 4 && <Skeleton height="2px" width="40px" />}
                  </React.Fragment>
                ))}
              </HStack>
              <Skeleton height="4px" width="full" borderRadius="full" />
            </VStack>
          </CardBody>
        </Card>

        {/* Chat Interface */}
        <Card flex={1} minH="400px">
          <CardBody>
            <VStack spacing={4} align="stretch" height="400px">
              {/* Chat Messages */}
              <Box flex={1} overflowY="hidden">
                <VStack spacing={4} align="stretch">
                  {/* AI Message */}
                  <HStack align="start" spacing={3}>
                    <Avatar size="sm">
                      <Skeleton boxSize="32px" borderRadius="full" />
                    </Avatar>
                    <Box flex={1}>
                      <Card variant="outline" bg="gray.50">
                        <CardBody p={4}>
                          <SkeletonText noOfLines={3} spacing={2} />
                        </CardBody>
                      </Card>
                    </Box>
                  </HStack>

                  {/* User Message */}
                  <HStack align="start" spacing={3} justify="flex-end">
                    <Box flex={1} maxW="80%">
                      <Card variant="outline" bg="blue.50">
                        <CardBody p={4}>
                          <SkeletonText noOfLines={2} spacing={2} />
                        </CardBody>
                      </Card>
                    </Box>
                    <Avatar size="sm">
                      <Skeleton boxSize="32px" borderRadius="full" />
                    </Avatar>
                  </HStack>

                  {/* AI Response */}
                  <HStack align="start" spacing={3}>
                    <Avatar size="sm">
                      <Skeleton boxSize="32px" borderRadius="full" />
                    </Avatar>
                    <Box flex={1}>
                      <Card variant="outline" bg="gray.50">
                        <CardBody p={4}>
                          <SkeletonText noOfLines={4} spacing={2} />
                        </CardBody>
                      </Card>
                    </Box>
                  </HStack>
                </VStack>
              </Box>

              <Divider />

              {/* Input Area */}
              <HStack spacing={3}>
                <Skeleton height="48px" flex={1} borderRadius="md" />
                <Skeleton boxSize="48px" borderRadius="md" />
              </HStack>

              {/* Action Buttons */}
              <HStack spacing={3} justify="center">
                <Skeleton height="36px" width="100px" borderRadius="md" />
                <Skeleton height="36px" width="120px" borderRadius="md" />
              </HStack>
            </VStack>
          </CardBody>
        </Card>

        {/* Tips/Help Section */}
        <Card>
          <CardHeader>
            <Skeleton height="20px" width="80px" />
          </CardHeader>
          <CardBody pt={0}>
            <VStack spacing={2} align="start">
              {[1, 2, 3].map((tip) => (
                <HStack key={tip} spacing={3}>
                  <Skeleton boxSize="6px" borderRadius="full" />
                  <Skeleton height="16px" width={`${120 + tip * 20}px`} />
                </HStack>
              ))}
            </VStack>
          </CardBody>
        </Card>
      </VStack>
    </Container>
  );
};

export default DatingGoalsSkeleton;