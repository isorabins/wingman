/**
 * Enhanced Location Capture Component
 * 
 * Features:
 * - Multi-stage progress indicators
 * - Retry mechanism with exponential backoff
 * - Graceful fallback to manual city entry
 * - Privacy mode switching
 * - Accessibility compliance
 * - Real-time feedback during location acquisition
 */

import React, { useState, useCallback, useEffect } from 'react'
import {
  Box,
  Button,
  VStack,
  HStack,
  Alert,
  AlertIcon,
  AlertTitle,
  AlertDescription,
  Progress,
  Text,
  Input,
  FormControl,
  FormLabel,
  FormErrorMessage,
  FormHelperText,
  Switch,
  Collapse,
  useColorModeValue,
  CircularProgress,
  CircularProgressLabel,
  Badge,
  Icon,
  Tooltip,
  Fade
} from '@chakra-ui/react'
import {
  MapPin,
  RefreshCw,
  AlertTriangle,
  CheckCircle,
  Navigation,
  Clock,
  Shield,
  Edit3
} from 'lucide-react'
import { locationService, LocationResult, LocationErrorCode } from '../services/locationService'

interface LocationCaptureProps {
  onLocationUpdate: (coordinates: { lat?: number; lng?: number; city?: string }) => void
  onPrivacyModeChange: (mode: 'precise' | 'city_only') => void
  privacyMode: 'precise' | 'city_only'
  initialCity?: string
  isRequired?: boolean
  disabled?: boolean
}

interface LocationState {
  status: 'idle' | 'requesting' | 'success' | 'error' | 'retry'
  stage: string
  progress: number
  result?: LocationResult
  manualCity: string
  showManualEntry: boolean
  retryCount: number
  lastError?: string
}

