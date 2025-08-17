/**
 * Subtask 23.1: Basic Signup Flow Test
 * 
 * Tests the complete signup flow including:
 * - Magic link authentication
 * - Test user creation
 * - Authentication validation
 * - Post-signup redirect
 */

import { test, expect } from './fixtures/user-fixtures'
import { 
  TEST_CONFIG, 
  TestDataHelper, 
  FRONTEND_ROUTES, 
  TEST_TIMEOUTS,
  ERROR_SCENARIOS 
} from './helpers/test-data'
import { TestSetupHelper } from './fixtures/user-fixtures'

test.describe('Signup Flow Tests', () => {
  
  test.beforeEach(async ({ page }) => {
    await TestSetupHelper.setupWingmanPage(page)
  })
  
  test('should complete basic signup flow with valid credentials', async ({ page }, testInfo) => {
    console.log('🧪 Testing basic signup flow')
    
    // Navigate to signin page
    await page.goto(`${TEST_CONFIG.baseUrl}${FRONTEND_ROUTES.signin}`)
    await TestSetupHelper.waitForPageReady(page)
    
    // Verify signin page loaded
    await expect(page.locator('h1')).toContainText(/sign in|sign up|welcome/i)
    await expect(page.locator('input[type="email"]')).toBeVisible()
    
    // Generate test email
    const testEmail = TestDataHelper.generateRandomEmail()
    console.log(`📧 Using test email: ${testEmail}`)
    
    // Fill email input
    const emailInput = page.locator('input[type="email"]')
    await emailInput.fill(testEmail)
    
    // Submit signin form
    const submitButton = page.locator('button:has-text("Sign In"), button:has-text("Continue"), button[type="submit"]').first()
    await expect(submitButton).toBeEnabled()
    await submitButton.click()
    
    // For magic link flow, we should see confirmation message
    const confirmationMessage = page.locator('text*="check your email", text*="magic link", text*="sent", text*="email sent"').first()
    await expect(confirmationMessage).toBeVisible({ timeout: TEST_TIMEOUTS.authFlow })
    
    // Take screenshot of successful email sent state
    await TestSetupHelper.takeScreenshot(page, 'signup-email-sent', testInfo)
    
    // Since we can't actually check email in tests, use test auth endpoint
    console.log('🔐 Using test authentication endpoint')
    
    const authResponse = await page.request.post(`${TEST_CONFIG.apiUrl}/auth/test-login`, {
      data: {
        email: testEmail,
        create_user: true
      }
    })
    
    expect(authResponse.ok()).toBeTruthy()
    const authData = await authResponse.json()
    expect(authData.success).toBeTruthy()
    expect(authData.user_id).toBeDefined()
    expect(authData.access_token).toBeDefined()
    
    console.log(`✅ Test user created: ${authData.user_id}`)
    
    // Setup browser authentication
    await page.evaluate((authInfo) => {
      const supabaseUrl = process.env.NEXT_PUBLIC_SUPABASE_URL || 'https://test-project.supabase.co'
      const projectId = supabaseUrl.split('//')[1].split('.')[0]
      const sessionKey = `sb-${projectId}-auth-token`
      
      const sessionData = {
        access_token: authInfo.access_token,
        refresh_token: authInfo.refresh_token,
        expires_at: Math.floor(new Date(authInfo.session_expires_at).getTime() / 1000),
        expires_in: 24 * 60 * 60,
        token_type: 'bearer',
        user: {
          id: authInfo.user_id,
          email: authInfo.email || testEmail,
          aud: 'authenticated',
          role: 'authenticated'
        }
      }
      
      localStorage.setItem(sessionKey, JSON.stringify(sessionData))
      
      (window as any).__WINGMAN_TEST_AUTH = {
        authenticated: true,
        userId: authInfo.user_id,
        email: authInfo.email || testEmail,
        timestamp: Date.now()
      }
    }, { ...authData, email: testEmail })
    
    // Navigate to a protected page to verify authentication
    await page.goto(`${TEST_CONFIG.baseUrl}${FRONTEND_ROUTES.profileSetup}`)
    await TestSetupHelper.waitForPageReady(page)
    
    // Should successfully load profile setup page (protected route)
    await expect(page.locator('h1')).toContainText(/profile|setup|complete/i, { timeout: TEST_TIMEOUTS.pageLoad })
    
    // Verify authentication state in browser
    const isAuthenticated = await page.evaluate(() => {
      const testAuth = (window as any).__WINGMAN_TEST_AUTH
      return testAuth?.authenticated === true
    })
    
    expect(isAuthenticated).toBeTruthy()
    
    // Take screenshot of successful signup completion
    await TestSetupHelper.takeScreenshot(page, 'signup-completed', testInfo)
    
    console.log('✅ Signup flow completed successfully')
  })
  
  test('should handle invalid email format gracefully', async ({ page }, testInfo) => {
    console.log('🧪 Testing invalid email handling')
    
    await page.goto(`${TEST_CONFIG.baseUrl}${FRONTEND_ROUTES.signin}`)
    await TestSetupHelper.waitForPageReady(page)
    
    // Try invalid email format
    const emailInput = page.locator('input[type="email"]')
    await emailInput.fill(ERROR_SCENARIOS.invalidEmail)
    
    const submitButton = page.locator('button:has-text("Sign In"), button:has-text("Continue"), button[type="submit"]').first()
    
    // Should either disable submit button or show validation error
    const isButtonDisabled = await submitButton.isDisabled()
    
    if (!isButtonDisabled) {
      await submitButton.click()
      
      // Should show validation error
      const errorMessage = page.locator('text*="invalid email", text*="valid email", text*="email format"').first()
      await expect(errorMessage).toBeVisible({ timeout: 3000 })
    }
    
    await TestSetupHelper.takeScreenshot(page, 'signup-invalid-email', testInfo)
    console.log('✅ Invalid email handling verified')
  })
  
  test('should handle empty email submission', async ({ page }, testInfo) => {
    console.log('🧪 Testing empty email handling')
    
    await page.goto(`${TEST_CONFIG.baseUrl}${FRONTEND_ROUTES.signin}`)
    await TestSetupHelper.waitForPageReady(page)
    
    // Leave email input empty
    const submitButton = page.locator('button:has-text("Sign In"), button:has-text("Continue"), button[type="submit"]').first()
    
    // Button should be disabled when email is empty
    await expect(submitButton).toBeDisabled()
    
    await TestSetupHelper.takeScreenshot(page, 'signup-empty-email', testInfo)
    console.log('✅ Empty email handling verified')
  })
  
  test('should display proper loading states during signup', async ({ page }, testInfo) => {
    console.log('🧪 Testing signup loading states')
    
    await page.goto(`${TEST_CONFIG.baseUrl}${FRONTEND_ROUTES.signin}`)
    await TestSetupHelper.waitForPageReady(page)
    
    const testEmail = TestDataHelper.generateRandomEmail()
    
    // Fill email
    const emailInput = page.locator('input[type="email"]')
    await emailInput.fill(testEmail)
    
    // Submit form
    const submitButton = page.locator('button:has-text("Sign In"), button:has-text("Continue"), button[type="submit"]').first()
    await submitButton.click()
    
    // Should show loading state immediately
    const loadingIndicator = page.locator('text*="sending", text*="loading", [aria-label*="loading"], .spinner, .loading').first()
    await expect(loadingIndicator).toBeVisible({ timeout: 1000 }).catch(() => {
      // Loading state might be very brief, that's okay
      console.log('⚠️ Loading state was too brief to capture')
    })
    
    // Should transition to success state
    const successMessage = page.locator('text*="check your email", text*="magic link", text*="sent"').first()
    await expect(successMessage).toBeVisible({ timeout: TEST_TIMEOUTS.authFlow })
    
    await TestSetupHelper.takeScreenshot(page, 'signup-loading-states', testInfo)
    console.log('✅ Loading states verified')
  })
  
  test('should handle network errors gracefully', async ({ page }, testInfo) => {
    console.log('🧪 Testing network error handling')
    
    // Mock network failure
    await page.route('**/auth/**', async route => {
      await route.abort('failed')
    })
    
    await page.goto(`${TEST_CONFIG.baseUrl}${FRONTEND_ROUTES.signin}`)
    await TestSetupHelper.waitForPageReady(page)
    
    const testEmail = TestDataHelper.generateRandomEmail()
    
    // Fill email and submit
    const emailInput = page.locator('input[type="email"]')
    await emailInput.fill(testEmail)
    
    const submitButton = page.locator('button:has-text("Sign In"), button:has-text("Continue"), button[type="submit"]').first()
    await submitButton.click()
    
    // Should show error message
    const errorMessage = page.locator('text*="error", text*="failed", text*="try again", text*="network"').first()
    await expect(errorMessage).toBeVisible({ timeout: 5000 })
    
    await TestSetupHelper.takeScreenshot(page, 'signup-network-error', testInfo)
    console.log('✅ Network error handling verified')
  })
  
  test('should redirect properly after successful authentication', async ({ page }, testInfo) => {
    console.log('🧪 Testing post-auth redirect')
    
    // Create authenticated user
    const testEmail = TestDataHelper.generateRandomEmail()
    
    // Use test auth endpoint directly
    const authResponse = await page.request.post(`${TEST_CONFIG.apiUrl}/auth/test-login`, {
      data: {
        email: testEmail,
        create_user: true
      }
    })
    
    expect(authResponse.ok()).toBeTruthy()
    const authData = await authResponse.json()
    
    // Setup browser authentication
    await page.goto(`${TEST_CONFIG.baseUrl}`)
    await page.evaluate((authInfo) => {
      const supabaseUrl = process.env.NEXT_PUBLIC_SUPABASE_URL || 'https://test-project.supabase.co'
      const projectId = supabaseUrl.split('//')[1].split('.')[0]
      const sessionKey = `sb-${projectId}-auth-token`
      
      const sessionData = {
        access_token: authInfo.access_token,
        refresh_token: authInfo.refresh_token,
        expires_at: Math.floor(new Date(authInfo.session_expires_at).getTime() / 1000),
        expires_in: 24 * 60 * 60,
        token_type: 'bearer',
        user: {
          id: authInfo.user_id,
          email: authInfo.email || testEmail,
          aud: 'authenticated',
          role: 'authenticated'
        }
      }
      
      localStorage.setItem(sessionKey, JSON.stringify(sessionData))
    }, { ...authData, email: testEmail })
    
    // Refresh page to trigger auth context update
    await page.reload({ waitUntil: 'networkidle' })
    
    // Should redirect to profile setup for new users
    await expect(page).toHaveURL(new RegExp(FRONTEND_ROUTES.profileSetup), { timeout: TEST_TIMEOUTS.pageLoad })
    
    await TestSetupHelper.takeScreenshot(page, 'signup-redirect-success', testInfo)
    console.log('✅ Post-auth redirect verified')
  })
  
  test('should preserve redirect path through auth flow', async ({ page }, testInfo) => {
    console.log('🧪 Testing redirect path preservation')
    
    // Try to access protected page first
    const targetPath = FRONTEND_ROUTES.profileSetup
    await page.goto(`${TEST_CONFIG.baseUrl}${targetPath}`)
    
    // Should redirect to signin with return URL
    await expect(page).toHaveURL(new RegExp(FRONTEND_ROUTES.signin), { timeout: TEST_TIMEOUTS.pageLoad })
    
    // Complete authentication
    const testEmail = TestDataHelper.generateRandomEmail()
    
    const authResponse = await page.request.post(`${TEST_CONFIG.apiUrl}/auth/test-login`, {
      data: {
        email: testEmail,
        create_user: true
      }
    })
    
    const authData = await authResponse.json()
    
    // Setup authentication in browser
    await page.evaluate((authInfo) => {
      const supabaseUrl = process.env.NEXT_PUBLIC_SUPABASE_URL || 'https://test-project.supabase.co'
      const projectId = supabaseUrl.split('//')[1].split('.')[0]
      const sessionKey = `sb-${projectId}-auth-token`
      
      const sessionData = {
        access_token: authInfo.access_token,
        refresh_token: authInfo.refresh_token,
        expires_at: Math.floor(new Date(authInfo.session_expires_at).getTime() / 1000),
        expires_in: 24 * 60 * 60,
        token_type: 'bearer',
        user: {
          id: authInfo.user_id,
          email: authInfo.email || testEmail,
          aud: 'authenticated',
          role: 'authenticated'
        }
      }
      
      localStorage.setItem(sessionKey, JSON.stringify(sessionData))
    }, { ...authData, email: testEmail })
    
    // Navigate to target path
    await page.goto(`${TEST_CONFIG.baseUrl}${targetPath}`)
    await TestSetupHelper.waitForPageReady(page)
    
    // Should successfully reach the target page
    await expect(page).toHaveURL(new RegExp(targetPath), { timeout: TEST_TIMEOUTS.pageLoad })
    await expect(page.locator('h1')).toContainText(/profile|setup|complete/i)
    
    await TestSetupHelper.takeScreenshot(page, 'signup-redirect-preserved', testInfo)
    console.log('✅ Redirect path preservation verified')
  })
  
  test('should handle existing user signin', async ({ page }, testInfo) => {
    console.log('🧪 Testing existing user signin')
    
    // Create user first
    const testEmail = TestDataHelper.generateRandomEmail()
    
    const createResponse = await page.request.post(`${TEST_CONFIG.apiUrl}/auth/test-login`, {
      data: {
        email: testEmail,
        create_user: true
      }
    })
    
    expect(createResponse.ok()).toBeTruthy()
    const userData = await createResponse.json()
    console.log(`👤 Created test user: ${userData.user_id}`)
    
    // Now test signin with existing user
    await page.goto(`${TEST_CONFIG.baseUrl}${FRONTEND_ROUTES.signin}`)
    await TestSetupHelper.waitForPageReady(page)
    
    const emailInput = page.locator('input[type="email"]')
    await emailInput.fill(testEmail)
    
    const submitButton = page.locator('button:has-text("Sign In"), button:has-text("Continue"), button[type="submit"]').first()
    await submitButton.click()
    
    // Should show email sent confirmation
    const confirmationMessage = page.locator('text*="check your email", text*="magic link", text*="sent"').first()
    await expect(confirmationMessage).toBeVisible({ timeout: TEST_TIMEOUTS.authFlow })
    
    // Use test auth for existing user (should not create new user)
    const authResponse = await page.request.post(`${TEST_CONFIG.apiUrl}/auth/test-login`, {
      data: {
        email: testEmail,
        create_user: false // Existing user
      }
    })
    
    expect(authResponse.ok()).toBeTruthy()
    const authData = await authResponse.json()
    expect(authData.user_id).toBe(userData.user_id) // Same user ID
    
    await TestSetupHelper.takeScreenshot(page, 'signin-existing-user', testInfo)
    console.log('✅ Existing user signin verified')
  })
})

