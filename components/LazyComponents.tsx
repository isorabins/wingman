"use client"

import dynamic from "next/dynamic"
import { 
  Box, 
  Skeleton, 
  SkeletonText, 
  VStack, 
  HStack,
  Badge,
  Text,
  Spinner
} from "@chakra-ui/react"

// Loading skeletons for different component types
export const ChatSkeleton = () => (
  <VStack spacing={4} align="stretch" p={4}>
    <HStack>
      <Skeleton height="40px" width="40px" borderRadius="full" />
      <VStack align="start" flex={1}>
        <Skeleton height="16px" width="100px" />
        <SkeletonText noOfLines={2} spacing="2" />
      </VStack>
    </HStack>
    <HStack>
      <Skeleton height="40px" width="40px" borderRadius="full" />
      <VStack align="start" flex={1}>
        <Skeleton height="16px" width="80px" />
        <SkeletonText noOfLines={3} spacing="2" />
      </VStack>
    </HStack>
    <HStack>
      <Skeleton height="40px" width="40px" borderRadius="full" />
      <VStack align="start" flex={1}>
        <Skeleton height="16px" width="120px" />
        <SkeletonText noOfLines={1} spacing="2" />
      </VStack>
    </HStack>
  </VStack>
)

export const LocationSkeleton = () => (
  <VStack spacing={4} p={4}>
    <Text fontSize="sm" color="gray.500">Loading location services...</Text>
    <Skeleton height="200px" width="100%" borderRadius="md" />
    <HStack width="100%">
      <Skeleton height="40px" flex={1} borderRadius="md" />
      <Skeleton height="40px" width="100px" borderRadius="md" />
    </HStack>
  </VStack>
)

export const PhotoUploadSkeleton = () => (
  <VStack spacing={4} p={4}>
    <Text fontSize="sm" color="gray.500">Preparing photo upload...</Text>
    <Skeleton height="150px" width="150px" borderRadius="lg" />
    <Skeleton height="40px" width="200px" borderRadius="md" />
  </VStack>
)

export const ReputationSkeleton = () => (
  <HStack spacing={2}>
    <Spinner size="sm" />
    <Badge variant="outline">Loading...</Badge>
  </HStack>
)

// Lazy-loaded components with optimized loading states
export const LazyLocationCapture = dynamic(() => import('./LocationCapture'), {
  loading: () => <LocationSkeleton />,
  ssr: false
})

export const LazyDatingGoalsChat = dynamic(() => import('./DatingGoalsChat'), {
  loading: () => <ChatSkeleton />,
  ssr: false
})

export const LazyReputationBadge = dynamic(() => import('./ReputationBadge'), {
  loading: () => <ReputationSkeleton />,
  ssr: false
})

export const LazyMatchCard = dynamic(() => import('./MatchCard'), {
  loading: () => (
    <Box borderWidth="1px" borderRadius="lg" p={4}>
      <VStack spacing={3}>
        <Skeleton height="80px" width="80px" borderRadius="full" />
        <SkeletonText noOfLines={3} spacing="2" />
        <Skeleton height="40px" width="100%" borderRadius="md" />
      </VStack>
    </Box>
  ),
  ssr: false
})

// Heavy feature components
export const LazyPhotoUpload = dynamic(() => import('../storage/photo_upload'), {
  loading: () => <PhotoUploadSkeleton />,
  ssr: false
})

export const LazyTestModeIndicator = dynamic(() => import('./TestModeIndicator'), {
  loading: () => null, // No loading state needed for this component
  ssr: false
})

// =================== PERFORMANCE OPTIMIZED COMPONENTS ===================

// Heavy page components - these are the largest bundle contributors
export const LazyConfidenceTest = dynamic(() => import('../app/confidence-test/page'), {
  loading: () => (
    <VStack spacing={6} p={8}>
      <Skeleton height="60px" width="300px" />
      <Skeleton height="20px" width="full" />
      <VStack spacing={4} width="full">
        {[1, 2, 3, 4].map(i => (
          <Skeleton key={i} height="80px" width="full" borderRadius="md" />
        ))}
      </VStack>
    </VStack>
  ),
  ssr: false // Assessment is interactive, no SSR benefit
})

export const LazyBuddyChat = dynamic(() => import('../app/buddy-chat/[matchId]/page'), {
  loading: () => <ChatSkeleton />,
  ssr: false // Real-time chat requires client-side rendering
})

export const LazySessionPage = dynamic(() => import('../app/session/[id]/page'), {
  loading: () => (
    <VStack spacing={6} p={8}>
      <Skeleton height="80px" width="full" />
      <Skeleton height="200px" width="full" />
      <Skeleton height="150px" width="full" />
      <Skeleton height="100px" width="full" />
    </VStack>
  ),
  ssr: true // Session data can benefit from SSR
})

// Third-party heavy libraries - split these to reduce initial bundle
export const LazyReactDropzone = dynamic(() => import('react-dropzone'), {
  loading: () => <PhotoUploadSkeleton />,
  ssr: false
})

export const LazyReactHookForm = dynamic(() => import('react-hook-form'), {
  loading: () => <Skeleton height="40px" width="full" />,
  ssr: false
})

// Performance monitoring (non-critical)
export const LazyPerformanceTracker = dynamic(() => import('./PerformanceTracker'), {
  loading: () => null, // Silent loading for performance monitoring
  ssr: false
})

// Progress tracking components
export const LazyProgressiveLoader = dynamic(() => import('./ProgressiveLoader'), {
  loading: () => <Spinner size="sm" />,
  ssr: false
})

// Complex UI components that can be deferred
export const LazyTopicProgress = dynamic(() => import('./TopicProgress'), {
  loading: () => (
    <HStack spacing={4} width="full">
      {[1, 2, 3, 4].map(i => (
        <VStack key={i} spacing={2}>
          <Skeleton boxSize="40px" borderRadius="full" />
          <Skeleton height="12px" width="60px" />
        </VStack>
      ))}
    </HStack>
  ),
  ssr: false
})

export const LazyGoalsCompletion = dynamic(() => import('./GoalsCompletion'), {
  loading: () => (
    <VStack spacing={4} p={6}>
      <Skeleton height="40px" width="200px" />
      <SkeletonText noOfLines={3} spacing={2} />
      <Skeleton height="40px" width="150px" />
    </VStack>
  ),
  ssr: false
})

// =================== UTILITY EXPORTS ===================

// Group related components for easier imports
export const HeavyPageComponents = {
  ConfidenceTest: LazyConfidenceTest,
  BuddyChat: LazyBuddyChat,
  SessionPage: LazySessionPage,
} as const

export const FormComponents = {
  PhotoUpload: LazyPhotoUpload,
  LocationCapture: LazyLocationCapture,
  ReactDropzone: LazyReactDropzone,
  ReactHookForm: LazyReactHookForm,
} as const

export const UIComponents = {
  ReputationBadge: LazyReputationBadge,
  MatchCard: LazyMatchCard,
  TopicProgress: LazyTopicProgress,
  GoalsCompletion: LazyGoalsCompletion,
} as const

export const UtilityComponents = {
  PerformanceTracker: LazyPerformanceTracker,
  ProgressiveLoader: LazyProgressiveLoader,
  TestModeIndicator: LazyTestModeIndicator,
} as const