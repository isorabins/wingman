/**
 * Session Page Loading Skeleton
 * Matches the actual session page layout for smooth transitions
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

export const SessionSkeleton: React.FC = () => {
  return (
    <Container maxW="4xl" py={8}>
      <VStack spacing={6} align="stretch">
        {/* Session Header Card */}
        <Card>
          <CardHeader>
            <Flex justify="space-between" align="center">
              <VStack align="start" spacing={2}>
                <Skeleton height="28px" width="200px" />
                <Skeleton height="16px" width="160px" />
              </VStack>
              <Skeleton>
                <Badge>Loading...</Badge>
              </Skeleton>
            </Flex>
          </CardHeader>
        </Card>

        {/* Session Participants */}
        <Card>
          <CardHeader>
            <Skeleton height="24px" width="140px" />
          </CardHeader>
          <CardBody pt={0}>
            <VStack spacing={4}>
              {[1, 2].map((index) => (
                <HStack key={index} spacing={4} width="full">
                  <Skeleton boxSize="50px" borderRadius="full" />
                  <VStack align="start" spacing={1} flex={1}>
                    <Skeleton height="18px" width="120px" />
                    <Skeleton height="14px" width="80px" />
                  </VStack>
                  <Skeleton height="32px" width="100px" borderRadius="md" />
                </HStack>
              ))}
            </VStack>
          </CardBody>
        </Card>

        {/* Session Details */}
        <Card>
          <CardHeader>
            <Skeleton height="24px" width="160px" />
          </CardHeader>
          <CardBody pt={0}>
            <VStack spacing={4} align="stretch">
              <HStack justify="space-between">
                <Skeleton height="16px" width="60px" />
                <Skeleton height="16px" width="140px" />
              </HStack>
              <HStack justify="space-between">
                <Skeleton height="16px" width="80px" />
                <Skeleton height="16px" width="180px" />
              </HStack>
              <HStack justify="space-between">
                <Skeleton height="16px" width="70px" />
                <Skeleton height="16px" width="100px" />
              </HStack>
              <Divider />
              <Box>
                <Skeleton height="18px" width="100px" mb={2} />
                <SkeletonText noOfLines={2} spacing={2} />
              </Box>
            </VStack>
          </CardBody>
        </Card>

        {/* Challenges */}
        <Card>
          <CardHeader>
            <Skeleton height="24px" width="120px" />
          </CardHeader>
          <CardBody pt={0}>
            <VStack spacing={3}>
              {[1, 2, 3].map((index) => (
                <Box key={index} p={4} borderWidth="1px" borderRadius="md" width="full">
                  <HStack justify="space-between" mb={2}>
                    <Skeleton height="18px" width="200px" />
                    <Skeleton height="20px" width="60px" borderRadius="full" />
                  </HStack>
                  <SkeletonText noOfLines={2} spacing={1} />
                </Box>
              ))}
            </VStack>
          </CardBody>
        </Card>

        {/* Action Buttons */}
        <Card>
          <CardBody>
            <HStack spacing={4} justify="center">
              <Skeleton height="40px" width="140px" borderRadius="md" />
              <Skeleton height="40px" width="120px" borderRadius="md" />
            </HStack>
          </CardBody>
        </Card>
      </VStack>
    </Container>
  );
};

export default SessionSkeleton;