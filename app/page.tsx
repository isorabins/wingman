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
  CardBody,
  SimpleGrid,
  Badge
} from "@chakra-ui/react"
import { Target, Users, TrendingUp, User, MapPin, MessageSquare } from "lucide-react"

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

          <SimpleGrid columns={{ base: 1, md: 2, lg: 3 }} spacing={6} w="full" maxW="6xl">
            <Card bg="white" border="1px solid" borderColor="gray.200">
              <CardBody p={8} textAlign="center">
                <Target size={48} color="var(--chakra-colors-brand-400)" style={{ margin: "0 auto 16px" }} />
                <Heading size="md" color="brand.900" mb={2}>
                  Discover Your Type
                </Heading>
                <Text color="gray.600" fontSize="sm" mb={4}>
                  Take our confidence assessment to understand your dating style
                </Text>
                <Badge colorScheme="green" variant="solid">Available</Badge>
              </CardBody>
            </Card>

            <Card bg="white" border="1px solid" borderColor="gray.200">
              <CardBody p={8} textAlign="center">
                <User size={48} color="var(--chakra-colors-brand-400)" style={{ margin: "0 auto 16px" }} />
                <Heading size="md" color="brand.900" mb={2}>
                  Complete Profile
                </Heading>
                <Text color="gray.600" fontSize="sm" mb={4}>
                  Set up your profile with photos and preferences
                </Text>
                <Badge colorScheme="green" variant="solid">Available</Badge>
              </CardBody>
            </Card>

            <Card bg="white" border="1px solid" borderColor="gray.200">
              <CardBody p={8} textAlign="center">
                <Users size={48} color="var(--chakra-colors-brand-400)" style={{ margin: "0 auto 16px" }} />
                <Heading size="md" color="brand.900" mb={2}>
                  Find Your Buddy
                </Heading>
                <Text color="gray.600" fontSize="sm" mb={4}>
                  Connect with accountability partners at your experience level
                </Text>
                <Badge colorScheme="yellow" variant="solid">Coming Soon</Badge>
              </CardBody>
            </Card>

            <Card bg="white" border="1px solid" borderColor="gray.200">
              <CardBody p={8} textAlign="center">
                <MapPin size={48} color="var(--chakra-colors-brand-400)" style={{ margin: "0 auto 16px" }} />
                <Heading size="md" color="brand.900" mb={2}>
                  Location Services
                </Heading>
                <Text color="gray.600" fontSize="sm" mb={4}>
                  Enhanced geolocation with privacy controls
                </Text>
                <Badge colorScheme="green" variant="solid">Available</Badge>
              </CardBody>
            </Card>

            <Card bg="white" border="1px solid" borderColor="gray.200">
              <CardBody p={8} textAlign="center">
                <TrendingUp size={48} color="var(--chakra-colors-brand-400)" style={{ margin: "0 auto 16px" }} />
                <Heading size="md" color="brand.900" mb={2}>
                  Build Confidence
                </Heading>
                <Text color="gray.600" fontSize="sm" mb={4}>
                  Practice real-world challenges and track your progress
                </Text>
                <Badge colorScheme="yellow" variant="solid">Coming Soon</Badge>
              </CardBody>
            </Card>

            <Card bg="white" border="1px solid" borderColor="gray.200">
              <CardBody p={8} textAlign="center">
                <MessageSquare size={48} color="var(--chakra-colors-brand-400)" style={{ margin: "0 auto 16px" }} />
                <Heading size="md" color="brand.900" mb={2}>
                  Email Testing
                </Heading>
                <Text color="gray.600" fontSize="sm" mb={4}>
                  Test email notifications and communication features
                </Text>
                <Badge colorScheme="green" variant="solid">Available</Badge>
              </CardBody>
            </Card>
          </SimpleGrid>

          <VStack spacing={6}>
            <Text fontSize="lg" fontWeight="medium" color="brand.900">
              Ready to get started?
            </Text>
            
            <HStack spacing={4} wrap="wrap" justify="center">
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
                Take the Assessment
              </Button>
              
              <Button 
                as={Link}
                href="/profile-setup?test=true"
                size="lg"
                variant="outline"
                borderColor="brand.400"
                color="brand.900"
                _hover={{ bg: "brand.100" }}
                rounded="full"
                px={8}
                py={6}
                fontSize="base"
              >
                Test Profile Setup
              </Button>
              
              <Button 
                as={Link}
                href="/email-test"
                size="lg"
                variant="outline"
                borderColor="brand.400"
                color="brand.900"
                _hover={{ bg: "brand.100" }}
                rounded="full"
                px={8}
                py={6}
                fontSize="base"
              >
                Test Email
              </Button>
            </HStack>
            
            <Text fontSize="sm" color="gray.600" textAlign="center" maxW="2xl">
              <strong>Assessment:</strong> Takes 3 minutes • Get personalized results<br/>
              <strong>Profile Setup:</strong> Test photo uploads and location services<br/>
              <strong>Email Test:</strong> Send test emails to verify functionality
            </Text>
          </VStack>
        </VStack>
      </Container>
    </Box>
  )
}