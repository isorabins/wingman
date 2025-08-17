/**
 * Subtask 23.2: Basic Profile Creation Test
 * 
 * Tests the complete profile setup flow including:
 * - Profile form completion
 * - Required fields validation
 * - Location services integration
 * - Profile submission and completion
 */

import { test, expect } from './fixtures/user-fixtures'
import { 
  TEST_CONFIG, 
  TestDataHelper, 
  FRONTEND_ROUTES, 
  TEST_TIMEOUTS,
  TEST_USERS,
  VALIDATION_PATTERNS,
  ERROR_SCENARIOS
} from './helpers/test-data'
import { TestSetupHelper } from './fixtures/user-fixtures'
import { setupLocationMocking } from './helpers/geolocation-mock'
import { createUserWithoutProfile } from './helpers/synthetic-users'

test.describe('Profile Creation Tests', () => {
  
  test.beforeEach(async ({ page }) => {
    await TestSetupHelper.setupWingmanPage(page)
    await setupLocationMocking(page, 'sanFrancisco')
  })
  
  test('should complete basic profile creation with required fields', async ({ page }, testInfo) => {
    console.log('🧪 Testing basic profile creation')
    
    // Create authenticated user without profile
    const user = await createUserWithoutProfile(page)
    console.log(`👤 Created user without profile: ${user.userId}`)
    
    // Navigate to profile setup
    await TestSetupHelper.navigateAuthenticated(page, user, FRONTEND_ROUTES.profileSetup)
    
    // Verify profile setup page loaded
    await expect(page.locator('h1')).toContainText(/profile|setup|complete/i)
    await expect(page.locator('textarea[placeholder*="about"], textarea[placeholder*="bio"], textarea[placeholder*="unique"]')).toBeVisible()
    
    // Fill bio field
    const bioField = page.locator('textarea[placeholder*="about"], textarea[placeholder*="bio"], textarea[placeholder*="unique"]').first()
    const testBio = TEST_USERS.alex.bio
    await bioField.fill(testBio)
    
    // Verify character counter
    await expect(page.locator(`text=${testBio.length}/400`)).toBeVisible()
    
    // Handle location setup (city-only mode)
    const privacyToggle = page.locator('input[type="checkbox"]').first()
    const isChecked = await privacyToggle.isChecked()
    
    if (!isChecked) {
      // Switch to city-only mode for simpler testing
      await privacyToggle.click()
    }
    
    // Fill city input
    const cityInput = page.locator('input[placeholder*="city"], input[placeholder*="location"]').first()
    await expect(cityInput).toBeVisible()
    await cityInput.fill(TEST_USERS.alex.city)
    
    // Set travel radius
    const radiusSlider = page.locator('input[type="range"]').first()
    await radiusSlider.fill(String(TEST_USERS.alex.travelRadius))
    
    // Verify travel radius display
    await expect(page.locator(`text*="${TEST_USERS.alex.travelRadius}"`)).toBeVisible()
    
    // Submit profile
    const submitButton = page.locator('button:has-text("Complete"), button:has-text("Submit"), button:has-text("Save")').first()
    await expect(submitButton).toBeEnabled()
    
    // Take screenshot before submission
    await TestSetupHelper.takeScreenshot(page, 'profile-before-submit', testInfo)
    
    await submitButton.click()
    
    // Should show loading state
    const loadingIndicator = page.locator('text*="completing", text*="saving", text*="loading", [aria-label*="loading"]').first()
    await expect(loadingIndicator).toBeVisible({ timeout: 2000 }).catch(() => {
      console.log('⚠️ Loading state was too brief to capture')
    })
    
    // Should redirect to next step or show success
    await expect(page).toHaveURL(new RegExp('find-buddy|matches|dashboard|success'), { timeout: TEST_TIMEOUTS.pageLoad })
    
    // Verify profile was created via API
    const profileResponse = await page.request.get(`${TEST_CONFIG.apiUrl}/api/profile/${user.userId}`, {
      headers: {
        'Authorization': `Bearer ${user.accessToken}`,
        'X-User-ID': user.userId
      }
    })
    
    if (profileResponse.ok()) {
      const profileData = await profileResponse.json()
      expect(profileData.bio).toBe(testBio)
      expect(profileData.travel_radius).toBe(TEST_USERS.alex.travelRadius)
      console.log('✅ Profile verified in database')
    }
    
    // Take screenshot of successful completion
    await TestSetupHelper.takeScreenshot(page, 'profile-completed', testInfo)
    
    console.log('✅ Profile creation completed successfully')
  })
  
  test('should validate bio field requirements', async ({ page }, testInfo) => {
    console.log('🧪 Testing bio field validation')
    
    const user = await createUserWithoutProfile(page)
    await TestSetupHelper.navigateAuthenticated(page, user, FRONTEND_ROUTES.profileSetup)
    
    const bioField = page.locator('textarea[placeholder*="about"], textarea[placeholder*="bio"], textarea[placeholder*="unique"]').first()
    
    // Test minimum length validation
    await bioField.fill(ERROR_SCENARIOS.shortBio)
    
    const minLengthError = page.locator('text*="too short", text*="at least", text*="minimum"').first()
    await expect(minLengthError).toBeVisible({ timeout: 3000 })
    
    // Test PII detection
    await bioField.fill(ERROR_SCENARIOS.bioWithPII)
    
    const piiError = page.locator('text*="phone", text*="email", text*="personal information", text*="contact"').first()
    await expect(piiError).toBeVisible({ timeout: 3000 })
    
    // Test valid bio clears errors
    await bioField.fill(TEST_USERS.alex.bio)
    
    await expect(minLengthError).not.toBeVisible()
    await expect(piiError).not.toBeVisible()
    
    // Verify character counter updates
    const charCount = TEST_USERS.alex.bio.length
    await expect(page.locator(`text=${charCount}/400`)).toBeVisible()
    
    await TestSetupHelper.takeScreenshot(page, 'bio-validation', testInfo)
    console.log('✅ Bio validation verified')
  })
  
  test('should handle location privacy modes correctly', async ({ page }, testInfo) => {
    console.log('🧪 Testing location privacy modes')
    
    const user = await createUserWithoutProfile(page)
    await TestSetupHelper.navigateAuthenticated(page, user, FRONTEND_ROUTES.profileSetup)
    
    // Fill bio first
    const bioField = page.locator('textarea[placeholder*="about"], textarea[placeholder*="bio"], textarea[placeholder*="unique"]').first()
    await bioField.fill(TEST_USERS.alex.bio)
    
    // Test precise location mode
    const privacyToggle = page.locator('input[type="checkbox"]').first()
    
    // Ensure we're in precise mode
    const isInCityMode = await privacyToggle.isChecked()
    if (isInCityMode) {
      await privacyToggle.click()
    }
    
    // Should show location permission button
    await expect(page.locator('text*="current location", text*="location permission", button:has-text("location")')).toBeVisible()
    
    // Switch to city-only mode
    await privacyToggle.click()
    
    // Should show city input
    const cityInput = page.locator('input[placeholder*="city"], input[placeholder*="location"]').first()
    await expect(cityInput).toBeVisible()
    await cityInput.fill(TEST_USERS.alex.city)
    
    // Switch back to precise mode
    await privacyToggle.click()
    
    // Should hide city input and show location button again
    await expect(cityInput).not.toBeVisible()
    await expect(page.locator('text*="current location", text*="location permission", button:has-text("location")')).toBeVisible()
    
    await TestSetupHelper.takeScreenshot(page, 'location-privacy-modes', testInfo)
    console.log('✅ Location privacy modes verified')
  })
  
  test('should handle travel radius configuration', async ({ page }, testInfo) => {
    console.log('🧪 Testing travel radius configuration')
    
    const user = await createUserWithoutProfile(page)
    await TestSetupHelper.navigateAuthenticated(page, user, FRONTEND_ROUTES.profileSetup)
    
    // Fill required fields
    const bioField = page.locator('textarea[placeholder*="about"], textarea[placeholder*="bio"], textarea[placeholder*="unique"]').first()
    await bioField.fill(TEST_USERS.alex.bio)
    
    // Switch to city mode for simpler testing
    const privacyToggle = page.locator('input[type="checkbox"]').first()
    if (!await privacyToggle.isChecked()) {
      await privacyToggle.click()
    }
    
    const cityInput = page.locator('input[placeholder*="city"], input[placeholder*="location"]').first()
    await cityInput.fill(TEST_USERS.alex.city)
    
    // Test radius slider
    const radiusSlider = page.locator('input[type="range"]').first()
    
    // Test minimum value
    await radiusSlider.fill('5')
    await expect(page.locator('text*="5 mile"')).toBeVisible()
    
    // Test maximum value
    await radiusSlider.fill('50')
    await expect(page.locator('text*="50 mile"')).toBeVisible()
    
    // Test mid-range value
    await radiusSlider.fill('25')
    await expect(page.locator('text*="25 mile"')).toBeVisible()
    
    await TestSetupHelper.takeScreenshot(page, 'travel-radius', testInfo)
    console.log('✅ Travel radius configuration verified')
  })
  
  test('should handle profile submission errors gracefully', async ({ page }, testInfo) => {
    console.log('🧪 Testing profile submission error handling')
    
    // Mock API error
    await page.route('**/api/profile/complete', async route => {
      await route.fulfill({
        status: 400,
        contentType: 'application/json',
        body: JSON.stringify({
          detail: 'Bio contains prohibited content'
        })
      })
    })
    
    const user = await createUserWithoutProfile(page)
    await TestSetupHelper.navigateAuthenticated(page, user, FRONTEND_ROUTES.profileSetup)
    
    // Fill form
    const bioField = page.locator('textarea[placeholder*="about"], textarea[placeholder*="bio"], textarea[placeholder*="unique"]').first()
    await bioField.fill(TEST_USERS.alex.bio)
    
    const privacyToggle = page.locator('input[type="checkbox"]').first()
    if (!await privacyToggle.isChecked()) {
      await privacyToggle.click()
    }
    
    const cityInput = page.locator('input[placeholder*="city"], input[placeholder*="location"]').first()
    await cityInput.fill(TEST_USERS.alex.city)
    
    // Submit form
    const submitButton = page.locator('button:has-text("Complete"), button:has-text("Submit"), button:has-text("Save")').first()
    await submitButton.click()
    
    // Should show error message
    const errorMessage = page.locator('text*="error", text*="failed", text*="prohibited", text*="try again"').first()
    await expect(errorMessage).toBeVisible({ timeout: 5000 })
    
    // Should remain on profile page
    await expect(page.locator('h1')).toContainText(/profile|setup|complete/i)
    
    await TestSetupHelper.takeScreenshot(page, 'profile-submission-error', testInfo)
    console.log('✅ Profile submission error handling verified')
  })
  
  test('should prevent submission with incomplete required fields', async ({ page }, testInfo) => {
    console.log('🧪 Testing incomplete field validation')
    
    const user = await createUserWithoutProfile(page)
    await TestSetupHelper.navigateAuthenticated(page, user, FRONTEND_ROUTES.profileSetup)
    
    // Submit button should be disabled initially
    const submitButton = page.locator('button:has-text("Complete"), button:has-text("Submit"), button:has-text("Save")').first()
    await expect(submitButton).toBeDisabled()
    
    // Fill bio only
    const bioField = page.locator('textarea[placeholder*="about"], textarea[placeholder*="bio"], textarea[placeholder*="unique"]').first()
    await bioField.fill(TEST_USERS.alex.bio)
    
    // Submit should still be disabled (missing location)
    await expect(submitButton).toBeDisabled()
    
    // Complete location setup
    const privacyToggle = page.locator('input[type="checkbox"]').first()
    if (!await privacyToggle.isChecked()) {
      await privacyToggle.click()
    }
    
    const cityInput = page.locator('input[placeholder*="city"], input[placeholder*="location"]').first()
    await cityInput.fill(TEST_USERS.alex.city)
    
    // Now submit should be enabled
    await expect(submitButton).toBeEnabled()
    
    await TestSetupHelper.takeScreenshot(page, 'profile-required-fields', testInfo)
    console.log('✅ Required field validation verified')
  })
  
  test('should handle bio character limit enforcement', async ({ page }, testInfo) => {
    console.log('🧪 Testing bio character limits')
    
    const user = await createUserWithoutProfile(page)
    await TestSetupHelper.navigateAuthenticated(page, user, FRONTEND_ROUTES.profileSetup)
    
    const bioField = page.locator('textarea[placeholder*="about"], textarea[placeholder*="bio"], textarea[placeholder*="unique"]').first()
    
    // Test maximum character limit
    const longBio = 'a'.repeat(400) // Exactly at limit
    await bioField.fill(longBio)
    
    // Verify character counter shows limit
    await expect(page.locator('text=400/400')).toBeVisible()
    
    // Try to exceed limit
    const exceedingBio = 'a'.repeat(450)
    await bioField.fill(exceedingBio)
    
    // Should be truncated to 400 characters
    const actualValue = await bioField.inputValue()
    expect(actualValue.length).toBe(400)
    
    await TestSetupHelper.takeScreenshot(page, 'bio-character-limit', testInfo)
    console.log('✅ Bio character limit enforcement verified')
  })
  
  test('should show profile completion progress', async ({ page }, testInfo) => {
    console.log('🧪 Testing profile completion progress')
    
    const user = await createUserWithoutProfile(page)
    await TestSetupHelper.navigateAuthenticated(page, user, FRONTEND_ROUTES.profileSetup)
    
    // Check initial progress (should be minimal)
    const progressBar = page.locator('[role="progressbar"], .progress, .completion').first()
    const initialProgress = await progressBar.getAttribute('aria-valuenow').catch(() => '0')
    
    // Fill bio
    const bioField = page.locator('textarea[placeholder*="about"], textarea[placeholder*="bio"], textarea[placeholder*="unique"]').first()
    await bioField.fill(TEST_USERS.alex.bio)
    
    // Progress should increase
    await page.waitForTimeout(500) // Allow progress to update
    const bioProgress = await progressBar.getAttribute('aria-valuenow').catch(() => '0')
    expect(Number(bioProgress)).toBeGreaterThan(Number(initialProgress))
    
    // Complete location
    const privacyToggle = page.locator('input[type="checkbox"]').first()
    if (!await privacyToggle.isChecked()) {
      await privacyToggle.click()
    }
    
    const cityInput = page.locator('input[placeholder*="city"], input[placeholder*="location"]').first()
    await cityInput.fill(TEST_USERS.alex.city)
    
    // Progress should increase further
    await page.waitForTimeout(500)
    const finalProgress = await progressBar.getAttribute('aria-valuenow').catch(() => '0')
    expect(Number(finalProgress)).toBeGreaterThan(Number(bioProgress))
    
    await TestSetupHelper.takeScreenshot(page, 'profile-progress', testInfo)
    console.log('✅ Profile completion progress verified')
  })
  
  test('should handle geolocation permission scenarios', async ({ page }, testInfo) => {
    console.log('🧪 Testing geolocation permission scenarios')
    
    const user = await createUserWithoutProfile(page)
    await TestSetupHelper.navigateAuthenticated(page, user, FRONTEND_ROUTES.profileSetup)
    
    // Fill bio first
    const bioField = page.locator('textarea[placeholder*="about"], textarea[placeholder*="bio"], textarea[placeholder*="unique"]').first()
    await bioField.fill(TEST_USERS.alex.bio)
    
    // Ensure we're in precise location mode
    const privacyToggle = page.locator('input[type="checkbox"]').first()
    if (await privacyToggle.isChecked()) {
      await privacyToggle.click()
    }
    
    // Click location permission button
    const locationButton = page.locator('button:has-text("location"), button:has-text("current"), button:has-text("permission")').first()
    await expect(locationButton).toBeVisible()
    await locationButton.click()
    
    // Should show loading state
    const loadingState = page.locator('text*="getting", text*="location", text*="detecting"').first()
    await expect(loadingState).toBeVisible({ timeout: 3000 })
    
    // Should show success with detected location
    const successState = page.locator('text*="captured", text*="detected", text*="San Francisco"').first()
    await expect(successState).toBeVisible({ timeout: 5000 })
    
    await TestSetupHelper.takeScreenshot(page, 'geolocation-permission', testInfo)
    console.log('✅ Geolocation permission handling verified')
  })
})

