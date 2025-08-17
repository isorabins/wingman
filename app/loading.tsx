import { Box, Spinner, Text, VStack, Progress } from "@chakra-ui/react"

export default function Loading() {
  return (
    <Box 
      display="flex" 
      justifyContent="center" 
      alignItems="center" 
      height="100vh"
      backgroundColor="gray.50"
    >
      <VStack spacing={4}>
        <Spinner size="xl" color="blue.500" thickness="4px" />
        <Text fontSize="lg" color="gray.600">
          Loading Wingman...
        </Text>
        <Progress 
          size="lg" 
          isIndeterminate 
          colorScheme="blue" 
          width="200px"
          borderRadius="md"
        />
      </VStack>
    </Box>
  )
}