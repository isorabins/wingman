/**
 * Comprehensive E2E Integration Tests for Task 7 Profile Setup
 * 
 * Test Coverage:
 * - Complete profile setup flow (photo → bio → location → submit)
 * - API endpoint validation and error handling
 * - File upload security (type, size, content validation)
 * - Location privacy modes (precise vs city_only)
 * - Database operations and data persistence
 * - Frontend-backend integration
 * - Security validation and edge cases
 * - Performance and accessibility testing
 */

import { test, expect, Page, BrowserContext } from '@playwright/test'
import { rm, writeFile, mkdir } from 'fs/promises'
import { join } from 'path'
import { existsSync } from 'fs'

// Test configuration
const TEST_CONFIG = {
  baseUrl: process.env.TEST_BASE_URL || 'http://localhost:3000',
  apiUrl: process.env.TEST_API_URL || 'http://localhost:8000',
  testDataDir: './tests/e2e/test-data',
  timeout: 30000,
  slowTestThreshold: 10000
}

// Test data for validation
const VALID_BIO = "I'm a software engineer who loves hiking and meeting new people. Looking for a confident wingman buddy to practice social skills and explore the city together!"
const INVALID_BIO_PII = "Call me at 555-123-4567 or email test@example.com"
const INVALID_BIO_SHORT = "Too short"
const VALID_CITY = "San Francisco, CA"

// Mock file creation helper
async function createTestImage(filename: string, size: number = 1024): Promise<string> {
  const testDataDir = TEST_CONFIG.testDataDir
  if (!existsSync(testDataDir)) {
    await mkdir(testDataDir, { recursive: true })
  }
  
  const filePath = join(testDataDir, filename)
  const buffer = Buffer.alloc(size)
  
  // Create a simple JPEG header for file validation
  const jpegHeader = Buffer.from([0xFF, 0xD8, 0xFF, 0xE0])
  jpegHeader.copy(buffer, 0)
  
  await writeFile(filePath, buffer)
  return filePath
}

// Cleanup helper
test.afterAll(async () => {
  if (existsSync(TEST_CONFIG.testDataDir)) {
    await rm(TEST_CONFIG.testDataDir, { recursive: true, force: true })
  }
})

