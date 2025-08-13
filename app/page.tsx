import Link from "next/link"
import { 
  Box, 
  Button, 
  Container, 
  Heading, 
  Text, 
  VStack,
  HStack,
  Card,
  CardBody
} from "@chakra-ui/react"
import { Target, Users, TrendingUp } from "lucide-react"

export default function HomePage() {
  return (
    <Box minH="100vh" bg="brand.50">
      <Container maxW="6xl" py={20}>
        <VStack spacing={12} textAlign="center">
          <VStack spacing={6}>
            <Heading 
              as="h1" 
              size="2xl" 
              fontFamily="heading" 
              color="brand.900"
            >
              Welcome to{" "}
              <Text as="span" color="brand.400">Wingman</Text>
            </Heading>
            <Text fontSize="xl" color="gray.600" maxW="2xl">
              Practice social confidence with accountability partners and 
              build real dating skills through guided challenges.
            </Text>
          </VStack>

          <HStack spacing={8} wrap="wrap" justify="center">
            <Card bg="white" border="1px solid" borderColor="gray.200">
              <CardBody p={8} textAlign="center">
                <Target size={48} color="var(--chakra-colors-brand-400)" style={{ margin: "0 auto 16px" }} />
                <Heading size="md" color="brand.900" mb={2}>
                  Discover Your Type
                </Heading>
                <Text color="gray.600" fontSize="sm">
                  Take our confidence assessment to understand your dating style
                </Text>
              </CardBody>
            </Card>

            <Card bg="white" border="1px solid" borderColor="gray.200">
              <CardBody p={8} textAlign="center">
                <Users size={48} color="var(--chakra-colors-brand-400)" style={{ margin: "0 auto 16px" }} />
                <Heading size="md" color="brand.900" mb={2}>
                  Get Matched
                </Heading>
                <Text color="gray.600" fontSize="sm">
                  Connect with accountability partners at your experience level
                </Text>
              </CardBody>
            </Card>

            <Card bg="white" border="1px solid" borderColor="gray.200">
              <CardBody p={8} textAlign="center">
                <TrendingUp size={48} color="var(--chakra-colors-brand-400)" style={{ margin: "0 auto 16px" }} />
                <Heading size="md" color="brand.900" mb={2}>
                  Build Confidence
                </Heading>
                <Text color="gray.600" fontSize="sm">
                  Practice real-world challenges and track your progress
                </Text>
              </CardBody>
            </Card>
          </HStack>

          <VStack spacing={4}>
            <Button 
              as={Link}
              href="/confidence-test"
              size="lg"
              colorScheme="brand"
              bg="brand.900"
              color="brand.50"
              _hover={{ bg: "gray.600" }}
              rounded="full"
              px={8}
              py={6}
              fontSize="base"
            >
              Take the Confidence Assessment
            </Button>
            <Text fontSize="sm" color="gray.600">
              Takes just 3 minutes • Get personalized results
            </Text>
          </VStack>
        </VStack>
      </Container>
    </Box>
  )
}