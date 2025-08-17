/**
 * Test Suite for Enhanced LocationService
 * 
 * Comprehensive test coverage for:
 * - Geolocation API interactions
 * - Retry mechanisms and error handling
 * - Multiple geocoding provider fallbacks
 * - Location caching and validation
 * - Privacy controls and coordinate precision
 */

import { LocationService, LocationResult, GeocodeResult, LocationErrorCode } from '../locationService'

// Mock geolocation API
const mockGeolocation = {
  getCurrentPosition: jest.fn(),
  watchPosition: jest.fn(),
  clearWatch: jest.fn()
}

// Mock fetch
global.fetch = jest.fn()

Object.defineProperty(global.navigator, 'geolocation', {
  value: mockGeolocation,
  configurable: true
})

describe('LocationService', () => {
  let locationService: LocationService

  beforeEach(() => {
    // Reset all mocks
    jest.clearAllMocks()
    ;(fetch as jest.Mock).mockClear()
    
    // Create fresh instance for each test
    locationService = new LocationService({
      initialTimeout: 1000,
      retryTimeout: 2000,
      maxRetries: 2,
      cacheExpiry: 5000,
      enableCache: true
    })
  })

  describe('getCurrentLocation', () => {
    it('should successfully get location coordinates', async () => {
      const mockPosition = {
        coords: {
          latitude: 37.7749,
          longitude: -122.4194,
          accuracy: 10
        },
        timestamp: Date.now()
      }

      mockGeolocation.getCurrentPosition.mockImplementation((success: Function) => {
        setTimeout(() => success(mockPosition), 100)
      })

      // Mock successful geocoding
      ;(fetch as jest.Mock).mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve({
          city: 'San Francisco',
          locality: 'San Francisco',
          principalSubdivision: 'California'
        })
      })

      const result = await locationService.getCurrentLocation()

      expect(result.success).toBe(true)
      expect(result.coordinates).toEqual({
        lat: 37.7749,
        lng: -122.4194,
        accuracy: 10,
        timestamp: mockPosition.timestamp
      })
      expect(result.city).toBe('San Francisco')
      expect(result.source).toBe('gps')
    })

    it('should handle permission denied error', async () => {
      const mockError = {
        code: 1, // PERMISSION_DENIED
        message: 'User denied the request for Geolocation.'
      }

      mockGeolocation.getCurrentPosition.mockImplementation((_success: Function, error: Function) => {
        setTimeout(() => error(mockError), 100)
      })

      const result = await locationService.getCurrentLocation()

      expect(result.success).toBe(false)
      expect(result.errorCode).toBe(LocationErrorCode.PERMISSION_DENIED)
      expect(result.retryable).toBe(false)
      expect(result.error).toContain('Location access denied')
    })

    it('should handle timeout error with retry capability', async () => {
      const mockError = {
        code: 3, // TIMEOUT
        message: 'The request to get user location timed out.'
      }

      mockGeolocation.getCurrentPosition.mockImplementation((_success: Function, error: Function) => {
        setTimeout(() => error(mockError), 100)
      })

      const result = await locationService.getCurrentLocation()

      expect(result.success).toBe(false)
      expect(result.errorCode).toBe(LocationErrorCode.TIMEOUT)
      expect(result.retryable).toBe(true)
      expect(result.error).toContain('Location request timed out')
    })

    it('should handle position unavailable error', async () => {
      const mockError = {
        code: 2, // POSITION_UNAVAILABLE
        message: 'Location information is unavailable.'
      }

      mockGeolocation.getCurrentPosition.mockImplementation((_success: Function, error: Function) => {
        setTimeout(() => error(mockError), 100)
      })

      const result = await locationService.getCurrentLocation()

      expect(result.success).toBe(false)
      expect(result.errorCode).toBe(LocationErrorCode.POSITION_UNAVAILABLE)
      expect(result.retryable).toBe(true)
      expect(result.error).toContain('Location information is currently unavailable')
    })

    it('should return cached location when available', async () => {
      // First successful request
      const mockPosition = {
        coords: {
          latitude: 37.7749,
          longitude: -122.4194,
          accuracy: 10
        },
        timestamp: Date.now()
      }

      mockGeolocation.getCurrentPosition.mockImplementation((success: Function) => {
        setTimeout(() => success(mockPosition), 100)
      })

      ;(fetch as jest.Mock).mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve({
          city: 'San Francisco'
        })
      })

      const firstResult = await locationService.getCurrentLocation()
      expect(firstResult.success).toBe(true)
      expect(firstResult.source).toBe('gps')

      // Second request should use cache
      const secondResult = await locationService.getCurrentLocation()
      expect(secondResult.success).toBe(true)
      expect(secondResult.source).toBe('cache')
      expect(secondResult.coordinates).toEqual(firstResult.coordinates)
    })

    it('should handle progress callbacks', async () => {
      const mockPosition = {
        coords: {
          latitude: 37.7749,
          longitude: -122.4194,
          accuracy: 10
        },
        timestamp: Date.now()
      }

      mockGeolocation.getCurrentPosition.mockImplementation((success: Function) => {
        setTimeout(() => success(mockPosition), 100)
      })

      ;(fetch as jest.Mock).mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve({ city: 'San Francisco' })
      })

      const progressCallback = jest.fn()
      await locationService.getCurrentLocation({
        onProgress: progressCallback
      })

      expect(progressCallback).toHaveBeenCalledWith('permission', 10)
      expect(progressCallback).toHaveBeenCalledWith('acquiring', 30)
      expect(progressCallback).toHaveBeenCalledWith('acquired', 60)
      expect(progressCallback).toHaveBeenCalledWith('geocoding', 70)
      expect(progressCallback).toHaveBeenCalledWith('complete', 100)
    })

    it('should handle unsupported browser', async () => {
      // Temporarily remove geolocation support
      const originalGeolocation = global.navigator.geolocation
      delete (global.navigator as any).geolocation

      const result = await locationService.getCurrentLocation()

      expect(result.success).toBe(false)
      expect(result.errorCode).toBe(LocationErrorCode.NOT_SUPPORTED)
      expect(result.retryable).toBe(false)

      // Restore geolocation
      ;(global.navigator as any).geolocation = originalGeolocation
    })
  })

  describe('retryLocation', () => {
    it('should retry location request with exponential backoff', async () => {
      const mockPosition = {
        coords: {
          latitude: 37.7749,
          longitude: -122.4194,
          accuracy: 10
        },
        timestamp: Date.now()
      }

      // First attempt fails
      mockGeolocation.getCurrentPosition
        .mockImplementationOnce((_success: Function, error: Function) => {
          setTimeout(() => error({ code: 3, message: 'Timeout' }), 50)
        })
        // Retry succeeds
        .mockImplementationOnce((success: Function) => {
          setTimeout(() => success(mockPosition), 50)
        })

      ;(fetch as jest.Mock).mockResolvedValue({
        ok: true,
        json: () => Promise.resolve({ city: 'San Francisco' })
      })

      // First attempt
      const firstResult = await locationService.getCurrentLocation()
      expect(firstResult.success).toBe(false)

      // Retry should succeed
      const retryResult = await locationService.retryLocation()
      expect(retryResult.success).toBe(true)
      expect(retryResult.coordinates).toEqual({
        lat: 37.7749,
        lng: -122.4194,
        accuracy: 10,
        timestamp: mockPosition.timestamp
      })
    })

    it('should limit number of retry attempts', async () => {
      mockGeolocation.getCurrentPosition.mockImplementation((_success: Function, error: Function) => {
        setTimeout(() => error({ code: 3, message: 'Timeout' }), 50)
      })

      // First attempt fails
      await locationService.getCurrentLocation()

      // First retry fails
      await locationService.retryLocation()

      // Second retry fails
      await locationService.retryLocation()

      // Third retry should fail with max attempts reached
      const maxRetryResult = await locationService.retryLocation()
      expect(maxRetryResult.success).toBe(false)
      expect(maxRetryResult.retryable).toBe(false)
      expect(maxRetryResult.error).toContain('Maximum retry attempts reached')
    })
  })

  describe('reverseGeocode', () => {
    it('should successfully reverse geocode with BigDataCloud', async () => {
      ;(fetch as jest.Mock).mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve({
          city: 'San Francisco',
          locality: 'San Francisco',
          principalSubdivision: 'California',
          countryName: 'United States'
        })
      })

      const result = await locationService.reverseGeocode(37.7749, -122.4194)

      expect(result.success).toBe(true)
      expect(result.city).toBe('San Francisco')
      expect(result.provider).toBe('BigDataCloud')
    })

    it('should fallback to Nominatim when BigDataCloud fails', async () => {
      // BigDataCloud fails
      ;(fetch as jest.Mock).mockRejectedValueOnce(new Error('Network error'))

      // Nominatim succeeds
      ;(fetch as jest.Mock).mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve({
          address: {
            city: 'San Francisco',
            state: 'California',
            country: 'United States'
          }
        })
      })

      const result = await locationService.reverseGeocode(37.7749, -122.4194)

      expect(result.success).toBe(true)
      expect(result.city).toBe('San Francisco')
      expect(result.provider).toBe('Nominatim')
    })

    it('should fail when all providers fail', async () => {
      ;(fetch as jest.Mock).mockRejectedValue(new Error('Network error'))

      const result = await locationService.reverseGeocode(37.7749, -122.4194)

      expect(result.success).toBe(false)
      expect(result.error).toContain('All geocoding providers failed')
    })

    it('should validate coordinates before geocoding', async () => {
      const result = await locationService.reverseGeocode(91.0, -181.0) // Invalid coordinates

      expect(result.success).toBe(false)
      expect(result.error).toBe('Invalid coordinates provided')
      expect(result.provider).toBe('validation')
    })
  })

  describe('validateCoordinates', () => {
    it('should validate valid coordinates', () => {
      expect(locationService.validateCoordinates(37.7749, -122.4194)).toBe(true)
      expect(locationService.validateCoordinates(0, 0)).toBe(true)
      expect(locationService.validateCoordinates(-90, -180)).toBe(true)
      expect(locationService.validateCoordinates(90, 180)).toBe(true)
    })

    it('should reject invalid coordinates', () => {
      expect(locationService.validateCoordinates(91, 0)).toBe(false)
      expect(locationService.validateCoordinates(-91, 0)).toBe(false)
      expect(locationService.validateCoordinates(0, 181)).toBe(false)
      expect(locationService.validateCoordinates(0, -181)).toBe(false)
      expect(locationService.validateCoordinates(NaN, 0)).toBe(false)
      expect(locationService.validateCoordinates(0, NaN)).toBe(false)
    })
  })

  describe('caching', () => {
    it('should cache location data', async () => {
      const mockPosition = {
        coords: {
          latitude: 37.7749,
          longitude: -122.4194,
          accuracy: 10
        },
        timestamp: Date.now()
      }

      mockGeolocation.getCurrentPosition.mockImplementation((success: Function) => {
        setTimeout(() => success(mockPosition), 100)
      })

      ;(fetch as jest.Mock).mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve({ city: 'San Francisco' })
      })

      // First request
      const firstResult = await locationService.getCurrentLocation()
      expect(firstResult.source).toBe('gps')

      // Second request should use cache
      const secondResult = await locationService.getCurrentLocation()
      expect(secondResult.source).toBe('cache')
      expect(mockGeolocation.getCurrentPosition).toHaveBeenCalledTimes(1)
    })

    it('should expire cached data after cache expiry', async () => {
      // Create service with very short cache expiry
      const shortCacheService = new LocationService({ cacheExpiry: 100 })

      const mockPosition = {
        coords: {
          latitude: 37.7749,
          longitude: -122.4194,
          accuracy: 10
        },
        timestamp: Date.now()
      }

      mockGeolocation.getCurrentPosition.mockImplementation((success: Function) => {
        setTimeout(() => success(mockPosition), 50)
      })

      ;(fetch as jest.Mock).mockResolvedValue({
        ok: true,
        json: () => Promise.resolve({ city: 'San Francisco' })
      })

      // First request
      const firstResult = await shortCacheService.getCurrentLocation()
      expect(firstResult.source).toBe('gps')

      // Wait for cache to expire
      await new Promise(resolve => setTimeout(resolve, 200))

      // Second request should fetch fresh data
      const secondResult = await shortCacheService.getCurrentLocation()
      expect(secondResult.source).toBe('gps')
      expect(mockGeolocation.getCurrentPosition).toHaveBeenCalledTimes(2)
    })

    it('should clear cache when requested', async () => {
      const mockPosition = {
        coords: {
          latitude: 37.7749,
          longitude: -122.4194,
          accuracy: 10
        },
        timestamp: Date.now()
      }

      mockGeolocation.getCurrentPosition.mockImplementation((success: Function) => {
        setTimeout(() => success(mockPosition), 100)
      })

      ;(fetch as jest.Mock).mockResolvedValue({
        ok: true,
        json: () => Promise.resolve({ city: 'San Francisco' })
      })

      // First request
      await locationService.getCurrentLocation()

      // Clear cache
      locationService.clearCache()

      // Next request should not use cache
      const result = await locationService.getCurrentLocation()
      expect(result.source).toBe('gps')
      expect(mockGeolocation.getCurrentPosition).toHaveBeenCalledTimes(2)
    })
  })

  describe('error handling edge cases', () => {
    it('should handle rate limiting', async () => {
      // Make multiple rapid requests
      const promises = [
        locationService.getCurrentLocation(),
        locationService.getCurrentLocation(),
        locationService.getCurrentLocation()
      ]

      const results = await Promise.all(promises)

      // At least one should fail due to rate limiting
      const hasRateLimitError = results.some(result => 
        !result.success && result.error?.includes('Rate limited')
      )
      expect(hasRateLimitError).toBe(true)
    })

    it('should handle invalid coordinates from GPS', async () => {
      const mockPosition = {
        coords: {
          latitude: 999, // Invalid latitude
          longitude: -122.4194,
          accuracy: 10
        },
        timestamp: Date.now()
      }

      mockGeolocation.getCurrentPosition.mockImplementation((success: Function) => {
        setTimeout(() => success(mockPosition), 100)
      })

      const result = await locationService.getCurrentLocation()

      expect(result.success).toBe(false)
      expect(result.error).toContain('Invalid coordinates received from GPS')
    })

    it('should continue if geocoding fails but GPS succeeds', async () => {
      const mockPosition = {
        coords: {
          latitude: 37.7749,
          longitude: -122.4194,
          accuracy: 10
        },
        timestamp: Date.now()
      }

      mockGeolocation.getCurrentPosition.mockImplementation((success: Function) => {
        setTimeout(() => success(mockPosition), 100)
      })

      // All geocoding providers fail
      ;(fetch as jest.Mock).mockRejectedValue(new Error('Network error'))

      const result = await locationService.getCurrentLocation()

      // Should still succeed with coordinates even without city
      expect(result.success).toBe(true)
      expect(result.coordinates).toBeDefined()
      expect(result.city).toBeUndefined()
    })
  })
})

describe('getUserLocation helper function', () => {
  beforeEach(() => {
    jest.clearAllMocks()
  })

  it('should work as a standalone function', async () => {
    const mockPosition = {
      coords: {
        latitude: 37.7749,
        longitude: -122.4194,
        accuracy: 10
      },
      timestamp: Date.now()
    }

    mockGeolocation.getCurrentPosition.mockImplementation((success: Function) => {
      setTimeout(() => success(mockPosition), 100)
    })

    ;(fetch as jest.Mock).mockResolvedValueOnce({
      ok: true,
      json: () => Promise.resolve({ city: 'San Francisco' })
    })

    // Import the helper function
    const { getUserLocation } = require('../locationService')

    const result = await getUserLocation()
    expect(result.success).toBe(true)
    expect(result.coordinates).toBeDefined()
  })
})