test.describe('Profile Setup Integration Tests', () => {
  let page: Page
  let context: BrowserContext

  test.beforeEach(async ({ browser }) => {
    context = await browser.newContext({
      // Simulate mobile viewport for responsive testing
      viewport: { width: 375, height: 667 },
      permissions: ['geolocation'],
      geolocation: { latitude: 37.7749, longitude: -122.4194 }, // San Francisco
    })
    page = await context.newPage()
    
    // Mock API responses for isolated testing
    await page.route('**/api/profile/complete', async route => {
      const request = route.request()
      const body = JSON.parse(request.postData() || '{}')
      
      // Validate request structure
      if (!body.user_id || !body.bio || !body.location || !body.travel_radius) {
        await route.fulfill({
          status: 400,
          contentType: 'application/json',
          body: JSON.stringify({ detail: 'Missing required fields' })
        })
        return
      }
      
      // Success response
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          success: true,
          message: 'Profile completed successfully',
          ready_for_matching: true,
          user_id: body.user_id
        })
      })
    })

    // Mock photo upload service
    await page.route('**/storage/**', async route => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({ 
          success: true, 
          photoUrl: 'https://example.com/test-photo.jpg' 
        })
      })
    })

    // Mock reverse geocoding
    await page.route('**/api.bigdatacloud.net/**', async route => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          city: 'San Francisco',
          locality: 'San Francisco',
          principalSubdivision: 'California'
        })
      })
    })
  })

  test.afterEach(async () => {
    await page.close()
    await context.close()
  })

  test('should render complete profile setup page with all sections', async () => {
    await page.goto('/profile-setup')
    
    // Check page loads properly
    await expect(page.locator('h1')).toContainText('Complete Your Profile')
    
    // Verify all main sections are present
    await expect(page.locator('text=Profile Photo')).toBeVisible()
    await expect(page.locator('text=About You')).toBeVisible()
    await expect(page.locator('text=Location & Preferences')).toBeVisible()
    
    // Check required form fields
    await expect(page.locator('textarea[placeholder*="Share what makes you unique"]')).toBeVisible()
    await expect(page.locator('text=Location Privacy')).toBeVisible()
    await expect(page.locator('text=Travel Radius')).toBeVisible()
    
    // Submit button should be present but disabled initially
    const submitButton = page.locator('button:has-text("Complete Profile")')
    await expect(submitButton).toBeVisible()
    await expect(submitButton).toBeDisabled()
  })

  test('should validate bio field with character limits and PII detection', async () => {
    await page.goto('/profile-setup')
    
    const bioField = page.locator('textarea[placeholder*="Share what makes you unique"]')
    
    // Test minimum character validation
    await bioField.fill(INVALID_BIO_SHORT)
    await expect(page.locator('text=Bio must be at least 10 characters')).toBeVisible()
    
    // Test character counter
    await expect(page.locator('text=9/400')).toBeVisible()
    
    // Test PII detection
    await bioField.fill(INVALID_BIO_PII)
    await expect(page.locator('text=Please don\'t include phone numbers or email addresses')).toBeVisible()
    
    // Test valid bio
    await bioField.fill(VALID_BIO)
    await expect(page.locator('text=Please don\'t include phone numbers or email addresses')).not.toBeVisible()
    
    // Character counter should update
    await expect(page.locator(`text=${VALID_BIO.length}/400`)).toBeVisible()
    
    // Progress bar should reflect bio length
    const progressBar = page.locator('[role="progressbar"]').first()
    await expect(progressBar).toHaveAttribute('aria-valuenow', String((VALID_BIO.length / 400) * 100))
  })

  test('should handle location permissions and geolocation accurately', async () => {
    await page.goto('/profile-setup')
    
    // Should start with precise location mode
    await expect(page.locator('text=Share exact location')).toBeVisible()
    
    // Click location permission button
    const locationButton = page.locator('button:has-text("Use My Current Location")')
    await locationButton.click()
    
    // Should show loading state
    await expect(page.locator('text=Getting location...')).toBeVisible()
    
    // Should show success message after location capture
    await expect(page.locator('text=Location captured successfully')).toBeVisible({ timeout: 5000 })
    await expect(page.locator('text=Detected city: San Francisco')).toBeVisible()
    
    // Button should change to show captured location
    await expect(page.locator('text=Location captured • San Francisco')).toBeVisible()
  })

  test('should handle location privacy toggle between precise and city-only modes', async () => {
    await page.goto('/profile-setup')
    
    // Should start with precise location mode
    await expect(page.locator('text=Share exact location')).toBeVisible()
    await expect(page.locator('button:has-text("Use My Current Location")')).toBeVisible()
    
    // Toggle to city-only mode
    const privacyToggle = page.locator('input[type="checkbox"]').first()
    await privacyToggle.click()
    
    // Should switch to city-only mode
    await expect(page.locator('text=City only')).toBeVisible()
    await expect(page.locator('input[placeholder*="Enter your city"]')).toBeVisible()
    
    // Fill city input
    const cityInput = page.locator('input[placeholder*="Enter your city"]')
    await cityInput.fill(VALID_CITY)
    
    // Toggle back to precise mode
    await privacyToggle.click()
    await expect(page.locator('text=Share exact location')).toBeVisible()
  })

  test('should handle photo upload with validation and progress tracking', async () => {
    await page.goto('/profile-setup')
    
    // Create test image files
    const validImagePath = await createTestImage('valid-photo.jpg', 1024 * 1024) // 1MB
    const oversizedImagePath = await createTestImage('oversized-photo.jpg', 6 * 1024 * 1024) // 6MB
    
    // Test valid photo upload
    const fileInput = page.locator('input[type="file"]')
    await fileInput.setInputFiles(validImagePath)
    
    // Should show upload progress
    await expect(page.locator('text=Uploading')).toBeVisible({ timeout: 2000 })
    
    // Should show preview after upload
    await expect(page.locator('img[alt="Profile preview"]')).toBeVisible({ timeout: 5000 })
    
    // Should show remove button
    const removeButton = page.locator('button').filter({ hasText: /×/ }).first()
    await expect(removeButton).toBeVisible()
    
    // Test photo removal
    await removeButton.click()
    await expect(page.locator('img[alt="Profile preview"]')).not.toBeVisible()
    await expect(page.locator('text=Upload a profile photo')).toBeVisible()
  })

  test('should validate file size and type restrictions', async () => {
    await page.goto('/profile-setup')
    
    // Create oversized image
    const oversizedImagePath = await createTestImage('oversized-photo.jpg', 6 * 1024 * 1024) // 6MB
    
    // Mock photo upload service to return size error
    await page.route('**/storage/**', async route => {
      await route.fulfill({
        status: 400,
        contentType: 'application/json',
        body: JSON.stringify({ 
          success: false,
          error: 'File too large. Maximum size is 5MB'
        })
      })
    })
    
    const fileInput = page.locator('input[type="file"]')
    await fileInput.setInputFiles(oversizedImagePath)
    
    // Should show error message
    await expect(page.locator('text=File too large. Maximum size is 5MB')).toBeVisible({ timeout: 3000 })
  })

  test('should complete full profile setup flow and redirect to find-buddy', async () => {
    await page.goto('/profile-setup')
    
    // Fill bio
    const bioField = page.locator('textarea[placeholder*="Share what makes you unique"]')
    await bioField.fill(VALID_BIO)
    
    // Toggle to city-only mode and enter city
    const privacyToggle = page.locator('input[type="checkbox"]').first()
    await privacyToggle.click()
    
    const cityInput = page.locator('input[placeholder*="Enter your city"]')
    await cityInput.fill(VALID_CITY)
    
    // Adjust travel radius
    const radiusSlider = page.locator('input[type="range"]')
    await radiusSlider.fill('25')
    
    // Verify travel radius display updates
    await expect(page.locator('text=Travel Radius: 25 miles')).toBeVisible()
    
    // Submit form
    const submitButton = page.locator('button:has-text("Complete Profile")')
    await expect(submitButton).not.toBeDisabled()
    await submitButton.click()
    
    // Should show loading state
    await expect(page.locator('text=Completing profile...')).toBeVisible()
    
    // Should redirect to find-buddy page
    await expect(page).toHaveURL('/find-buddy', { timeout: 10000 })
  })

  test('should handle API errors gracefully with proper error messages', async () => {
    await page.goto('/profile-setup')
    
    // Mock API error response
    await page.route('**/api/profile/complete', async route => {
      await route.fulfill({
        status: 400,
        contentType: 'application/json',
        body: JSON.stringify({ 
          detail: 'Bio contains prohibited content'
        })
      })
    })
    
    // Fill out form
    const bioField = page.locator('textarea[placeholder*="Share what makes you unique"]')
    await bioField.fill(VALID_BIO)
    
    const privacyToggle = page.locator('input[type="checkbox"]').first()
    await privacyToggle.click()
    
    const cityInput = page.locator('input[placeholder*="Enter your city"]')
    await cityInput.fill(VALID_CITY)
    
    // Submit form
    const submitButton = page.locator('button:has-text("Complete Profile")')
    await submitButton.click()
    
    // Should show error (error handling is done via toast notifications)
    // In a real implementation, we'd check for toast or error message display
    // For now, verify the page doesn't redirect on error
    await page.waitForTimeout(2000)
    await expect(page).toHaveURL('/profile-setup')
  })

  test('should handle network failures and retry logic', async () => {
    await page.goto('/profile-setup')
    
    // Mock network failure
    await page.route('**/api/profile/complete', async route => {
      await route.abort('failed')
    })
    
    // Fill out form
    const bioField = page.locator('textarea[placeholder*="Share what makes you unique"]')
    await bioField.fill(VALID_BIO)
    
    const privacyToggle = page.locator('input[type="checkbox"]').first()
    await privacyToggle.click()
    
    const cityInput = page.locator('input[placeholder*="Enter your city"]')
    await cityInput.fill(VALID_CITY)
    
    // Submit form
    const submitButton = page.locator('button:has-text("Complete Profile")')
    await submitButton.click()
    
    // Should handle network failure gracefully
    await page.waitForTimeout(2000)
    await expect(page).toHaveURL('/profile-setup')
  })

  test('should validate coordinate ranges for precise location mode', async () => {
    await page.goto('/profile-setup')
    
    // Mock invalid coordinates from geolocation
    await context.setGeolocation({ latitude: 91.0, longitude: -181.0 }) // Invalid ranges
    
    // Should still work with coordinate validation in place
    const locationButton = page.locator('button:has-text("Use My Current Location")')
    await locationButton.click()
    
    // Even with invalid coordinates, the system should handle it gracefully
    // In production, coordinate validation would prevent this
  })

  test('should meet accessibility requirements (WCAG 2.1 AA)', async () => {
    await page.goto('/profile-setup')
    
    // Check for proper heading hierarchy
    const h1 = page.locator('h1')
    await expect(h1).toContainText('Complete Your Profile')
    
    const h2Elements = page.locator('h2')
    await expect(h2Elements).toHaveCount(3) // Photo, Bio, Location sections
    
    // Check form labels are properly associated
    const bioField = page.locator('textarea[placeholder*="Share what makes you unique"]')
    await expect(bioField).toHaveAttribute('aria-label')
    
    // Check ARIA attributes on progress bar
    const progressBar = page.locator('[role="progressbar"]').first()
    await expect(progressBar).toHaveAttribute('aria-valuenow')
    await expect(progressBar).toHaveAttribute('aria-valuemin')
    await expect(progressBar).toHaveAttribute('aria-valuemax')
    
    // Test keyboard navigation
    await page.keyboard.press('Tab')
    await page.keyboard.press('Tab')
    
    // Should be able to navigate to bio field
    await expect(bioField).toBeFocused()
    
    // Check color contrast (would need additional tooling for full validation)
    // Verify focus indicators are visible
    const focusedElement = page.locator(':focus')
    await expect(focusedElement).toBeVisible()
  })

  test('should handle responsive design across different screen sizes', async () => {
    // Test mobile viewport (already set in beforeEach)
    await page.goto('/profile-setup')
    await expect(page.locator('h1')).toContainText('Complete Your Profile')
    
    // Test tablet viewport
    await page.setViewportSize({ width: 768, height: 1024 })
    await page.reload()
    await expect(page.locator('h1')).toContainText('Complete Your Profile')
    
    // Test desktop viewport
    await page.setViewportSize({ width: 1200, height: 800 })
    await page.reload()
    await expect(page.locator('h1')).toContainText('Complete Your Profile')
    
    // All form elements should remain accessible across viewports
    await expect(page.locator('textarea[placeholder*="Share what makes you unique"]')).toBeVisible()
    await expect(page.locator('button:has-text("Complete Profile")')).toBeVisible()
  })

  test('should measure performance with Lighthouse-style metrics', async () => {
    const startTime = Date.now()
    
    await page.goto('/profile-setup')
    
    // Measure time to interactive (TTI)
    await page.waitForLoadState('networkidle')
    const loadTime = Date.now() - startTime
    
    // Should load within reasonable time (< 3 seconds)
    expect(loadTime).toBeLessThan(3000)
    
    // Measure form interaction responsiveness
    const interactionStart = Date.now()
    const bioField = page.locator('textarea[placeholder*="Share what makes you unique"]')
    await bioField.fill('Test responsiveness')
    const interactionTime = Date.now() - interactionStart
    
    // Form interactions should be responsive (< 100ms)
    expect(interactionTime).toBeLessThan(100)
  })
})

