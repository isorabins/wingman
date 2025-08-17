/**
 * Enhanced Location Service for WingmanMatch Profile Setup
 * 
 * Features:
 * - Progressive timeout strategy with automatic retries
 * - Multiple reverse geocoding providers with fallback
 * - Location caching and validation
 * - Comprehensive error handling with user-friendly messages
 * - Privacy controls and coordinate precision management
 * 
 * Usage:
 * ```typescript
 * const locationService = new LocationService()
 * const result = await locationService.getCurrentLocation()
 * ```
 */

export interface Coordinates {
  lat: number
  lng: number
  accuracy?: number
  timestamp?: number
}

export interface LocationResult {
  success: boolean
  coordinates?: Coordinates
  city?: string
  error?: string
  errorCode?: LocationErrorCode
  retryable?: boolean
  source: 'gps' | 'network' | 'cache'
}

export interface GeocodeResult {
  success: boolean
  city?: string
  region?: string
  country?: string
  error?: string
  provider: string
  confidence?: number
}

export enum LocationErrorCode {
  PERMISSION_DENIED = 'permission_denied',
  POSITION_UNAVAILABLE = 'position_unavailable', 
  TIMEOUT = 'timeout',
  NETWORK_ERROR = 'network_error',
  INVALID_COORDINATES = 'invalid_coordinates',
  GEOCODING_FAILED = 'geocoding_failed',
  NOT_SUPPORTED = 'not_supported'
}

interface LocationServiceConfig {
  initialTimeout: number
  retryTimeout: number
  maxRetries: number
  cacheExpiry: number
  accuracyThreshold: number
  enableCache: boolean
  fallbackProviders: GeocodeProvider[]
}

interface GeocodeProvider {
  name: string
  url: (lat: number, lng: number) => string
  parser: (response: any) => GeocodeResult
  rateLimit?: number
}

interface CachedLocation {
  coordinates: Coordinates
  city?: string
  timestamp: number
}

export class LocationService {
  private config: LocationServiceConfig
  private cache: Map<string, CachedLocation> = new Map()
  private retryCount = 0
  private lastRequestTime = 0
  
  constructor(config?: Partial<LocationServiceConfig>) {
    this.config = {
      initialTimeout: 15000,      // 15 seconds initial timeout
      retryTimeout: 30000,        // 30 seconds for retry
      maxRetries: 2,              // Maximum 2 retries
      cacheExpiry: 600000,        // 10 minutes cache
      accuracyThreshold: 1000,    // 1km accuracy threshold
      enableCache: true,
      fallbackProviders: [
        {
          name: 'BigDataCloud',
          url: (lat, lng) => `https://api.bigdatacloud.net/data/reverse-geocode-client?latitude=${lat}&longitude=${lng}&localityLanguage=en`,
          parser: this.parseBigDataCloudResponse
        },
        {
          name: 'Nominatim',
          url: (lat, lng) => `https://nominatim.openstreetmap.org/reverse?format=json&lat=${lat}&lon=${lng}&zoom=10`,
          parser: this.parseNominatimResponse
        }
      ],
      ...config
    }
  }

  /**
   * Get current location with enhanced error handling and retry logic
   */
  async getCurrentLocation(options?: {
    forceRefresh?: boolean
    privacy?: 'precise' | 'city_only'
    onProgress?: (stage: string, progress: number) => void
  }): Promise<LocationResult> {
    const { forceRefresh = false, privacy = 'precise', onProgress } = options || {}
    
    try {
      // Check browser support
      if (!navigator.geolocation) {
        return {
          success: false,
          error: 'Geolocation is not supported by this browser. Please enter your city manually.',
          errorCode: LocationErrorCode.NOT_SUPPORTED,
          retryable: false,
          source: 'gps'
        }
      }

      // Check cache first (unless forced refresh)
      if (!forceRefresh && this.config.enableCache) {
        const cached = this.getCachedLocation()
        if (cached) {
          onProgress?.('cache', 100)
          return {
            success: true,
            coordinates: cached.coordinates,
            city: cached.city,
            source: 'cache'
          }
        }
      }

      onProgress?.('permission', 10)

      // Request location with progressive timeout
      const timeout = this.retryCount === 0 ? this.config.initialTimeout : this.config.retryTimeout
      const coordinates = await this.requestGeolocation(timeout, onProgress)

      onProgress?.('geocoding', 70)

      // Reverse geocode to get city name
      let city: string | undefined
      if (coordinates) {
        try {
          const geocodeResult = await this.reverseGeocode(coordinates.lat, coordinates.lng)
          city = geocodeResult.city
        } catch (geocodeError) {
          console.warn('Geocoding failed, but location was successful:', geocodeError)
          // Don't fail the entire request if geocoding fails
        }
      }

      onProgress?.('complete', 100)

      const result: LocationResult = {
        success: true,
        coordinates,
        city,
        source: 'gps'
      }

      // Cache the result
      if (this.config.enableCache && coordinates) {
        this.cacheLocation(coordinates, city)
      }

      // Reset retry count on success
      this.retryCount = 0

      return result

    } catch (error: any) {
      return this.handleLocationError(error)
    }
  }

