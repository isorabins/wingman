/**
 * Progressive Loading Component
 * Phase 5: Service worker integration and skeleton loading states
 */

"use client"

import { useEffect, useState, ReactNode } from 'react'
import { Box, VStack, HStack, Skeleton, SkeletonText, Text, Progress } from '@chakra-ui/react'

interface ProgressiveLoaderProps {
  children: ReactNode
  loadingStages?: LoadingStage[]
  showProgress?: boolean
  minLoadTime?: number
  className?: string
}

interface LoadingStage {
  name: string
  duration: number
  skeleton: ReactNode
  description?: string
}

// Default loading stages for WingmanMatch features
const DEFAULT_STAGES: LoadingStage[] = [
  {
    name: 'initializing',
    duration: 500,
    description: 'Initializing application...',
    skeleton: <Skeleton height="100px" />
  },
  {
    name: 'authentication',
    duration: 800,
    description: 'Checking authentication...',
    skeleton: (
      <VStack spacing={3}>
        <Skeleton height="60px" width="200px" />
        <SkeletonText noOfLines={2} spacing="2" />
      </VStack>
    )
  },
  {
    name: 'data-loading',
    duration: 1200,
    description: 'Loading your data...',
    skeleton: (
      <VStack spacing={4}>
        <HStack width="100%">
          <Skeleton height="50px" width="50px" borderRadius="full" />
          <VStack align="start" flex={1}>
            <Skeleton height="16px" width="150px" />
            <Skeleton height="12px" width="100px" />
          </VStack>
        </HStack>
        <SkeletonText noOfLines={3} spacing="2" />
      </VStack>
    )
  },
  {
    name: 'finalizing',
    duration: 300,
    description: 'Almost ready...',
    skeleton: <Skeleton height="40px" width="100%" />
  }
]

// Service Worker Registration
const registerServiceWorker = async () => {
  if ('serviceWorker' in navigator && process.env.NODE_ENV === 'production') {
    try {
      const registration = await navigator.serviceWorker.register('/sw.js')
      console.log('SW registered:', registration)
      return registration
    } catch (error) {
      console.warn('SW registration failed:', error)
      return null
    }
  }
  return null
}

// Cache Status Check
const checkCacheStatus = (): Promise<boolean> => {
  return new Promise((resolve) => {
    if ('caches' in window) {
      caches.has('wingman-v1').then(resolve).catch(() => resolve(false))
    } else {
      resolve(false)
    }
  })
}

// Progressive Enhancement Manager
class ProgressiveEnhancement {
  private static instance: ProgressiveEnhancement
  private features: Map<string, boolean> = new Map()
  private loadPromises: Map<string, Promise<any>> = new Map()

  static getInstance(): ProgressiveEnhancement {
    if (!ProgressiveEnhancement.instance) {
      ProgressiveEnhancement.instance = new ProgressiveEnhancement()
    }
    return ProgressiveEnhancement.instance
  }

  async checkFeature(feature: string): Promise<boolean> {
    if (this.features.has(feature)) {
      return this.features.get(feature)!
    }

    let supported = false
    switch (feature) {
      case 'serviceWorker':
        supported = 'serviceWorker' in navigator
        break
      case 'cacheAPI':
        supported = 'caches' in window
        break
      case 'intersectionObserver':
        supported = 'IntersectionObserver' in window
        break
      case 'webGL':
        try {
          const canvas = document.createElement('canvas')
          supported = !!(canvas.getContext('webgl') || canvas.getContext('experimental-webgl'))
        } catch {
          supported = false
        }
        break
      case 'geolocation':
        supported = 'geolocation' in navigator
        break
      default:
        supported = false
    }

    this.features.set(feature, supported)
    return supported
  }

  async loadFeature(feature: string, loader: () => Promise<any>): Promise<any> {
    if (!this.loadPromises.has(feature)) {
      this.loadPromises.set(feature, loader())
    }
    return this.loadPromises.get(feature)
  }
}