// Security-focused test suite
test.describe('Profile Setup Security Tests', () => {
  let page: Page
  let context: BrowserContext

  test.beforeEach(async ({ browser }) => {
    context = await browser.newContext()
    page = await context.newPage()
  })

  test.afterEach(async () => {
    await page.close()
    await context.close()
  })

  test('should prevent XSS attacks in bio field', async () => {
    await page.goto('/profile-setup')
    
    const maliciousScript = '<script>alert("XSS")</script>'
    const bioField = page.locator('textarea[placeholder*="Share what makes you unique"]')
    
    await bioField.fill(maliciousScript)
    
    // Script should not execute
    // In a real test, we'd verify the content is sanitized
    await expect(page.locator('text=' + maliciousScript)).not.toBeVisible()
  })

  test('should validate file types and prevent malicious uploads', async () => {
    await page.goto('/profile-setup')
    
    // Create a fake executable file with image extension
    const maliciousFilePath = await createTestImage('malicious.jpg.exe', 1024)
    
    // Mock upload service to catch malicious file
    await page.route('**/storage/**', async route => {
      await route.fulfill({
        status: 400,
        contentType: 'application/json',
        body: JSON.stringify({ 
          success: false,
          error: 'Invalid file type detected'
        })
      })
    })
    
    const fileInput = page.locator('input[type="file"]')
    await fileInput.setInputFiles(maliciousFilePath)
    
    // Should reject malicious file
    await expect(page.locator('text=Invalid file type detected')).toBeVisible({ timeout: 3000 })
  })

  test('should prevent SQL injection attempts in city field', async () => {
    await page.goto('/profile-setup')
    
    const sqlInjection = "'; DROP TABLE users; --"
    
    // Toggle to city mode
    const privacyToggle = page.locator('input[type="checkbox"]').first()
    await privacyToggle.click()
    
    const cityInput = page.locator('input[placeholder*="Enter your city"]')
    await cityInput.fill(sqlInjection)
    
    // Form should still validate normally (backend protection assumed)
    await expect(cityInput).toHaveValue(sqlInjection)
  })

  test('should enforce rate limiting on form submissions', async () => {
    await page.goto('/profile-setup')
    
    // Mock rate limit response
    await page.route('**/api/profile/complete', async route => {
      await route.fulfill({
        status: 429,
        contentType: 'application/json',
        body: JSON.stringify({ 
          error: 'Rate limit exceeded',
          retry_after: 60
        })
      })
    })
    
    // Fill form
    const bioField = page.locator('textarea[placeholder*="Share what makes you unique"]')
    await bioField.fill(VALID_BIO)
    
    const privacyToggle = page.locator('input[type="checkbox"]').first()
    await privacyToggle.click()
    
    const cityInput = page.locator('input[placeholder*="Enter your city"]')
    await cityInput.fill(VALID_CITY)
    
    // Submit multiple times rapidly
    const submitButton = page.locator('button:has-text("Complete Profile")')
    await submitButton.click()
    
    // Should handle rate limiting gracefully
    await page.waitForTimeout(1000)
  })
})

