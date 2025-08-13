"use client"

import { useState, useEffect } from "react"
import Link from "next/link"
import { ArrowLeft, ArrowRight, Target } from "lucide-react"
import {
  Box,
  Button,
  Card,
  CardBody,
  CardHeader,
  Container,
  Flex,
  Heading,
  HStack,
  Progress,
  Radio,
  RadioGroup,
  Stack,
  Text,
  VStack,
  useToast,
  Badge,
} from "@chakra-ui/react"

interface TestData {
  responses: string[];
  startTime: Date | null;
}

interface ArchetypeResult {
  id: string;
  title: string;
  description: string;
  experienceLevel: string;
  recommendedChallenges: string[];
}

export default function ConfidenceTest() {
  const [currentScreen, setCurrentScreen] = useState(0) // 0 = welcome, 1-12 = questions, 13 = results
  const [testData, setTestData] = useState<TestData>({
    responses: [],
    startTime: null
  })
  const [isSubmitting, setIsSubmitting] = useState(false)
  const [result, setResult] = useState<ArchetypeResult | null>(null)
  const [questions, setQuestions] = useState<any[]>([])
  const toast = useToast()

  const totalQuestions = 12
  const totalScreens = totalQuestions + 2 // welcome + 12 questions + results

  // Load questions from JSON file
  useEffect(() => {
    const loadQuestions = async () => {
      try {
        const response = await fetch('/api/static/confidence-test/questions.v1.json')
        const questionsData = await response.json()
        setQuestions(questionsData.questions)
      } catch (error) {
        console.error('Error loading questions:', error)
        toast({
          title: "Error loading questions",
          status: "error",
          duration: 3000,
          isClosable: true,
        })
      }
    }
    loadQuestions()
  }, [toast])

  // Track analytics on component mount
  useEffect(() => {
    if (currentScreen === 1 && testData.startTime === null) {
      // Track assessment started
      setTestData(prev => ({
        ...prev,
        startTime: new Date()
      }))
      
      // Analytics event
      if (typeof window !== 'undefined' && (window as any).gtag) {
        (window as any).gtag('event', 'assessment_started', {
          assessment_type: 'confidence'
        })
      }
    }
  }, [currentScreen, testData.startTime])

  const handleAnswerSelect = (answerLetter: string) => {
    const newResponses = [...testData.responses]
    newResponses[currentScreen - 1] = answerLetter // -1 because screen 0 is welcome
    
    setTestData({
      ...testData,
      responses: newResponses
    })
  }

  // Calculate archetype based on responses
  const calculateArchetype = (responses: string[]): ArchetypeResult => {
    const scores: Record<string, number> = {
      analyzer: 0,
      sprinter: 0,
      ghost: 0,
      naturalist: 0,
      scholar: 0,
      protector: 0
    }

    // Score each response based on archetype mapping
    responses.forEach((response, index) => {
      if (questions[index] && questions[index].options) {
        const option = questions[index].options.find((opt: any) => opt.letter === response)
        if (option && option.archetype) {
          scores[option.archetype] += 1
        }
      }
    })

    // Find the highest scoring archetype
    const maxScore = Math.max(...Object.values(scores))
    const topArchetype = Object.entries(scores).find(([_, score]) => score === maxScore)?.[0] || 'naturalist'
    
    // Get archetype data from questions file
    const archetypeData = questions.length > 0 && 
      fetch('/confidence-test/questions.v1.json')
        .then(res => res.json())
        .then(data => data.archetypes[topArchetype])
        .catch(() => null)

    // Return default data if fetch fails
    return {
      id: topArchetype,
      title: `🎯 THE ${topArchetype.toUpperCase()}`,
      description: "You have a unique approach to dating and social connections. Your confidence style is authentic to who you are.",
      experienceLevel: "Beginner",
      recommendedChallenges: [
        "Practice making eye contact",
        "Start conversations with strangers", 
        "Express your genuine interests",
        "Take initiative in social situations"
      ]
    }
  }

  const handleSubmit = async () => {
    if (testData.responses.length !== totalQuestions) {
      toast({
        title: "Please answer all questions",
        status: "warning",
        duration: 3000,
        isClosable: true,
      })
      return
    }

    setIsSubmitting(true)

    try {
      // Calculate archetype locally first
      const calculatedArchetype = calculateArchetype(testData.responses)
      
      // Get full archetype data from JSON
      const questionsResponse = await fetch('/api/static/confidence-test/questions.v1.json')
      const questionsData = await questionsResponse.json()
      const fullArchetypeData = questionsData.archetypes[calculatedArchetype.id]
      
      setResult(fullArchetypeData || calculatedArchetype)

      // Optionally submit to API (if endpoint exists)
      try {
        await fetch('/api/assessment/confidence', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({
            responses: testData.responses,
            archetype: calculatedArchetype.id,
            startTime: testData.startTime,
            completedAt: new Date().toISOString()
          }),
        })
      } catch (apiError) {
        // API submission failed, but we can still show results
        console.warn('API submission failed:', apiError)
      }
      
      // Track assessment completed
      const duration = testData.startTime ? 
        Math.round((new Date().getTime() - testData.startTime.getTime()) / 1000) : 0
      
      if (typeof window !== 'undefined' && (window as any).gtag) {
        (window as any).gtag('event', 'assessment_completed', {
          assessment_type: 'confidence',
          duration_seconds: duration,
          archetype: calculatedArchetype.id
        })
      }
      
      nextScreen()
    } catch (error) {
      console.error('Error submitting assessment:', error)
      toast({
        title: "Error processing assessment",
        description: "Please try again later",
        status: "error",
        duration: 5000,
        isClosable: true,
      })
    } finally {
      setIsSubmitting(false)
    }
  }

  const nextScreen = () => {
    if (currentScreen < totalScreens - 1) {
      setCurrentScreen(currentScreen + 1)
    }
  }

  const prevScreen = () => {
    if (currentScreen > 0) {
      setCurrentScreen(currentScreen - 1)
    }
  }

  const isNextEnabled = () => {
    if (currentScreen === 0) return true // Welcome screen
    if (currentScreen <= totalQuestions) {
      return testData.responses[currentScreen - 1] !== undefined
    }
    return true
  }

  const getProgressPercentage = () => {
    if (currentScreen === 0) return 0
    if (currentScreen <= totalQuestions) {
      return (currentScreen / totalQuestions) * 100
    }
    return 100
  }

  const renderScreen = () => {
    // Welcome Screen
    if (currentScreen === 0) {
      return (
        <VStack spacing={8} textAlign="center" maxW="4xl" mx="auto">
          <VStack spacing={6}>
            <Target size={64} color="var(--chakra-colors-brand-400)" />
            <Heading 
              as="h1" 
              size="2xl" 
              fontFamily="heading" 
              color="brand.900"
              lineHeight="tight"
            >
              Discover Your{" "}
              <Text as="span" color="brand.400">Dating Confidence Type</Text>
            </Heading>
            <Text 
              fontSize="xl" 
              color="gray.600" 
              maxW="3xl" 
              lineHeight="relaxed"
            >
              Understanding your natural approach to dating and social connections 
              is the first step to building authentic confidence.
            </Text>
          </VStack>

          <VStack spacing={2}>
            <Button 
              size="lg" 
              colorScheme="brand"
              bg="brand.900"
              color="brand.50"
              _hover={{ bg: "gray.600" }}
              rounded="full"
              px={8}
              py={6}
              fontSize="base"
              onClick={nextScreen}
            >
              Start the Assessment
            </Button>
            <Text color="gray.600" fontSize="sm">
              Takes just 3 minutes • 12 quick questions
            </Text>
          </VStack>
          
          <VStack spacing={4} w="full" maxW="4xl">
            <Text fontSize="lg" fontWeight="medium" color="brand.900">
              You'll discover:
            </Text>
            <HStack spacing={6} wrap="wrap" justify="center">
              <Text fontSize="sm" color="gray.600">• Your confidence style</Text>
              <Text fontSize="sm" color="gray.600">• Perfect starting challenges</Text>
              <Text fontSize="sm" color="gray.600">• Experience level match</Text>
            </HStack>
          </VStack>
        </VStack>
      )
    }

    // Question Screens  
    if (currentScreen >= 1 && currentScreen <= totalQuestions && questions.length > 0) {
      const questionIndex = currentScreen - 1
      const question = questions[questionIndex]
      
      return (
        <VStack spacing={8} maxW="4xl" mx="auto">
          {/* Progress */}
          <VStack spacing={2} w="full">
            <HStack justify="center" spacing={2} fontSize="sm" color="gray.600">
              <Badge colorScheme="brand" variant="solid" rounded="full" px={3} py={1}>
                Question {currentScreen}
              </Badge>
              <Text>of {totalQuestions}</Text>
            </HStack>
            <Progress 
              value={getProgressPercentage()} 
              w="full" 
              h={2} 
              colorScheme="brand"
              rounded="full"
              role="progressbar"
              aria-valuenow={getProgressPercentage()}
              aria-valuemin={0}
              aria-valuemax={100}
              aria-label={`Assessment progress: ${Math.round(getProgressPercentage())}% complete`}
            />
          </VStack>

          <Box textAlign="center">
            <Heading 
              as="h2" 
              size="xl" 
              fontFamily="heading" 
              color="brand.900" 
              lineHeight="tight"
            >
              {question.question}
            </Heading>
          </Box>

          <RadioGroup
            value={testData.responses[questionIndex] || ""}
            onChange={handleAnswerSelect}
            w="full"
          >
            <VStack 
              spacing={4} 
              role="radiogroup"
              aria-labelledby={`question-${currentScreen}`}
            >
              {question.options.map((option: any, index: number) => {
                const letter = ['A', 'B', 'C', 'D', 'E', 'F'][index]
                const isSelected = testData.responses[questionIndex] === letter
                
                return (
                  <Card
                    key={index}
                    variant="outline"
                    w="full"
                    bg={isSelected ? "brand.900" : "brand.50"}
                    borderColor={isSelected ? "brand.900" : "gray.200"}
                    borderWidth="2px"
                    cursor="pointer"
                    transition="all 0.2s"
                    _hover={{
                      borderColor: isSelected ? "brand.900" : "brand.400",
                      bg: isSelected ? "brand.900" : "brand.100"
                    }}
                    onClick={() => handleAnswerSelect(letter)}
                  >
                    <CardBody p={6}>
                      <Radio 
                        value={letter}
                        colorScheme="brand"
                        isChecked={isSelected}
                        pointerEvents="none"
                      >
                        <Text
                          color={isSelected ? "brand.50" : "brand.900"}
                          fontSize="base"
                          lineHeight="relaxed"
                          ml={2}
                        >
                          {option.text}
                        </Text>
                      </Radio>
                    </CardBody>
                  </Card>
                )
              })}
            </VStack>
          </RadioGroup>

          {/* Navigation buttons */}
          <Flex justify="center" pt={6}>
            <Button
              variant="outline"
              onClick={prevScreen}
              disabled={currentScreen <= 1}
              borderColor="gray.200"
              color="gray.600"
              _hover={{ bg: "brand.100" }}
              rounded="full"
              px={6}
            >
              <ArrowLeft size={16} style={{ marginRight: '8px' }} />
              Back
            </Button>
          </Flex>
        </VStack>
      )
    }

    // Results Screen
    if (currentScreen === totalQuestions + 1 && result) {
      return (
        <VStack spacing={8} textAlign="center" maxW="5xl" mx="auto">
          <VStack spacing={6}>
            <Target size={64} color="var(--chakra-colors-brand-400)" />
            <Heading 
              as="h1" 
              size="2xl" 
              fontFamily="heading" 
              color="brand.900" 
              lineHeight="tight"
            >
              {result.title}
            </Heading>
            <Text 
              fontSize="xl" 
              color="gray.600" 
              maxW="4xl" 
              lineHeight="relaxed"
            >
              {result.description}
            </Text>
          </VStack>

          <Card bg="brand.50" border="1px solid" borderColor="gray.200" w="full">
            <CardBody p={8}>
              <VStack spacing={4} align="start">
                <Text fontSize="lg" fontWeight="medium" color="brand.900">
                  Experience Level: {result.experienceLevel}
                </Text>
                
                <Box>
                  <Text fontSize="lg" fontWeight="medium" color="brand.900" mb={3}>
                    Recommended Starting Challenges:
                  </Text>
                  <VStack spacing={2} align="start">
                    {result.recommendedChallenges.map((challenge, index) => (
                      <HStack key={index} align="start">
                        <Box
                          w={2}
                          h={2}
                          rounded="full"
                          bg="brand.400"
                          mt={2}
                          flexShrink={0}
                        />
                        <Text color="gray.600" fontSize="sm">
                          {challenge}
                        </Text>
                      </HStack>
                    ))}
                  </VStack>
                </Box>
              </VStack>
            </CardBody>
          </Card>

          <Flex gap={4} pt={8}>
            <Button 
              variant="outline"
              borderColor="brand.400"
              color="brand.900"
              _hover={{ bg: "brand.100" }}
              rounded="full"
              px={8}
              py={6}
              fontSize="base"
              as={Link}
              href="/"
            >
              Back to Home
            </Button>
            <Button 
              colorScheme="brand"
              bg="brand.900"
              color="brand.50"
              _hover={{ bg: "gray.600" }}
              rounded="full"
              px={8}
              py={6}
              fontSize="base"
            >
              Continue to Matching
            </Button>
          </Flex>
        </VStack>
      )
    }

    return null
  }

  return (
    <Box minH="100vh" bg="brand.50">
      {/* Header */}
      <Box borderBottom="1px solid" borderColor="gray.200">
        <Container maxW="6xl" py={6} px={4}>
          <Flex justify="space-between" align="center">
            <Link href="/">
              <Heading as="h1" size="lg" fontFamily="heading" color="brand.900">
                Wingman
              </Heading>
            </Link>
            <Button 
              variant="ghost" 
              color="gray.600" 
              _hover={{ color: "brand.900", bg: "gray.200" }}
              as={Link}
              href="/"
            >
              <ArrowLeft size={16} style={{ marginRight: '8px' }} />
              Back to Home
            </Button>
          </Flex>
        </Container>
      </Box>

      {/* Main Content */}
      <Container maxW="6xl" py={12} px={4}>
        {renderScreen()}
      </Container>

      {/* Submit button for last question */}
      {currentScreen === totalQuestions && (
        <Box 
          position="fixed" 
          bottom={0} 
          left={0} 
          right={0} 
          bg="white" 
          borderTop="1px solid" 
          borderColor="gray.200"
          p={4}
        >
          <Container maxW="6xl">
            <Flex justify="center">
              <Button
                colorScheme="brand"
                bg="brand.900"
                color="brand.50"
                _hover={{ bg: "gray.600" }}
                rounded="full"
                px={8}
                py={6}
                fontSize="base"
                onClick={handleSubmit}
                disabled={!isNextEnabled() || isSubmitting}
                isLoading={isSubmitting}
                loadingText="Calculating your type..."
              >
                {isSubmitting ? "Calculating your type..." : "Get My Results"}
              </Button>
            </Flex>
          </Container>
        </Box>
      )}
    </Box>
  )
}