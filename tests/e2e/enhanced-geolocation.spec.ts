/**
 * Enhanced Geolocation E2E Tests
 * 
 * Comprehensive testing for the new LocationService and LocationCapture component
 * Focuses on timeout fixes, retry mechanisms, and improved user experience
 */

import { test, expect, Page, BrowserContext } from '@playwright/test'

// Test configuration
const TEST_CONFIG = {
  baseUrl: process.env.TEST_BASE_URL || 'http://localhost:3000',
  timeout: 30000,
}

test.describe('Enhanced Geolocation Tests', () => {
  let page: Page
  let context: BrowserContext

  test.beforeEach(async ({ browser }) => {
    context = await browser.newContext({
      viewport: { width: 1280, height: 720 },
      permissions: ['geolocation'],
      geolocation: { latitude: 37.7749, longitude: -122.4194 }, // San Francisco
    })
    page = await context.newPage()

    // Mock the enhanced reverse geocoding APIs
    await page.route('**/api.bigdatacloud.net/**', async route => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          city: 'San Francisco',
          locality: 'San Francisco',
          principalSubdivision: 'California',
          countryName: 'United States',
          confidence: 0.95
        })
      })
    })

    await page.route('**/nominatim.openstreetmap.org/**', async route => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          address: {
            city: 'San Francisco',
            state: 'California',
            country: 'United States'
          }
        })
      })
    })

    // Mock profile completion API
    await page.route('**/api/profile/complete', async route => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          success: true,
          message: 'Profile completed successfully'
        })
      })
    })
  })

  test.afterEach(async () => {
    await page.close()
    await context.close()
  })

  test('should handle location request with enhanced progress indicators', async () => {
    await page.goto('/profile-setup')

    // Fill required bio field first
    const bioField = page.locator('textarea[placeholder*="Share what makes you unique"]')
    await bioField.fill('I am a test user looking for enhanced location services testing.')

    // Should be in precise location mode by default
    await expect(page.locator('text=Share exact location')).toBeVisible()

    // Click location button
    const locationButton = page.locator('button:has-text("Use My Current Location")')
    await locationButton.click()

    // Should show multi-stage progress
    await expect(page.locator('text=Getting Location')).toBeVisible()
    
    // Progress bar should be visible
    await expect(page.locator('[role="progressbar"]')).toBeVisible()

    // Should eventually show success
    await expect(page.locator('text=Location Captured')).toBeVisible({ timeout: 10000 })
    await expect(page.locator('text=Detected: San Francisco')).toBeVisible()

    // Button should change to show captured location
    await expect(page.locator('text=Location captured • San Francisco')).toBeVisible()

    // Should show accuracy information
    await expect(page.locator('text=Location accuracy:')).toBeVisible()
  })

  test('should handle geolocation timeout with retry mechanism', async () => {
    await page.goto('/profile-setup')

    // Fill bio field
    const bioField = page.locator('textarea[placeholder*="Share what makes you unique"]')
    await bioField.fill('Testing timeout and retry functionality.')

    // Mock geolocation to timeout initially, then succeed on retry
    await page.addInitScript(() => {
      let attemptCount = 0
      const originalGetCurrentPosition = navigator.geolocation.getCurrentPosition
      
      navigator.geolocation.getCurrentPosition = function(success, error, options) {
        attemptCount++
        
        if (attemptCount === 1) {
          // First attempt times out
          setTimeout(() => {
            error({
              code: 3, // TIMEOUT
              message: 'The request to get user location timed out.'
            })
          }, 100)
        } else {
          // Retry succeeds
          setTimeout(() => {
            success({
              coords: {
                latitude: 37.7749,
                longitude: -122.4194,
                accuracy: 10
              },
              timestamp: Date.now()
            })
          }, 100)
        }
      }
    })

    // Click location button - should timeout first
    const locationButton = page.locator('button:has-text("Use My Current Location")')
    await locationButton.click()

    // Should show timeout error
    await expect(page.locator('text=Location Failed')).toBeVisible({ timeout: 5000 })
    await expect(page.locator('text=Location request timed out')).toBeVisible()

    // Should show retry and manual entry options
    await expect(page.locator('button:has-text("Try Again")')).toBeVisible()
    await expect(page.locator('button:has-text("Enter City Manually")')).toBeVisible()

    // Click retry - should succeed
    const retryButton = page.locator('button:has-text("Try Again")')
    await retryButton.click()

    // Should show retry attempt
    await expect(page.locator('text=Retrying... (Attempt 2)')).toBeVisible()

    // Should eventually succeed
    await expect(page.locator('text=Location Captured')).toBeVisible({ timeout: 10000 })
  })

  test('should handle permission denied with helpful guidance', async () => {
    await page.goto('/profile-setup')

    // Fill bio field
    const bioField = page.locator('textarea[placeholder*="Share what makes you unique"]')
    await bioField.fill('Testing permission denied scenario.')

    // Mock permission denied error
    await page.addInitScript(() => {
      navigator.geolocation.getCurrentPosition = function(success, error, options) {
        setTimeout(() => {
          error({
            code: 1, // PERMISSION_DENIED
            message: 'User denied the request for Geolocation.'
          })
        }, 100)
      }
    })

    // Click location button
    const locationButton = page.locator('button:has-text("Use My Current Location")')
    await locationButton.click()

    // Should show permission error
    await expect(page.locator('text=Location Failed')).toBeVisible()
    await expect(page.locator('text=Location access denied')).toBeVisible()

    // Should show detailed permission guidance
    await expect(page.locator('text=Location Permission Needed')).toBeVisible()
    await expect(page.locator('text=Click the location icon in your browser\'s address bar')).toBeVisible()

    // Should not show retry button (not retryable)
    await expect(page.locator('button:has-text("Try Again")')).not.toBeVisible()

    // Should automatically show manual entry option
    await expect(page.locator('input[placeholder*="Enter your city"]')).toBeVisible({ timeout: 3000 })
  })

  test('should fallback to manual city entry gracefully', async () => {
    await page.goto('/profile-setup')

    // Fill bio field
    const bioField = page.locator('textarea[placeholder*="Share what makes you unique"]')
    await bioField.fill('Testing manual fallback functionality.')

    // Mock repeated location failures
    await page.addInitScript(() => {
      navigator.geolocation.getCurrentPosition = function(success, error, options) {
        setTimeout(() => {
          error({
            code: 3, // TIMEOUT
            message: 'The request to get user location timed out.'
          })
        }, 100)
      }
    })

    // Try location request - should fail
    const locationButton = page.locator('button:has-text("Use My Current Location")')
    await locationButton.click()

    await expect(page.locator('text=Location Failed')).toBeVisible()

    // Click manual entry option
    const manualButton = page.locator('button:has-text("Enter City Manually")')
    await manualButton.click()

    // Manual city input should appear
    await expect(page.locator('input[placeholder*="Enter your city"]')).toBeVisible()

    // Enter city manually
    const cityInput = page.locator('input[placeholder*="Enter your city"]')
    await cityInput.fill('New York, NY')

    // Should be able to complete profile with manual city
    const submitButton = page.locator('button:has-text("Complete Profile")')
    await expect(submitButton).not.toBeDisabled()
    
    await submitButton.click()
    await expect(page).toHaveURL('/find-buddy', { timeout: 10000 })
  })

  test('should switch between privacy modes correctly', async () => {
    await page.goto('/profile-setup')

    // Fill bio field
    const bioField = page.locator('textarea[placeholder*="Share what makes you unique"]')
    await bioField.fill('Testing privacy mode switching.')

    // Should start in precise mode
    await expect(page.locator('text=Share exact location')).toBeVisible()
    await expect(page.locator('text=Precise')).toBeVisible()
    await expect(page.locator('button:has-text("Use My Current Location")')).toBeVisible()

    // Toggle to city-only mode
    const privacyToggle = page.locator('input[type="checkbox"]').first()
    await privacyToggle.click()

    // Should switch to city-only mode
    await expect(page.locator('text=City only')).toBeVisible()
    await expect(page.locator('text=Private')).toBeVisible()
    await expect(page.locator('input[placeholder*="Enter your city"]')).toBeVisible()

    // Enter city in city-only mode
    const cityInput = page.locator('input[placeholder*="Enter your city"]')
    await cityInput.fill('Boston, MA')

    // Toggle back to precise mode
    await privacyToggle.click()

    // Should switch back to precise mode
    await expect(page.locator('text=Share exact location')).toBeVisible()
    await expect(page.locator('button:has-text("Use My Current Location")')).toBeVisible()

    // Manual city input should be hidden
    await expect(page.locator('input[placeholder*="Enter your city"]')).not.toBeVisible()
  })

  test('should handle multiple geocoding provider fallback', async () => {
    await page.goto('/profile-setup')

    // Fill bio field
    const bioField = page.locator('textarea[placeholder*="Share what makes you unique"]')
    await bioField.fill('Testing geocoding provider fallback.')

    // Mock BigDataCloud to fail, Nominatim to succeed
    await page.route('**/api.bigdatacloud.net/**', async route => {
      await route.abort('failed')
    })

    // Click location button
    const locationButton = page.locator('button:has-text("Use My Current Location")')
    await locationButton.click()

    // Should eventually succeed with fallback provider
    await expect(page.locator('text=Location Captured')).toBeVisible({ timeout: 10000 })
    await expect(page.locator('text=Detected: San Francisco')).toBeVisible()
  })

  test('should cache location data properly', async () => {
    await page.goto('/profile-setup')

    // Fill bio field
    const bioField = page.locator('textarea[placeholder*="Share what makes you unique"]')
    await bioField.fill('Testing location caching functionality.')

    // Get location first time
    const locationButton = page.locator('button:has-text("Use My Current Location")')
    await locationButton.click()

    await expect(page.locator('text=Location Captured')).toBeVisible()

    // Refresh page to simulate return visit
    await page.reload()

    // Fill bio again
    const bioFieldAfterReload = page.locator('textarea[placeholder*="Share what makes you unique"]')
    await bioFieldAfterReload.fill('Testing cached location.')

    // Request location again - should be faster (cached)
    const locationButtonAfterReload = page.locator('button:has-text("Use My Current Location")')
    await locationButtonAfterReload.click()

    // Should show cached indicator or be very fast
    await expect(page.locator('text=Location Captured')).toBeVisible({ timeout: 2000 })
    // May show "(cached)" indicator if available
  })

  test('should handle rapid clicking gracefully', async () => {
    await page.goto('/profile-setup')

    // Fill bio field
    const bioField = page.locator('textarea[placeholder*="Share what makes you unique"]')
    await bioField.fill('Testing rapid clicking protection.')

    const locationButton = page.locator('button:has-text("Use My Current Location")')
    
    // Rapid clicks
    await locationButton.click()
    await locationButton.click()
    await locationButton.click()

    // Should only process one request
    await expect(page.locator('text=Getting Location')).toBeVisible()

    // Should eventually succeed
    await expect(page.locator('text=Location Captured')).toBeVisible({ timeout: 10000 })
  })

  test('should meet accessibility requirements', async () => {
    await page.goto('/profile-setup')

    // Check ARIA labels and roles
    await expect(page.locator('[role="checkbox"]')).toBeVisible() // Privacy toggle
    await expect(page.locator('button[aria-describedby]')).toBeVisible() // Location button with description

    // Check keyboard navigation
    await page.keyboard.press('Tab') // Navigate to first focusable element
    
    // Should be able to reach location controls
    const locationButton = page.locator('button:has-text("Use My Current Location")')
    await locationButton.focus()
    await expect(locationButton).toBeFocused()

    // Should be able to activate with keyboard
    await page.keyboard.press('Enter')
    await expect(page.locator('text=Getting Location')).toBeVisible()
  })

  test('should handle network connectivity issues', async () => {
    await page.goto('/profile-setup')

    // Fill bio field
    const bioField = page.locator('textarea[placeholder*="Share what makes you unique"]')
    await bioField.fill('Testing network connectivity issues.')

    // Mock network failure for geocoding
    await page.route('**/api.bigdatacloud.net/**', async route => {
      await route.abort('failed')
    })
    await page.route('**/nominatim.openstreetmap.org/**', async route => {
      await route.abort('failed')
    })

    // Click location button
    const locationButton = page.locator('button:has-text("Use My Current Location")')
    await locationButton.click()

    // Should still succeed with GPS coordinates even if geocoding fails
    await expect(page.locator('text=Location Captured')).toBeVisible({ timeout: 10000 })

    // Should not show city name since geocoding failed
    await expect(page.locator('text=Location captured • San Francisco')).not.toBeVisible()
    
    // Should show just "Location captured"
    await expect(page.locator('text=Location captured')).toBeVisible()
  })

  test('should handle browser compatibility issues', async () => {
    await page.goto('/profile-setup')

    // Mock unsupported browser
    await page.addInitScript(() => {
      delete navigator.geolocation
    })

    // Fill bio field
    const bioField = page.locator('textarea[placeholder*="Share what makes you unique"]')
    await bioField.fill('Testing browser compatibility.')

    // Click location button
    const locationButton = page.locator('button:has-text("Use My Current Location")')
    await locationButton.click()

    // Should show not supported error
    await expect(page.locator('text=Geolocation is not supported by this browser')).toBeVisible()

    // Should automatically show manual entry
    await expect(page.locator('input[placeholder*="Enter your city"]')).toBeVisible({ timeout: 2000 })
  })

  test('should complete full profile with enhanced location features', async () => {
    await page.goto('/profile-setup')

    // Fill bio
    const bioField = page.locator('textarea[placeholder*="Share what makes you unique"]')
    await bioField.fill('Testing complete profile flow with enhanced location services. I am excited to try the improved geolocation features!')

    // Get location using enhanced service
    const locationButton = page.locator('button:has-text("Use My Current Location")')
    await locationButton.click()

    // Wait for location capture with progress indicators
    await expect(page.locator('text=Getting Location')).toBeVisible()
    await expect(page.locator('[role="progressbar"]')).toBeVisible()
    await expect(page.locator('text=Location Captured')).toBeVisible({ timeout: 15000 })

    // Adjust travel radius
    const radiusSlider = page.locator('input[type="range"]')
    await radiusSlider.fill('30')
    await expect(page.locator('text=Travel Radius: 30 miles')).toBeVisible()

    // Submit profile
    const submitButton = page.locator('button:has-text("Complete Profile")')
    await expect(submitButton).not.toBeDisabled()
    await submitButton.click()

    // Should redirect successfully
    await expect(page).toHaveURL('/find-buddy', { timeout: 10000 })
  })
})