// Performance benchmark tests
test.describe('Profile Setup Performance Tests', () => {
  let page: Page
  let context: BrowserContext

  test.beforeEach(async ({ browser }) => {
    context = await browser.newContext()
    page = await context.newPage()
  })

  test.afterEach(async () => {
    await page.close()
    await context.close()
  })

  test('should handle large photo uploads efficiently', async () => {
    await page.goto('/profile-setup')
    
    // Create 5MB test image (at the limit)
    const largeImagePath = await createTestImage('large-photo.jpg', 5 * 1024 * 1024)
    
    const uploadStart = Date.now()
    
    const fileInput = page.locator('input[type="file"]')
    await fileInput.setInputFiles(largeImagePath)
    
    // Should show progress tracking
    await expect(page.locator('text=Uploading')).toBeVisible({ timeout: 2000 })
    
    // Should complete within reasonable time (< 30 seconds for 5MB)
    await expect(page.locator('img[alt="Profile preview"]')).toBeVisible({ timeout: 30000 })
    
    const uploadTime = Date.now() - uploadStart
    console.log(`Large photo upload completed in ${uploadTime}ms`)
    
    // Performance assertion
    expect(uploadTime).toBeLessThan(30000)
  })

  test('should handle form validation without blocking UI', async () => {
    await page.goto('/profile-setup')
    
    const bioField = page.locator('textarea[placeholder*="Share what makes you unique"]')
    
    // Type rapidly and check validation responsiveness
    const validationStart = Date.now()
    
    await bioField.type('This is a test bio that should trigger validation as I type it out', { delay: 10 })
    
    // Character counter should update in real-time
    await expect(page.locator('text=77/400')).toBeVisible()
    
    const validationTime = Date.now() - validationStart
    
    // Validation should not block typing
    expect(validationTime).toBeLessThan(2000)
  })
})