test.describe('Profile Creation Performance Tests', () => {
  
  test('should complete profile setup within performance thresholds', async ({ page }, testInfo) => {
    console.log('🧪 Testing profile creation performance')
    
    const user = await createUserWithoutProfile(page)
    
    const startTime = Date.now()
    await TestSetupHelper.navigateAuthenticated(page, user, FRONTEND_ROUTES.profileSetup)
    const pageLoadTime = Date.now() - startTime
    
    console.log(`📊 Profile page load time: ${pageLoadTime}ms`)
    
    // Measure form interaction responsiveness
    const interactionStart = Date.now()
    
    const bioField = page.locator('textarea[placeholder*="about"], textarea[placeholder*="bio"], textarea[placeholder*="unique"]').first()
    await bioField.fill(TEST_USERS.alex.bio)
    
    const privacyToggle = page.locator('input[type="checkbox"]').first()
    if (!await privacyToggle.isChecked()) {
      await privacyToggle.click()
    }
    
    const cityInput = page.locator('input[placeholder*="city"], input[placeholder*="location"]').first()
    await cityInput.fill(TEST_USERS.alex.city)
    
    const interactionTime = Date.now() - interactionStart
    console.log(`📊 Form interaction time: ${interactionTime}ms`)
    
    // Measure submission time
    const submitStart = Date.now()
    const submitButton = page.locator('button:has-text("Complete"), button:has-text("Submit"), button:has-text("Save")').first()
    await submitButton.click()
    
    // Wait for redirect or success
    await expect(page).toHaveURL(new RegExp('find-buddy|matches|dashboard|success'), { timeout: TEST_TIMEOUTS.pageLoad })
    
    const submitTime = Date.now() - submitStart
    console.log(`📊 Profile submission time: ${submitTime}ms`)
    
    // Performance assertions
    expect(pageLoadTime).toBeLessThan(3000) // Page load < 3s
    expect(interactionTime).toBeLessThan(200) // Form interaction < 200ms
    expect(submitTime).toBeLessThan(2000) // Submission < 2s
    
    console.log('✅ Profile creation performance within thresholds')
  })
})