/**
 * User Fixtures for WingmanMatch E2E Tests
 * 
 * Provides test fixtures for user management, authentication,
 * and profile setup in isolated test environments
 */

import { test as base, Page, BrowserContext } from '@playwright/test'
import { syntheticUsers, SyntheticUser, UserCreationOptions } from '../helpers/synthetic-users'
import { GeolocationMocker, setupLocationMocking } from '../helpers/geolocation-mock'
import { TEST_CONFIG } from '../helpers/test-data'

// Extend Playwright test with custom fixtures
export interface WingmanTestFixtures {
  authenticatedUser: SyntheticUser
  userPair: [SyntheticUser, SyntheticUser]
  matchedUserPair: [SyntheticUser, SyntheticUser, string]
  userWithoutProfile: SyntheticUser
  pageWithLocation: Page
  contextWithLocation: BrowserContext
}

export const test = base.extend<WingmanTestFixtures>({
  /**
   * Fixture: Single authenticated user with completed profile
   */
  authenticatedUser: async ({ page }, use) => {
    console.log('🔧 Setting up authenticated user fixture')
    
    const user = await syntheticUsers.createUser(page, {
      skipProfileSetup: false
    })
    
    await use(user)
    
    // Cleanup handled by global teardown
    console.log('🧹 Authenticated user fixture cleaned up')
  },
  
  /**
   * Fixture: Pair of authenticated users with completed profiles
   */
  userPair: async ({ page }, use) => {
    console.log('🔧 Setting up user pair fixture')
    
    const [user1, user2] = await syntheticUsers.createUserPair(page, 
      { useFixedProfile: 'alex' },
      { useFixedProfile: 'jordan' }
    )
    
    await use([user1, user2])
    
    console.log('🧹 User pair fixture cleaned up')
  },
  
  /**
   * Fixture: Matched user pair with accepted match
   */
  matchedUserPair: async ({ page }, use) => {
    console.log('🔧 Setting up matched user pair fixture')
    
    const [user1, user2] = await syntheticUsers.createUserPair(page,
      { useFixedProfile: 'alex' },
      { useFixedProfile: 'jordan' }
    )
    
    const matchId = await syntheticUsers.createTestMatch(page, user1, user2)
    
    await use([user1, user2, matchId])
    
    console.log('🧹 Matched user pair fixture cleaned up')
  },
  
  /**
   * Fixture: Authenticated user without completed profile
   */
  userWithoutProfile: async ({ page }, use) => {
    console.log('🔧 Setting up user without profile fixture')
    
    const user = await syntheticUsers.createUser(page, {
      skipProfileSetup: true
    })
    
    await use(user)
    
    console.log('🧹 User without profile fixture cleaned up')
  },
  
  /**
   * Fixture: Page with mocked geolocation
   */
  pageWithLocation: async ({ page }, use) => {
    console.log('🔧 Setting up page with location fixture')
    
    await setupLocationMocking(page, 'sanFrancisco')
    
    await use(page)
    
    console.log('🧹 Page with location fixture cleaned up')
  },
  
  /**
   * Fixture: Browser context with mocked geolocation
   */
  contextWithLocation: async ({ browser }, use) => {
    console.log('🔧 Setting up context with location fixture')
    
    const context = await browser.newContext({
      permissions: ['geolocation'],
      geolocation: { latitude: 37.7749, longitude: -122.4194 }, // San Francisco
      viewport: { width: 1280, height: 720 }
    })
    
    await use(context)
    
    await context.close()
    console.log('🧹 Context with location fixture cleaned up')
  }
})

/**
 * Enhanced test function with automatic screenshot on failure
 */
export const testWithScreenshots = test.extend({
  page: async ({ page }, use, testInfo) => {
    // Setup
    await page.setViewportSize({ width: 1280, height: 720 })
    
    await use(page)
    
    // Cleanup - take screenshot on failure
    if (testInfo.status !== 'passed') {
      const screenshotPath = testInfo.outputPath('failure-screenshot.png')
      await page.screenshot({ 
        path: screenshotPath, 
        fullPage: true 
      })
      testInfo.attachments.push({
        name: 'failure-screenshot',
        path: screenshotPath,
        contentType: 'image/png'
      })
      console.log(`📸 Failure screenshot saved: ${screenshotPath}`)
    }
  }
})

/**
 * Worker-scoped fixture for global setup/teardown
 */
