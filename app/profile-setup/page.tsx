"use client"

import { useState, useCallback, useEffect } from "react"
import { useRouter } from "next/navigation"
import { useAuth } from "../../lib/auth-context"
import { useForm, Controller } from "react-hook-form"
import { zodResolver } from "@hookform/resolvers/zod"
import { z } from "zod"
import { useDropzone } from "react-dropzone"
import {
  Box,
  Button,
  Card,
  CardBody,
  Container,
  Flex,
  FormControl,
  FormErrorMessage,
  FormHelperText,
  FormLabel,
  Heading,
  HStack,
  Image,
  Input,
  Progress,
  Slider,
  SliderFilledTrack,
  SliderThumb,
  SliderTrack,
  Switch,
  Text,
  Textarea,
  VStack,
  useToast,
  CircularProgress,
  CircularProgressLabel,
  Badge,
  Icon,
  Alert,
  AlertIcon,
  AlertTitle,
  AlertDescription,
} from "@chakra-ui/react"
import { 
  Upload, 
  MapPin, 
  User, 
  Camera, 
  X, 
  Check, 
  AlertTriangle,
  Loader2
} from "lucide-react"
import { photoUploadService, type PhotoUploadProgress } from "../../storage/photo_upload"
import LocationCapture from "../../components/LocationCapture"

// Validation schema
const profileSetupSchema = z.object({
  bio: z.string()
    .min(10, "Bio must be at least 10 characters")
    .max(400, "Bio must be 400 characters or less")
    .refine((bio) => {
      // Check for PII patterns
      const phonePattern = /(\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4})/
      const emailPattern = /([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})/
      return !phonePattern.test(bio) && !emailPattern.test(bio)
    }, "Please don't include phone numbers or email addresses in your bio"),
  
  location: z.object({
    lat: z.number().min(-90).max(90).optional(),
    lng: z.number().min(-180).max(180).optional(),
    city: z.string().optional(),
    privacy_mode: z.enum(["precise", "city_only"]),
  }).refine((location) => {
    // Either coordinates or city must be provided
    return (location.lat !== undefined && location.lng !== undefined) || (location.city && location.city.trim().length > 0)
  }, "Either precise location or city name is required"),
  
  travel_radius: z.number().min(1).max(50),
  photo_file: z.instanceof(File).optional(),
})

type ProfileSetupForm = z.infer<typeof profileSetupSchema>

// Location state now handled by LocationCapture component

interface PhotoUploadState {
  isUploading: boolean
  progress: number
  stage: string
  error: string | null
  photoUrl: string | null
  previewUrl: string | null
}