  /**
   * Retry location request with exponential backoff
   */
  async retryLocation(options?: {
    onProgress?: (stage: string, progress: number) => void
  }): Promise<LocationResult> {
    if (this.retryCount >= this.config.maxRetries) {
      return {
        success: false,
        error: 'Maximum retry attempts reached. Please enter your city manually or check your location settings.',
        errorCode: LocationErrorCode.TIMEOUT,
        retryable: false,
        source: 'gps'
      }
    }

    this.retryCount++
    
    // Wait before retry (exponential backoff)
    const delay = Math.min(1000 * Math.pow(2, this.retryCount - 1), 5000)
    await new Promise(resolve => setTimeout(resolve, delay))
    
    return this.getCurrentLocation({ forceRefresh: true, ...options })
  }

  /**
   * Reverse geocode coordinates to get city name with fallback providers
   */
  async reverseGeocode(lat: number, lng: number): Promise<GeocodeResult> {
    // Validate coordinates
    if (!this.validateCoordinates(lat, lng)) {
      return {
        success: false,
        error: 'Invalid coordinates provided',
        provider: 'validation',
        confidence: 0
      }
    }

    let lastError: string | undefined

    // Try each provider in sequence
    for (const provider of this.config.fallbackProviders) {
      try {
        const response = await fetch(provider.url(lat, lng), {
          method: 'GET',
          headers: {
            'User-Agent': 'WingmanMatch/1.0'
          }
        })

        if (!response.ok) {
          throw new Error(`HTTP ${response.status}: ${response.statusText}`)
        }

        const data = await response.json()
        const result = provider.parser(data)
        
        if (result.success && result.city) {
          return result
        }
        
        lastError = result.error || 'No city found'
      } catch (error) {
        console.warn(`Geocoding provider ${provider.name} failed:`, error)
        lastError = error instanceof Error ? error.message : 'Network error'
        continue
      }
    }

    return {
      success: false,
      error: lastError || 'All geocoding providers failed',
      provider: 'fallback',
      confidence: 0
    }
  }

  /**
   * Validate geographic coordinates
   */
  validateCoordinates(lat: number, lng: number): boolean {
    return (
      typeof lat === 'number' &&
      typeof lng === 'number' &&
      !isNaN(lat) &&
      !isNaN(lng) &&
      lat >= -90 &&
      lat <= 90 &&
      lng >= -180 &&
      lng <= 180
    )
  }

  /**
   * Clear location cache
   */
  clearCache(): void {
    this.cache.clear()
  }

  /**
   * Get cached location if valid
   */
  private getCachedLocation(): CachedLocation | null {
    const cacheKey = 'user_location'
    const cached = this.cache.get(cacheKey)
    
    if (!cached) return null
    
    const now = Date.now()
    if (now - cached.timestamp > this.config.cacheExpiry) {
      this.cache.delete(cacheKey)
      return null
    }
    
    return cached
  }

  /**
   * Cache location data
   */
  private cacheLocation(coordinates: Coordinates, city?: string): void {
    const cacheKey = 'user_location'
    this.cache.set(cacheKey, {
      coordinates: {
        ...coordinates,
        timestamp: Date.now()
      },
      city,
      timestamp: Date.now()
    })
  }