export const ProgressiveLoader = ({
  children,
  loadingStages = DEFAULT_STAGES,
  showProgress = true,
  minLoadTime = 1000,
  className
}: ProgressiveLoaderProps) => {
  const [currentStage, setCurrentStage] = useState(0)
  const [isLoading, setIsLoading] = useState(true)
  const [progress, setProgress] = useState(0)
  const [cacheReady, setCacheReady] = useState(false)
  const [features, setFeatures] = useState<Record<string, boolean>>({})

  const enhancement = ProgressiveEnhancement.getInstance()

  // Initialize progressive enhancement
  useEffect(() => {
    const initializeFeatures = async () => {
      const featureChecks = await Promise.all([
        enhancement.checkFeature('serviceWorker'),
        enhancement.checkFeature('cacheAPI'),
        enhancement.checkFeature('intersectionObserver'),
        enhancement.checkFeature('geolocation'),
      ])

      setFeatures({
        serviceWorker: featureChecks[0],
        cacheAPI: featureChecks[1],
        intersectionObserver: featureChecks[2],
        geolocation: featureChecks[3],
      })

      // Register service worker if supported
      if (featureChecks[0]) {
        registerServiceWorker()
      }

      // Check cache status
      if (featureChecks[1]) {
        const hasCache = await checkCacheStatus()
        setCacheReady(hasCache)
      }
    }

    initializeFeatures()
  }, [])

  // Progressive loading stages
  useEffect(() => {
    const startTime = Date.now()
    let stageIndex = 0
    let accumulatedTime = 0

    const runStages = () => {
      if (stageIndex >= loadingStages.length) {
        // Ensure minimum load time
        const elapsed = Date.now() - startTime
        const remaining = Math.max(0, minLoadTime - elapsed)
        
        setTimeout(() => {
          setIsLoading(false)
        }, remaining)
        return
      }

      const stage = loadingStages[stageIndex]
      setCurrentStage(stageIndex)

      setTimeout(() => {
        accumulatedTime += stage.duration
        const totalDuration = loadingStages.reduce((sum, s) => sum + s.duration, 0)
        setProgress((accumulatedTime / totalDuration) * 100)
        
        stageIndex++
        runStages()
      }, stage.duration)
    }

    runStages()
  }, [loadingStages, minLoadTime])

  // Render loading state
  if (isLoading) {
    const currentStageData = loadingStages[currentStage]
    
    return (
      <Box className={className} p={6}>
        <VStack spacing={6} align="center">
          {/* Progress indicator */}
          {showProgress && (
            <Box width="100%" maxW="400px">
              <Text fontSize="sm" color="gray.600" mb={2}>
                {currentStageData?.description || 'Loading...'}
              </Text>
              <Progress value={progress} colorScheme="blue" size="sm" borderRadius="full" />
              <Text fontSize="xs" color="gray.500" mt={1} textAlign="center">
                {Math.round(progress)}%
              </Text>
            </Box>
          )}

          {/* Stage-specific skeleton */}
          <Box width="100%">
            {currentStageData?.skeleton}
          </Box>

          {/* Feature status indicators (development only) */}
          {process.env.NODE_ENV === 'development' && (
            <Box fontSize="xs" color="gray.500">
              <Text>Features: SW:{features.serviceWorker ? '✓' : '✗'} Cache:{cacheReady ? '✓' : '✗'}</Text>
            </Box>
          )}
        </VStack>
      </Box>
    )
  }

  return <>{children}</>
}

// Specialized loaders for WingmanMatch features
export const AssessmentLoader = ({ children }: { children: ReactNode }) => (
  <ProgressiveLoader
    loadingStages={[
      {
        name: 'questions',
        duration: 600,
        description: 'Loading assessment questions...',
        skeleton: (
          <VStack spacing={4}>
            <Skeleton height="80px" />
            <VStack spacing={2} width="100%">
              {Array.from({ length: 4 }).map((_, i) => (
                <HStack key={i} spacing={3} width="100%">
                  <Skeleton width="20px" height="20px" borderRadius="full" />
                  <Skeleton height="20px" flex={1} />
                </HStack>
              ))}
            </VStack>
          </VStack>
        )
      },
      {
        name: 'progress',
        duration: 400,
        description: 'Checking your progress...',
        skeleton: <Skeleton height="40px" />
      }
    ]}
    minLoadTime={800}
  >
    {children}
  </ProgressiveLoader>
)

export const ChatLoader = ({ children }: { children: ReactNode }) => (
  <ProgressiveLoader
    loadingStages={[
      {
        name: 'messages',
        duration: 500,
        description: 'Loading conversation...',
        skeleton: (
          <VStack spacing={3}>
            {Array.from({ length: 3 }).map((_, i) => (
              <HStack key={i} spacing={3} width="100%">
                <Skeleton width="40px" height="40px" borderRadius="full" />
                <VStack align="start" flex={1}>
                  <Skeleton height="16px" width="80px" />
                  <SkeletonText noOfLines={2} spacing="1" />
                </VStack>
              </HStack>
            ))}
          </VStack>
        )
      },
      {
        name: 'ai',
        duration: 700,
        description: 'Connecting to AI coach...',
        skeleton: <Skeleton height="60px" />
      }
    ]}
    minLoadTime={1000}
  >
    {children}
  </ProgressiveLoader>
)

export const ProfileLoader = ({ children }: { children: ReactNode }) => (
  <ProgressiveLoader
    loadingStages={[
      {
        name: 'form',
        duration: 400,
        description: 'Setting up your profile...',
        skeleton: (
          <VStack spacing={4}>
            <Skeleton height="120px" width="120px" borderRadius="full" />
            <VStack spacing={3} width="100%">
              <Skeleton height="40px" />
              <Skeleton height="40px" />
              <Skeleton height="80px" />
            </VStack>
          </VStack>
        )
      },
      {
        name: 'location',
        duration: 600,
        description: 'Initializing location services...',
        skeleton: <Skeleton height="200px" />
      }
    ]}
    minLoadTime={800}
  >
    {children}
  </ProgressiveLoader>
)

// Hook for progressive enhancement
export const useProgressiveEnhancement = () => {
  const [enhancement] = useState(() => ProgressiveEnhancement.getInstance())
  
  return {
    checkFeature: enhancement.checkFeature.bind(enhancement),
    loadFeature: enhancement.loadFeature.bind(enhancement),
  }
}