export const workerTest = base.extend<{}, { workerStorageState: string }>({
  workerStorageState: [async ({ browser }, use) => {
    console.log('🚀 Worker setup starting')
    
    // Setup worker-level state
    const context = await browser.newContext()
    const page = await context.newPage()
    
    // Initialize any worker-level data
    await page.goto(TEST_CONFIG.baseUrl)
    await page.waitForLoadState('networkidle')
    
    const storageState = await context.storageState()
    await context.close()
    
    await use('')
    
    // Worker cleanup
    console.log('🧹 Worker cleanup starting')
    await syntheticUsers.cleanup()
    GeolocationMocker.clearLocationHistory()
    console.log('✅ Worker cleanup completed')
  }, { scope: 'worker' }]
})

/**
 * Helper functions for test setup
 */
export class TestSetupHelper {
  
  /**
   * Setup page for WingmanMatch testing
   */
  static async setupWingmanPage(page: Page): Promise<void> {
    // Set reasonable viewport
    await page.setViewportSize({ width: 1280, height: 720 })
    
    // Mock geolocation
    await setupLocationMocking(page, 'sanFrancisco')
    
    // Mock external services that might be slow
    await this.mockExternalServices(page)
    
    // Navigate to base URL to establish session
    await page.goto(TEST_CONFIG.baseUrl)
    await page.waitForLoadState('networkidle')
  }
  
  /**
   * Mock external services for faster/more reliable testing
   */
  static async mockExternalServices(page: Page): Promise<void> {
    // Mock photo upload service (Supabase Storage)
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
    
    // Mock email service responses
    await page.route('**/resend.com/**', async route => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({ success: true })
      })
    })
    
    // Mock analytics/tracking
    await page.route('**/analytics/**', async route => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({ tracked: true })
      })
    })
  }
  
  /**
   * Wait for page to be ready for testing
   */
  static async waitForPageReady(page: Page): Promise<void> {
    // Wait for network to be idle
    await page.waitForLoadState('networkidle')
    
    // Wait for any React hydration to complete
    await page.waitForFunction(() => {
      return (window as any).React !== undefined || 
             document.readyState === 'complete'
    }, { timeout: 5000 }).catch(() => {
      // If React detection fails, just ensure DOM is ready
      console.log('⚠️ React detection timeout, proceeding with DOM ready state')
    })
    
    // Wait for any auth context to initialize
    await page.waitForTimeout(500)
  }
  
  /**
   * Setup test environment with authentication
   */
  static async setupAuthenticatedEnvironment(
    page: Page, 
    userOptions?: UserCreationOptions
  ): Promise<SyntheticUser> {
    await this.setupWingmanPage(page)
    
    const user = await syntheticUsers.createUser(page, {
      skipProfileSetup: false,
      ...userOptions
    })
    
    await this.waitForPageReady(page)
    
    return user
  }
  
  /**
   * Navigate to page with authentication check
   */
  static async navigateAuthenticated(
    page: Page, 
    user: SyntheticUser, 
    path: string
  ): Promise<void> {
    // Ensure user is authenticated in browser
    await syntheticUsers.switchToUser(page, user)
    
    // Navigate to target page
    await page.goto(`${TEST_CONFIG.baseUrl}${path}`)
    await this.waitForPageReady(page)
    
    // Verify authentication state
    await page.waitForFunction(
      () => {
        const auth = (window as any).__WINGMAN_TEST_AUTH
        return auth?.authenticated === true
      },
      { timeout: 5000 }
    ).catch(() => {
      console.warn('⚠️ Authentication verification timeout')
    })
  }
  
  /**
   * Take screenshot with test context
   */
  static async takeScreenshot(
    page: Page, 
    name: string,
    testInfo?: any
  ): Promise<string> {
    const timestamp = new Date().toISOString().replace(/[:.]/g, '-')
    const filename = `${name}-${timestamp}.png`
    
    const screenshotPath = testInfo 
      ? testInfo.outputPath(filename)
      : `./test-results/${filename}`
    
    await page.screenshot({ 
      path: screenshotPath, 
      fullPage: true 
    })
    
    if (testInfo) {
      testInfo.attachments.push({
        name,
        path: screenshotPath,
        contentType: 'image/png'
      })
    }
    
    console.log(`📸 Screenshot saved: ${screenshotPath}`)
    return screenshotPath
  }
}

// Export the enhanced test
export { expect } from '@playwright/test'
export default test