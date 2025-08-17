/**
 * Geolocation Mocking for WingmanMatch E2E Tests
 * 
 * Provides mock geolocation data and utilities for testing
 * location-based matching and privacy features
 */

import { Page, BrowserContext } from '@playwright/test'
import { GEO_TEST_DATA } from './test-data'

export interface MockLocation {
  latitude: number
  longitude: number
  accuracy?: number
  city?: string
  timestamp?: number
}

export interface GeolocationMockOptions {
  enableHighAccuracy?: boolean
  timeout?: number
  maximumAge?: number
  mockError?: GeolocationPositionError
}

export class GeolocationMocker {
  private static locationHistory: Map<string, MockLocation[]> = new Map()
  
  /**
   * Set mock geolocation for a browser context
   */
  static async setMockLocation(
    context: BrowserContext,
    location: MockLocation,
    options: GeolocationMockOptions = {}
  ): Promise<void> {
    const { enableHighAccuracy = true } = options
    
    await context.setGeolocation({
      latitude: location.latitude,
      longitude: location.longitude,
      accuracy: location.accuracy || (enableHighAccuracy ? 10 : 100)
    })
    
    console.log(`📍 Mock location set: ${location.latitude}, ${location.longitude} (${location.city || 'Unknown'})`)
  }
  
  /**
   * Mock geolocation API on a page level
   */
  static async mockGeolocationAPI(
    page: Page,
    location: MockLocation,
    options: GeolocationMockOptions = {}
  ): Promise<void> {
    const { enableHighAccuracy = true, timeout = 10000, maximumAge = 0, mockError } = options
    
    await page.addInitScript((mockData) => {
      const { location, enableHighAccuracy, timeout, maximumAge, mockError } = mockData
      
      // Override geolocation API
      Object.defineProperty(navigator, 'geolocation', {
        value: {
          getCurrentPosition: (successCallback: PositionCallback, errorCallback?: PositionErrorCallback, options?: PositionOptions) => {
            setTimeout(() => {
              if (mockError && errorCallback) {
                errorCallback(mockError)
                return
              }
              
              const position: GeolocationPosition = {
                coords: {
                  latitude: location.latitude,
                  longitude: location.longitude,
                  accuracy: location.accuracy || (enableHighAccuracy ? 10 : 100),
                  altitude: null,
                  altitudeAccuracy: null,
                  heading: null,
                  speed: null
                },
                timestamp: Date.now()
              }
              
              successCallback(position)
            }, 100) // Small delay to simulate API call
          },
          
          watchPosition: (successCallback: PositionCallback, errorCallback?: PositionErrorCallback, options?: PositionOptions) => {
            // For simplicity, just call getCurrentPosition once
            navigator.geolocation.getCurrentPosition(successCallback, errorCallback, options)
            return 1 // Return mock watch ID
          },
          
          clearWatch: (watchId: number) => {
            // Mock implementation - no actual clearing needed
          }
        },
        writable: true
      })
      
      // Add flag to indicate geolocation is mocked
      (window as any).__WINGMAN_GEOLOCATION_MOCKED = true
      (window as any).__WINGMAN_MOCK_LOCATION = location
    }, { location, enableHighAccuracy, timeout, maximumAge, mockError })
    
    console.log(`🌍 Geolocation API mocked on page: ${location.latitude}, ${location.longitude}`)
  }
  
  /**
   * Set location to San Francisco (default test location)
   */
  static async setSanFranciscoLocation(context: BrowserContext): Promise<void> {
    await this.setMockLocation(context, GEO_TEST_DATA.sanFrancisco)
  }
  
  /**
   * Set location to Oakland for match testing
   */
  static async setOaklandLocation(context: BrowserContext): Promise<void> {
    await this.setMockLocation(context, GEO_TEST_DATA.oakland)
  }
  
  /**
   * Set location to Berkeley for match testing
   */
  static async setBerkeleyLocation(context: BrowserContext): Promise<void> {
    await this.setMockLocation(context, GEO_TEST_DATA.berkeley)
  }
  
  /**
   * Set location to San Jose for distance testing
   */
  static async setSanJoseLocation(context: BrowserContext): Promise<void> {
    await this.setMockLocation(context, GEO_TEST_DATA.sanJose)
  }
  
  /**
   * Set invalid location for error testing
   */
  static async setInvalidLocation(context: BrowserContext): Promise<void> {
    await this.setMockLocation(context, GEO_TEST_DATA.invalid)
  }
  
  /**
   * Mock geolocation permission denied error
   */
  static async mockPermissionDenied(page: Page): Promise<void> {
    const error: GeolocationPositionError = {
      code: 1, // PERMISSION_DENIED
      message: 'User denied geolocation access',
      PERMISSION_DENIED: 1,
      POSITION_UNAVAILABLE: 2,
      TIMEOUT: 3
    }
    
    await this.mockGeolocationAPI(page, GEO_TEST_DATA.sanFrancisco, { mockError: error })
    console.log(`🚫 Geolocation permission denied mocked`)
  }
  
  /**
   * Mock geolocation timeout error
   */
  static async mockTimeout(page: Page): Promise<void> {
    const error: GeolocationPositionError = {
      code: 3, // TIMEOUT
      message: 'Geolocation request timed out',
      PERMISSION_DENIED: 1,
      POSITION_UNAVAILABLE: 2,
      TIMEOUT: 3
    }
    
    await this.mockGeolocationAPI(page, GEO_TEST_DATA.sanFrancisco, { mockError: error })
    console.log(`⏰ Geolocation timeout mocked`)
  }
  
