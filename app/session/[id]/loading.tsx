import { Container, VStack, Skeleton, Card, CardBody, CardHeader } from '@chakra-ui/react'

export default function SessionLoading() {
  return (
    <Container maxW="4xl" py={8}>
      <VStack spacing={6} align="stretch">
        {/* Session Header Skeleton */}
        <Card>
          <CardHeader>
            <Skeleton height="32px" width="60%" mb={2} />
            <Skeleton height="20px" width="40%" />
          </CardHeader>
        </Card>

        {/* Session Details Skeleton */}
        <Card>
          <CardBody>
            <VStack spacing={4} align="stretch">
              <Skeleton height="24px" width="80%" />
              <Skeleton height="20px" width="60%" />
              <Skeleton height="20px" width="70%" />
              
              {/* Challenge sections */}
              <VStack spacing={3} align="stretch" mt={6}>
                <Skeleton height="100px" />
                <Skeleton height="100px" />
              </VStack>
            </VStack>
          </CardBody>
        </Card>

        {/* Actions Skeleton */}
        <Card>
          <CardBody>
            <VStack spacing={4} align="stretch">
              <Skeleton height="40px" width="200px" />
              <Skeleton height="40px" width="200px" />
              <Skeleton height="80px" />
            </VStack>
          </CardBody>
        </Card>
      </VStack>
    </Container>
  )
}