// Component that contains all the form logic - only renders when user is authenticated
function ProfileSetupForm({ user }: { user: any }) {
  const router = useRouter()
  const toast = useToast()

  // Form state
  const { 
    control, 
    handleSubmit, 
    formState: { errors, isSubmitting, isValid },
    setValue,
    watch,
    trigger
  } = useForm<ProfileSetupForm>({
    resolver: zodResolver(profileSetupSchema),
    defaultValues: {
      bio: "",
      location: {
        privacy_mode: "city_only",
        city: "",
      },
      travel_radius: 20,
    },
    mode: "onChange"
  })

  // Watch form values for live updates
  const bioValue = watch("bio")
  const privacyMode = watch("location.privacy_mode")
  const travelRadius = watch("travel_radius")
  

  // Photo upload state
  const [photoState, setPhotoState] = useState<PhotoUploadState>({
    isUploading: false,
    progress: 0,
    stage: "",
    error: null,
    photoUrl: null,
    previewUrl: null
  })

  // Character count for bio
  const bioCharCount = bioValue?.length || 0
  const bioProgress = (bioCharCount / 400) * 100

  // Handle location updates from LocationCapture component
  const handleLocationUpdate = useCallback(async (coordinates: { lat?: number; lng?: number; city?: string }) => {
    if (coordinates.lat && coordinates.lng) {
      setValue("location.lat", coordinates.lat)
      setValue("location.lng", coordinates.lng)
    }
    
    if (coordinates.city) {
      setValue("location.city", coordinates.city)
    }
    
    await trigger("location")
  }, [setValue, trigger])

  // Handle privacy mode changes
  const handlePrivacyModeChange = useCallback(async (mode: 'precise' | 'city_only') => {
    setValue("location.privacy_mode", mode)
    await trigger("location")
  }, [setValue, trigger])

  // Handle photo upload
  const onDrop = useCallback(async (acceptedFiles: File[]) => {
    const file = acceptedFiles[0]
    if (!file) return

    // Validate file
    const validation = photoUploadService.validatePhotoFile(file)
    if (!validation.valid) {
      setPhotoState(prev => ({
        ...prev,
        error: validation.error || "Invalid file"
      }))
      return
    }

    // Create preview URL
    const previewUrl = URL.createObjectURL(file)
    setPhotoState(prev => ({
      ...prev,
      previewUrl,
      error: null,
      isUploading: true,
      progress: 0
    }))

    try {
      // For demo purposes, we'll use a mock user ID
      // In production, this would come from authentication context
      const userId = user.id
      
      const result = await photoUploadService.uploadPhoto(
        file,
        userId,
        (progress: PhotoUploadProgress) => {
          setPhotoState(prev => ({
            ...prev,
            progress: progress.progress,
            stage: progress.stage
          }))
        }
      )

      if (result.success && result.photoUrl) {
        setPhotoState(prev => ({
          ...prev,
          isUploading: false,
          photoUrl: result.photoUrl || null,
          progress: 100,
          stage: "complete"
        }))
        
        setValue("photo_file", file)
        await trigger("photo_file")
        
        toast({
          title: "Photo uploaded successfully",
          status: "success",
          duration: 3000,
        })
      } else {
        throw new Error(result.error || "Upload failed")
      }
    } catch (error) {
      setPhotoState(prev => ({
        ...prev,
        isUploading: false,
        error: error instanceof Error ? error.message : "Upload failed"
      }))
      
      toast({
        title: "Photo upload failed",
        description: error instanceof Error ? error.message : "Please try again",
        status: "error",
        duration: 5000,
      })
    }
  }, [setValue, trigger, toast])

  // Remove uploaded photo
  const removePhoto = useCallback(() => {
    if (photoState.previewUrl) {
      URL.revokeObjectURL(photoState.previewUrl)
    }
    
    setPhotoState({
      isUploading: false,
      progress: 0,
      stage: "",
      error: null,
      photoUrl: null,
      previewUrl: null
    })
    
    setValue("photo_file", undefined)
  }, [photoState.previewUrl, setValue])

  // Setup dropzone
  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      'image/*': ['.jpeg', '.jpg', '.png', '.webp', '.gif']
    },
    maxSize: 5 * 1024 * 1024, // 5MB
    multiple: false,
    disabled: photoState.isUploading
  })

  // Form submission
  const onSubmit = async (data: ProfileSetupForm) => {
    try {
      // Prepare the request payload
      const locationData = {
        lat: data.location.lat || 0, // Default to 0,0 if no coordinates provided
        lng: data.location.lng || 0,
        city: data.location.city,
        privacy_mode: data.location.privacy_mode
      }

      const payload = {
        user_id: user.id,
        bio: data.bio,
        location: locationData,
        travel_radius: data.travel_radius,
        photo_url: photoState.photoUrl
      }

      const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'
      const response = await fetch(`${apiUrl}/api/profile/complete`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(payload),
      })

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}))
        throw new Error(errorData.detail || `HTTP ${response.status}`)
      }

      const result = await response.json()
      
      if (result.success) {
        toast({
          title: "Profile completed successfully!",
          description: "You're ready to find your wingman buddy",
          status: "success",
          duration: 4000,
        })
        
        // Redirect to find-buddy page
        router.push('/find-buddy')
      } else {
        throw new Error(result.message || "Profile completion failed")
      }
      
    } catch (error) {
      console.error('Profile submission error:', error)
      toast({
        title: "Profile submission failed",
        description: error instanceof Error ? error.message : "Please try again",
        status: "error",
        duration: 5000,
      })
    }
  }

  return (
    <Box minH="100vh" bg="brand.50">
      {/* Header */}
      <Box borderBottom="1px solid" borderColor="gray.200">
        <Container maxW="4xl" py={6} px={4}>
          <VStack spacing={4} textAlign="center">
            <Heading as="h1" size="xl" fontFamily="heading" color="brand.900">
              Complete Your Profile
            </Heading>
            <Text color="gray.600" fontSize="lg">
              Tell us about yourself and set your preferences
            </Text>
          </VStack>
        </Container>
      </Box>

      {/* Main Content */}
      <Container maxW="4xl" py={8} px={4}>
        <form onSubmit={handleSubmit(onSubmit)}>
          <VStack spacing={8} align="stretch">
            
            {/* Photo Upload Section */}
            <Card>
              <CardBody p={8}>
                <VStack spacing={6} align="stretch">
                  <HStack>
                    <Icon as={Camera} color="brand.400" />
                    <Heading as="h2" size="md" color="brand.900">
                      Profile Photo
                    </Heading>
                    <Badge colorScheme="gray" variant="subtle">Optional</Badge>
                  </HStack>
                  
                  {photoState.previewUrl ? (
                    // Photo preview
                    <VStack spacing={4}>
                      <Box position="relative">
                        <Image
                          src={photoState.previewUrl}
                          alt="Profile preview"
                          borderRadius="lg"
                          maxH="200px"
                          maxW="200px"
                          objectFit="cover"
                        />
                        <Button
                          position="absolute"
                          top={2}
                          right={2}
                          size="sm"
                          colorScheme="red"
                          variant="solid"
                          onClick={removePhoto}
                          isDisabled={photoState.isUploading}
                        >
                          <Icon as={X} />
                        </Button>
                      </Box>
                      
                      {photoState.isUploading && (
                        <VStack spacing={2}>
                          <CircularProgress 
                            value={photoState.progress} 
                            color="brand.400"
                            size="60px"
                          >
                            <CircularProgressLabel fontSize="sm">
                              {Math.round(photoState.progress)}%
                            </CircularProgressLabel>
                          </CircularProgress>
                          <Text fontSize="sm" color="gray.600" textTransform="capitalize">
                            {photoState.stage}...
                          </Text>
                        </VStack>
                      )}
                    </VStack>
                  ) : (
                    // Photo upload dropzone
                    <Box
                      {...getRootProps()}
                      borderWidth="2px"
                      borderStyle="dashed"
                      borderColor={isDragActive ? "brand.400" : "gray.200"}
                      borderRadius="lg"
                      p={8}
                      textAlign="center"
                      cursor="pointer"
                      bg={isDragActive ? "brand.50" : "white"}
                      transition="all 0.2s"
                      _hover={{
                        borderColor: "brand.400",
                        bg: "brand.50"
                      }}
                    >
                      <input {...getInputProps()} />
                      <VStack spacing={4}>
                        <Icon as={Upload} size={32} color="brand.400" />
                        <VStack spacing={2}>
                          <Text fontWeight="medium" color="brand.900">
                            {isDragActive ? "Drop your photo here" : "Upload a profile photo"}
                          </Text>
                          <Text fontSize="sm" color="gray.600">
                            Drag and drop or click to browse
                          </Text>
                          <Text fontSize="xs" color="gray.500">
                            JPEG, PNG, WebP, GIF • Max 5MB
                          </Text>
                        </VStack>
                      </VStack>
                    </Box>
                  )}
                  
                  {photoState.error && (
                    <Alert status="error" borderRadius="md">
                      <AlertIcon />
                      <AlertTitle fontSize="sm">Upload Error:</AlertTitle>
                      <AlertDescription fontSize="sm">
                        {photoState.error}
                      </AlertDescription>
                    </Alert>
                  )}
                </VStack>
              </CardBody>
            </Card>

            {/* Bio Section */}
            <Card>
              <CardBody p={8}>
                <VStack spacing={6} align="stretch">
                  <HStack>
                    <Icon as={User} color="brand.400" />
                    <Heading as="h2" size="md" color="brand.900">
                      About You
                    </Heading>
                    <Badge colorScheme="red" variant="solid">Required</Badge>
                  </HStack>

                  <Controller
                    name="bio"
                    control={control}
                    render={({ field }) => (
                      <FormControl isInvalid={!!errors.bio}>
                        <FormLabel>Tell us about yourself</FormLabel>
                        <Textarea
                          {...field}
                          placeholder="Share what makes you unique, your interests, what you're looking for in a wingman buddy..."
                          rows={4}
                          resize="vertical"
                          bg="white"
                        />
                        <Flex justify="space-between" align="center" mt={2}>
                          <FormErrorMessage>
                            {errors.bio?.message}
                          </FormErrorMessage>
                          <HStack spacing={2}>
                            <Progress
                              value={bioProgress}
                              size="sm"
                              w="100px"
                              colorScheme={bioProgress > 90 ? "red" : "brand"}
                            />
                            <Text
                              fontSize="sm"
                              color={bioProgress > 90 ? "red.500" : "gray.600"}
                            >
                              {bioCharCount}/400
                            </Text>
                          </HStack>
                        </Flex>
                        {!errors.bio && (
                          <FormHelperText>
                            Minimum 10 characters. Avoid including personal contact information.
                          </FormHelperText>
                        )}
                      </FormControl>
                    )}
                  />
                </VStack>
              </CardBody>
            </Card>

            {/* Location Section */}
            <Card>
              <CardBody p={8}>
                <VStack spacing={6} align="stretch">
                  <HStack>
                    <Icon as={MapPin} color="brand.400" />
                    <Heading as="h2" size="md" color="brand.900">
                      Location & Preferences
                    </Heading>
                    <Badge colorScheme="red" variant="solid">Required</Badge>
                  </HStack>

                  {/* Enhanced Location Capture */}
                  <LocationCapture
                    onLocationUpdate={handleLocationUpdate}
                    onPrivacyModeChange={handlePrivacyModeChange}
                    privacyMode={privacyMode}
                    initialCity={watch("location.city") || ""}
                    isRequired={true}
                    disabled={isSubmitting}
                  />

                  {/* Show validation errors */}
                  {errors.location && (
                    <Alert status="error" borderRadius="md">
                      <AlertIcon />
                      <AlertDescription fontSize="sm">
                        {errors.location.message}
                      </AlertDescription>
                    </Alert>
                  )}

                  {/* Travel Radius */}
                  <Controller
                    name="travel_radius"
                    control={control}
                    render={({ field }) => (
                      <FormControl>
                        <FormLabel>Travel Radius: {field.value} miles</FormLabel>
                        <Slider
                          {...field}
                          min={1}
                          max={50}
                          step={1}
                          colorScheme="brand"
                        >
                          <SliderTrack>
                            <SliderFilledTrack />
                          </SliderTrack>
                          <SliderThumb />
                        </Slider>
                        <FormHelperText>
                          Maximum distance you're willing to travel to meet your wingman buddy
                        </FormHelperText>
                      </FormControl>
                    )}
                  />
                </VStack>
              </CardBody>
            </Card>

            {/* Submit Button */}
            <Card>
              <CardBody p={8}>
                <VStack spacing={4}>
                  <Button
                    type="submit"
                    size="lg"
                    colorScheme="brand"
                    bg="brand.900"
                    color="brand.50"
                    _hover={{ bg: "gray.600" }}
                    isLoading={isSubmitting}
                    loadingText="Completing profile..."
                    isDisabled={!isValid || photoState.isUploading}
                    w="full"
                    maxW="300px"
                  >
                    {isSubmitting ? (
                      <HStack>
                        <Loader2 size={16} />
                        <Text>Completing Profile...</Text>
                      </HStack>
                    ) : (
                      "Complete Profile"
                    )}
                  </Button>
                  
                  {/* Debug info - remove after testing */}
                  <Box p={2} bg="gray.100" borderRadius="md" fontSize="xs">
                    <Text>Form Valid: {isValid ? "✅" : "❌"}</Text>
                    <Text>Bio length: {watch("bio")?.length || 0}/10 min</Text>
                    <Text>City: {watch("location.city") || "empty"}</Text>
                    <Text>Coordinates: {watch("location.lat") ? "✅" : "❌"}</Text>
                    <Text>Errors: {Object.keys(errors).join(", ") || "none"}</Text>
                  </Box>
                  
                  <Text fontSize="sm" color="gray.600" textAlign="center">
                    By completing your profile, you'll be ready to find and connect with wingman buddies
                  </Text>
                </VStack>
              </CardBody>
            </Card>
          </VStack>
        </form>
      </Container>
    </Box>
  )
}

// Main component with authentication guards
export default function ProfileSetupPage() {
  const { user, loading } = useAuth()
  const router = useRouter()

  // Authentication guard
  useEffect(() => {
    if (!loading && !user) {
      router.push('/auth/signin')
    }
  }, [user, loading, router])

  // Show loading while checking authentication
  if (loading) {
    return (
      <Container maxW="4xl" py={8}>
        <VStack spacing={4}>
          <CircularProgress isIndeterminate color="brand.500" />
          <Text>Loading...</Text>
        </VStack>
      </Container>
    )
  }

  // Don't render if no user
  if (!user) {
    return null
  }

  // Render the actual form component
  return <ProfileSetupForm user={user} />
}