  /**
   * Mock geolocation position unavailable error
   */
  static async mockPositionUnavailable(page: Page): Promise<void> {
    const error: GeolocationPositionError = {
      code: 2, // POSITION_UNAVAILABLE
      message: 'Position unavailable',
      PERMISSION_DENIED: 1,
      POSITION_UNAVAILABLE: 2,
      TIMEOUT: 3
    }
    
    await this.mockGeolocationAPI(page, GEO_TEST_DATA.sanFrancisco, { mockError: error })
    console.log(`📍 Geolocation position unavailable mocked`)
  }
  
  /**
   * Mock reverse geocoding API responses
   */
  static async mockReverseGeocoding(page: Page, cityName: string = 'San Francisco'): Promise<void> {
    // Mock BigDataCloud reverse geocoding API
    await page.route('**/api.bigdatacloud.net/**', async route => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          city: cityName,
          locality: cityName,
          principalSubdivision: 'California',
          countryCode: 'US',
          countryName: 'United States'
        })
      })
    })
    
    // Mock OpenStreetMap Nominatim API (fallback)
    await page.route('**/nominatim.openstreetmap.org/**', async route => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          address: {
            city: cityName,
            state: 'California',
            country: 'United States',
            country_code: 'us'
          },
          display_name: `${cityName}, California, United States`
        })
      })
    })
    
    console.log(`🗺️ Reverse geocoding mocked for: ${cityName}`)
  }
  
  /**
   * Track location changes for testing
   */
  static trackLocationChange(userId: string, location: MockLocation): void {
    if (!this.locationHistory.has(userId)) {
      this.locationHistory.set(userId, [])
    }
    
    this.locationHistory.get(userId)!.push({
      ...location,
      timestamp: Date.now()
    })
  }
  
  /**
   * Get location history for a user
   */
  static getLocationHistory(userId: string): MockLocation[] {
    return this.locationHistory.get(userId) || []
  }
  
  /**
   * Clear location history
   */
  static clearLocationHistory(): void {
    this.locationHistory.clear()
  }
  
  /**
   * Calculate distance between two mock locations
   */
  static calculateDistance(loc1: MockLocation, loc2: MockLocation): number {
    const R = 3959 // Earth's radius in miles
    const dLat = (loc2.latitude - loc1.latitude) * Math.PI / 180
    const dLon = (loc2.longitude - loc1.longitude) * Math.PI / 180
    
    const a = Math.sin(dLat/2) * Math.sin(dLat/2) +
              Math.cos(loc1.latitude * Math.PI / 180) * Math.cos(loc2.latitude * Math.PI / 180) *
              Math.sin(dLon/2) * Math.sin(dLon/2)
    
    const c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1-a))
    return R * c
  }
  
  /**
   * Create a sequence of location moves for testing
   */
  static async simulateLocationMovement(
    context: BrowserContext,
    locations: MockLocation[],
    intervalMs: number = 1000
  ): Promise<void> {
    for (let i = 0; i < locations.length; i++) {
      await this.setMockLocation(context, locations[i])
      
      if (i < locations.length - 1) {
        await new Promise(resolve => setTimeout(resolve, intervalMs))
      }
    }
    
    console.log(`🎬 Simulated movement through ${locations.length} locations`)
  }
  
  /**
   * Verify location-based matching works correctly
   */
  static async verifyLocationMatching(
    page: Page,
    userLocation: MockLocation,
    expectedMatches: MockLocation[],
    radiusMiles: number
  ): Promise<boolean> {
    console.log(`🎯 Verifying location matching within ${radiusMiles} miles`)
    
    let allWithinRadius = true
    
    for (const matchLocation of expectedMatches) {
      const distance = this.calculateDistance(userLocation, matchLocation)
      
      if (distance > radiusMiles) {
        console.warn(`❌ Match outside radius: ${distance.toFixed(1)} miles > ${radiusMiles} miles`)
        allWithinRadius = false
      } else {
        console.log(`✅ Match within radius: ${distance.toFixed(1)} miles`)
      }
    }
    
    return allWithinRadius
  }
  
  /**
   * Test geolocation privacy modes
   */
  static async testPrivacyModes(page: Page): Promise<void> {
    // Test precise location mode
    await this.mockGeolocationAPI(page, GEO_TEST_DATA.sanFrancisco)
    
    // Verify precise coordinates are used
    const preciseLocation = await page.evaluate(() => {
      return (window as any).__WINGMAN_MOCK_LOCATION
    })
    
    console.log(`🔒 Precise mode tested: ${preciseLocation.latitude}, ${preciseLocation.longitude}`)
    
    // Test city-only mode by mocking the reverseGeocoding
    await this.mockReverseGeocoding(page, 'San Francisco')
    console.log(`🏙️ City-only mode mocked`)
  }
}

// Convenience functions for common test scenarios
export async function setTestLocationSF(context: BrowserContext): Promise<void> {
  await GeolocationMocker.setSanFranciscoLocation(context)
}

export async function setTestLocationOakland(context: BrowserContext): Promise<void> {
  await GeolocationMocker.setOaklandLocation(context)
}

export async function mockLocationPermissionDenied(page: Page): Promise<void> {
  await GeolocationMocker.mockPermissionDenied(page)
}

export async function mockLocationTimeout(page: Page): Promise<void> {
  await GeolocationMocker.mockTimeout(page)
}

export async function setupLocationMocking(page: Page, location?: keyof typeof GEO_TEST_DATA): Promise<void> {
  const testLocation = location ? GEO_TEST_DATA[location] : GEO_TEST_DATA.sanFrancisco
  await GeolocationMocker.mockGeolocationAPI(page, testLocation)
  await GeolocationMocker.mockReverseGeocoding(page, testLocation.city)
}

export default {
  GeolocationMocker,
  setTestLocationSF,
  setTestLocationOakland,
  mockLocationPermissionDenied,
  mockLocationTimeout,
  setupLocationMocking
}