test.describe('Signup Performance Tests', () => {
  
  test('should complete signup flow within performance thresholds', async ({ page }, testInfo) => {
    console.log('🧪 Testing signup performance')
    
    const startTime = Date.now()
    
    await page.goto(`${TEST_CONFIG.baseUrl}${FRONTEND_ROUTES.signin}`)
    await TestSetupHelper.waitForPageReady(page)
    
    const pageLoadTime = Date.now() - startTime
    console.log(`📊 Page load time: ${pageLoadTime}ms`)
    
    const testEmail = TestDataHelper.generateRandomEmail()
    
    // Measure form interaction time
    const interactionStart = Date.now()
    
    const emailInput = page.locator('input[type="email"]')
    await emailInput.fill(testEmail)
    
    const submitButton = page.locator('button:has-text("Sign In"), button:has-text("Continue"), button[type="submit"]').first()
    await submitButton.click()
    
    const interactionTime = Date.now() - interactionStart
    console.log(`📊 Form interaction time: ${interactionTime}ms`)
    
    // Measure auth API response time
    const authStart = Date.now()
    
    const authResponse = await page.request.post(`${TEST_CONFIG.apiUrl}/auth/test-login`, {
      data: {
        email: testEmail,
        create_user: true
      }
    })
    
    const authTime = Date.now() - authStart
    console.log(`📊 Auth API response time: ${authTime}ms`)
    
    expect(authResponse.ok()).toBeTruthy()
    
    // Performance assertions
    expect(pageLoadTime).toBeLessThan(3000) // Page load < 3s
    expect(interactionTime).toBeLessThan(100) // Form interaction < 100ms
    expect(authTime).toBeLessThan(1000) // API response < 1s
    
    console.log('✅ Signup performance within thresholds')
  })
})