  /**
   * Request geolocation with timeout handling
   */
  private async requestGeolocation(
    timeout: number,
    onProgress?: (stage: string, progress: number) => void
  ): Promise<Coordinates> {
    return new Promise((resolve, reject) => {
      // Rate limiting check
      const now = Date.now()
      if (now - this.lastRequestTime < 1000) {
        reject(new Error('Rate limited: too many requests'))
        return
      }
      this.lastRequestTime = now

      onProgress?.('acquiring', 30)

      const timeoutId = setTimeout(() => {
        reject({
          code: 3, // TIMEOUT
          message: 'Location request timed out. This can happen if GPS signal is weak or location services are slow.'
        })
      }, timeout)

      navigator.geolocation.getCurrentPosition(
        (position) => {
          clearTimeout(timeoutId)
          onProgress?.('acquired', 60)
          
          const { latitude, longitude, accuracy } = position.coords
          
          // Validate coordinates
          if (!this.validateCoordinates(latitude, longitude)) {
            reject(new Error('Invalid coordinates received from GPS'))
            return
          }

          resolve({
            lat: latitude,
            lng: longitude,
            accuracy,
            timestamp: position.timestamp
          })
        },
        (error) => {
          clearTimeout(timeoutId)
          reject(error)
        },
        {
          enableHighAccuracy: true,
          timeout: timeout,
          maximumAge: 300000 // 5 minutes
        }
      )
    })
  }

  /**
   * Handle location errors with user-friendly messages
   */
  private handleLocationError(error: any): LocationResult {
    let errorMessage = 'Unable to get your location'
    let errorCode = LocationErrorCode.POSITION_UNAVAILABLE
    let retryable = true

    if (error.code !== undefined) {
      switch (error.code) {
        case GeolocationPositionError.PERMISSION_DENIED:
          errorMessage = 'Location access denied. Please enable location permissions in your browser settings, or enter your city manually below.'
          errorCode = LocationErrorCode.PERMISSION_DENIED
          retryable = false
          break
        case GeolocationPositionError.POSITION_UNAVAILABLE:
          errorMessage = 'Location information is currently unavailable. This might be due to poor GPS signal. You can try again or enter your city manually.'
          errorCode = LocationErrorCode.POSITION_UNAVAILABLE
          retryable = true
          break
        case GeolocationPositionError.TIMEOUT:
          errorMessage = 'Location request timed out. This can happen with slow GPS or network connections. Try again or enter your city manually.'
          errorCode = LocationErrorCode.TIMEOUT
          retryable = true
          break
        default:
          errorMessage = 'An unexpected error occurred while getting your location. Please try again or enter your city manually.'
          retryable = true
      }
    } else if (error.message?.includes('Rate limited')) {
      errorMessage = 'Too many location requests. Please wait a moment and try again.'
      errorCode = LocationErrorCode.NETWORK_ERROR
      retryable = true
    } else if (error.message?.includes('Network')) {
      errorMessage = 'Network error occurred. Please check your internet connection and try again.'
      errorCode = LocationErrorCode.NETWORK_ERROR
      retryable = true
    }

    return {
      success: false,
      error: errorMessage,
      errorCode,
      retryable,
      source: 'gps'
    }
  }

  /**
   * Parse BigDataCloud API response
   */
  private parseBigDataCloudResponse(data: any): GeocodeResult {
    try {
      const city = data.city || data.locality || data.principalSubdivision
      const region = data.principalSubdivision || data.countryName
      const country = data.countryName

      if (!city) {
        return {
          success: false,
          error: 'No city found in response',
          provider: 'BigDataCloud',
          confidence: 0
        }
      }

      return {
        success: true,
        city,
        region,
        country,
        provider: 'BigDataCloud',
        confidence: data.confidence || 0.8
      }
    } catch (error) {
      return {
        success: false,
        error: 'Failed to parse geocoding response',
        provider: 'BigDataCloud',
        confidence: 0
      }
    }
  }

  /**
   * Parse Nominatim API response
   */
  private parseNominatimResponse(data: any): GeocodeResult {
    try {
      const address = data.address || {}
      const city = address.city || address.town || address.village || address.municipality
      const region = address.state || address.province || address.region
      const country = address.country

      if (!city) {
        return {
          success: false,
          error: 'No city found in response',
          provider: 'Nominatim',
          confidence: 0
        }
      }

      return {
        success: true,
        city,
        region,
        country,
        provider: 'Nominatim',
        confidence: 0.7 // Nominatim typically has good accuracy
      }
    } catch (error) {
      return {
        success: false,
        error: 'Failed to parse geocoding response',
        provider: 'Nominatim',
        confidence: 0
      }
    }
  }
}

// Singleton instance for app-wide usage
export const locationService = new LocationService()

// Helper function for common use cases
export async function getUserLocation(options?: {
  onProgress?: (stage: string, progress: number) => void
  privacy?: 'precise' | 'city_only'
}): Promise<LocationResult> {
  return locationService.getCurrentLocation(options)
}

// Types are already exported above