export const LocationCapture: React.FC<LocationCaptureProps> = ({
  onLocationUpdate,
  onPrivacyModeChange,
  privacyMode,
  initialCity = '',
  isRequired = true,
  disabled = false
}) => {
  const [locationState, setLocationState] = useState<LocationState>({
    status: 'idle',
    stage: '',
    progress: 0,
    manualCity: initialCity,
    showManualEntry: privacyMode === 'city_only',
    retryCount: 0
  })

  // Color scheme
  const successColor = useColorModeValue('green.500', 'green.300')
  const errorColor = useColorModeValue('red.500', 'red.300')
  const warningColor = useColorModeValue('orange.500', 'orange.300')

  // Progress callback for location service
  const handleProgress = useCallback((stage: string, progress: number) => {
    setLocationState(prev => ({
      ...prev,
      stage,
      progress
    }))
  }, [])

  // Request location
  const requestLocation = useCallback(async () => {
    if (disabled) return

    setLocationState(prev => ({
      ...prev,
      status: 'requesting',
      stage: 'Initializing...',
      progress: 0,
      result: undefined,
      lastError: undefined
    }))

    try {
      const result = await locationService.getCurrentLocation({
        privacy: privacyMode,
        onProgress: handleProgress
      })

      setLocationState(prev => ({
        ...prev,
        status: result.success ? 'success' : 'error',
        result,
        lastError: result.error
      }))

      if (result.success && result.coordinates) {
        onLocationUpdate({
          lat: result.coordinates.lat,
          lng: result.coordinates.lng,
          city: result.city
        })
      }

      // Auto-show manual entry if location fails and it's retryable
      if (!result.success && result.retryable) {
        setTimeout(() => {
          setLocationState(prev => ({
            ...prev,
            showManualEntry: true
          }))
        }, 2000)
      }

    } catch (error) {
      console.error('Location request failed:', error)
      setLocationState(prev => ({
        ...prev,
        status: 'error',
        lastError: 'Unexpected error occurred'
      }))
    }
  }, [disabled, privacyMode, handleProgress, onLocationUpdate])

  // Retry location request
  const retryLocation = useCallback(async () => {
    if (disabled) return

    setLocationState(prev => ({
      ...prev,
      status: 'retry',
      stage: 'Retrying...',
      progress: 0,
      retryCount: prev.retryCount + 1
    }))

    try {
      const result = await locationService.retryLocation({
        onProgress: handleProgress
      })

      setLocationState(prev => ({
        ...prev,
        status: result.success ? 'success' : 'error',
        result,
        lastError: result.error
      }))

      if (result.success && result.coordinates) {
        onLocationUpdate({
          lat: result.coordinates.lat,
          lng: result.coordinates.lng,
          city: result.city
        })
      } else if (!result.retryable) {
        // Force manual entry if no more retries
        setLocationState(prev => ({
          ...prev,
          showManualEntry: true
        }))
      }

    } catch (error) {
      console.error('Location retry failed:', error)
      setLocationState(prev => ({
        ...prev,
        status: 'error',
        lastError: 'Retry failed'
      }))
    }
  }, [disabled, handleProgress, onLocationUpdate])

  // Handle manual city input
  const handleManualCityChange = useCallback((city: string) => {
    setLocationState(prev => ({
      ...prev,
      manualCity: city
    }))

    onLocationUpdate({ city })
  }, [onLocationUpdate])

  // Handle privacy mode toggle
  const handlePrivacyToggle = useCallback((checked: boolean) => {
    const newMode = checked ? 'precise' : 'city_only'
    onPrivacyModeChange(newMode)
    
    setLocationState(prev => ({
      ...prev,
      showManualEntry: newMode === 'city_only',
      status: 'idle' // Reset status when switching modes
    }))
  }, [onPrivacyModeChange])

  // Show manual entry fallback
  const showManualEntry = useCallback(() => {
    setLocationState(prev => ({
      ...prev,
      showManualEntry: true
    }))
  }, [])

  // Get status display info
  const getStatusInfo = () => {
    const { status, result, stage, progress, retryCount } = locationState

    switch (status) {
      case 'requesting':
      case 'retry':
        return {
          status: 'info' as const,
          icon: Navigation,
          title: status === 'retry' ? `Retrying... (Attempt ${retryCount + 1})` : 'Getting Location',
          description: stage,
          showProgress: true
        }
      case 'success':
        return {
          status: 'success' as const,
          icon: CheckCircle,
          title: 'Location Captured',
          description: result?.city ? `Detected: ${result.city}` : 'Coordinates obtained',
          showProgress: false
        }
      case 'error':
        return {
          status: 'error' as const,
          icon: AlertTriangle,
          title: 'Location Failed',
          description: result?.error || 'Unable to get location',
          showProgress: false
        }
      default:
        return null
    }
  }

  const statusInfo = getStatusInfo()

  return (
    <VStack spacing={6} align="stretch">
      {/* Privacy Mode Toggle */}
      <FormControl>
        <FormLabel>
          <HStack>
            <Icon as={Shield} color="brand.400" />
            <Text>Location Privacy</Text>
          </HStack>
        </FormLabel>
        <HStack>
          <Switch
            isChecked={privacyMode === 'precise'}
            onChange={(e) => handlePrivacyToggle(e.target.checked)}
            colorScheme="brand"
            isDisabled={disabled}
          />
          <Text fontWeight="medium">
            {privacyMode === 'precise' ? 'Share exact location' : 'City only'}
          </Text>
          <Tooltip 
            label={privacyMode === 'precise' 
              ? 'Your precise coordinates will be used for more accurate matching'
              : 'Only your city will be shared for privacy'
            }
          >
            <Badge 
              variant="outline" 
              colorScheme={privacyMode === 'precise' ? 'blue' : 'green'}
              cursor="help"
            >
              {privacyMode === 'precise' ? 'Precise' : 'Private'}
            </Badge>
          </Tooltip>
        </HStack>
        <FormHelperText>
          {privacyMode === 'precise' 
            ? 'Your precise coordinates will be used for matching within your travel radius'
            : 'Only your city will be shared, using city center for distance calculations'
          }
        </FormHelperText>
      </FormControl>

      {/* Location Capture Section */}
      {privacyMode === 'precise' && (
        <VStack spacing={4} align="stretch">
          {/* Main Location Button */}
          <Button
            onClick={requestLocation}
            isLoading={locationState.status === 'requesting' || locationState.status === 'retry'}
            loadingText={locationState.stage || 'Getting location...'}
            leftIcon={<Icon as={MapPin} />}
            variant="outline"
            borderColor="brand.400"
            color="brand.900"
            _hover={{ bg: "brand.100" }}
            isDisabled={disabled || locationState.status === 'success'}
            size="lg"
          >
            {locationState.status === 'success' && locationState.result?.city
              ? `Location captured • ${locationState.result.city}`
              : locationState.status === 'success'
              ? 'Location captured'
              : 'Use My Current Location'
            }
          </Button>

          {/* Progress Indicator */}
          {statusInfo && statusInfo.showProgress && (
            <Fade in={true}>
              <VStack spacing={2}>
                <HStack w="full" justify="space-between">
                  <HStack>
                    <CircularProgress 
                      value={locationState.progress} 
                      color="brand.400"
                      size="24px"
                      thickness="12px"
                    />
                    <Text fontSize="sm" fontWeight="medium">
                      {statusInfo.description}
                    </Text>
                  </HStack>
                  <Text fontSize="xs" color="gray.500">
                    {Math.round(locationState.progress)}%
                  </Text>
                </HStack>
                <Progress 
                  value={locationState.progress} 
                  colorScheme="brand" 
                  size="sm" 
                  w="full" 
                  borderRadius="md"
                />
              </VStack>
            </Fade>
          )}

          {/* Status Messages */}
          {statusInfo && (
            <Fade in={true}>
              <Alert 
                status={statusInfo.status} 
                borderRadius="md"
                variant="left-accent"
              >
                <AlertIcon as={statusInfo.icon} />
                <Box>
                  <AlertTitle fontSize="sm">{statusInfo.title}</AlertTitle>
                  <AlertDescription fontSize="sm">
                    {statusInfo.description}
                  </AlertDescription>
                </Box>
              </Alert>
            </Fade>
          )}

          {/* Retry Button */}
          {locationState.status === 'error' && locationState.result?.retryable && (
            <Fade in={true}>
              <HStack spacing={3}>
                <Button
                  onClick={retryLocation}
                  leftIcon={<Icon as={RefreshCw} />}
                  variant="outline"
                  colorScheme="orange"
                  size="sm"
                  isDisabled={disabled}
                >
                  Try Again
                </Button>
                <Button
                  onClick={showManualEntry}
                  leftIcon={<Icon as={Edit3} />}
                  variant="ghost"
                  size="sm"
                  isDisabled={disabled}
                >
                  Enter City Manually
                </Button>
              </HStack>
            </Fade>
          )}

          {/* Location Accuracy Info */}
          {locationState.status === 'success' && locationState.result?.coordinates?.accuracy && (
            <Alert status="info" size="sm" borderRadius="md">
              <AlertIcon />
              <AlertDescription fontSize="xs">
                Location accuracy: ±{Math.round(locationState.result.coordinates.accuracy)}m
                {locationState.result.source === 'cache' && ' (cached)'}
              </AlertDescription>
            </Alert>
          )}
        </VStack>
      )}

      {/* Manual City Entry */}
      <Collapse in={locationState.showManualEntry || privacyMode === 'city_only'}>
        <FormControl isInvalid={isRequired && !locationState.manualCity} isRequired={isRequired}>
          <FormLabel>
            <HStack>
              <Icon as={Edit3} color="brand.400" />
              <Text>City</Text>
            </HStack>
          </FormLabel>
          <Input
            value={locationState.manualCity}
            onChange={(e) => handleManualCityChange(e.target.value)}
            placeholder="Enter your city (e.g., San Francisco, CA)"
            bg="white"
            isDisabled={disabled}
          />
          <FormErrorMessage>
            Please enter your city name
          </FormErrorMessage>
          <FormHelperText>
            {privacyMode === 'city_only' 
              ? "We'll use your city center for distance calculations"
              : "As a backup, you can enter your city manually"
            }
          </FormHelperText>
        </FormControl>
      </Collapse>

      {/* Tips for Location Issues */}
      {locationState.status === 'error' && locationState.result?.errorCode === LocationErrorCode.PERMISSION_DENIED && (
        <Alert status="info" borderRadius="md" size="sm">
          <AlertIcon />
          <Box>
            <AlertTitle fontSize="sm">Location Permission Needed</AlertTitle>
            <AlertDescription fontSize="xs">
              To use precise location, please:
              <br />• Click the location icon in your browser's address bar
              <br />• Select "Allow" for location access
              <br />• Refresh the page and try again
            </AlertDescription>
          </Box>
        </Alert>
      )}
    </VStack>
  )
}

export default LocationCapture