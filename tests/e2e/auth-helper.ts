/**
 * Playwright Authentication Helper
 * 
 * Utilities for authenticating users in Playwright end-to-end tests
 * Works with the backend test authentication endpoint
 */

import { Page, BrowserContext } from '@playwright/test'

interface TestUser {
  email: string
  userId?: string
  accessToken?: string
  refreshToken?: string
}

interface AuthHelperOptions {
  apiUrl?: string
  createUser?: boolean
  skipAuthCheck?: boolean
}

/**
 * Authenticate a user in Playwright tests
 * This function handles both API-level and browser-level authentication
 * 
 * @param page - Playwright page object
 * @param email - Email address for test user
 * @param options - Additional authentication options
 * @returns Test user data with tokens
 */
export async function authenticateTestUser(
  page: Page, 
  email: string, 
  options: AuthHelperOptions = {}
): Promise<TestUser> {
  const {
    apiUrl = process.env.TEST_API_URL || 'http://localhost:8000',
    createUser = true,
    skipAuthCheck = false
  } = options

  console.log(`🧪 Playwright: Authenticating test user ${email}`)

  try {
    // Step 1: Call the backend test auth endpoint
    const authResponse = await page.request.post(`${apiUrl}/auth/test-login`, {
      data: {
        email,
        create_user: createUser
      }
    })

    if (!authResponse.ok()) {
      const errorText = await authResponse.text()
      throw new Error(`Test auth API failed: ${authResponse.status()} - ${errorText}`)
    }

    const authData = await authResponse.json()

    if (!authData.success) {
      throw new Error(`Test auth unsuccessful: ${authData.message}`)
    }

    console.log(`🧪 Playwright: API authentication successful for ${email}`)

    // Step 2: Set up browser-side authentication
    await setupBrowserAuth(page, authData)

    // Step 3: Verify authentication (optional)
    if (!skipAuthCheck) {
      await verifyAuthentication(page, authData.user_id)
    }

    console.log(`🧪 Playwright: Browser authentication complete for ${email}`)

    return {
      email,
      userId: authData.user_id,
      accessToken: authData.access_token,
      refreshToken: authData.refresh_token
    }

  } catch (error) {
    console.error(`🧪 Playwright: Authentication failed for ${email}:`, error)
    throw error
  }
}

/**
 * Set up browser-side authentication by injecting session data
 * This makes the frontend auth context recognize the user as authenticated
 */
async function setupBrowserAuth(page: Page, authData: any): Promise<void> {
  try {
    // Navigate to the app if not already there
    const currentUrl = page.url()
    if (!currentUrl.includes('localhost:3') && !currentUrl.includes('vercel.app')) {
      await page.goto(process.env.TEST_BASE_URL || 'http://localhost:3000')
    }

    // Wait for page to load
    await page.waitForLoadState('networkidle')

    // Inject authentication session into browser
    await page.evaluate((authInfo) => {
      // Set localStorage session data
      const supabaseUrl = process.env.NEXT_PUBLIC_SUPABASE_URL || 'https://your-project.supabase.co'
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
          email: authInfo.email || `test-${authInfo.user_id.slice(-8)}@example.com`,
          aud: 'authenticated',
          role: 'authenticated',
          email_confirmed_at: new Date().toISOString(),
          phone: '',
          last_sign_in_at: new Date().toISOString(),
          app_metadata: {
            provider: 'test',
            providers: ['test']
          },
          user_metadata: {
            test_user: true
          },
          identities: [],
          created_at: new Date().toISOString(),
          updated_at: new Date().toISOString(),
          is_anonymous: false
        }
      }

      localStorage.setItem(sessionKey, JSON.stringify(sessionData))

      // Set a global flag that auth context can detect
      (window as any).__WINGMAN_TEST_AUTH = {
        authenticated: true,
        userId: authInfo.user_id,
        email: authInfo.email,
        timestamp: Date.now()
      }

      console.log('🧪 Browser: Test session injected into localStorage')
    }, authData)

    // Refresh the page to trigger auth context update
    await page.reload({ waitUntil: 'networkidle' })

    console.log('🧪 Browser: Session data injected and page refreshed')

  } catch (error) {
    console.error('🧪 Browser: Error setting up browser auth:', error)
    throw error
  }
}

/**
 * Verify that authentication was successful by checking for authenticated UI elements
 */
async function verifyAuthentication(page: Page, expectedUserId: string): Promise<void> {
  try {
    // Wait for auth context to update (check for authenticated state)
    await page.waitForFunction(
      (userId) => {
        // Check localStorage for session
        const supabaseUrl = process.env.NEXT_PUBLIC_SUPABASE_URL || 'https://your-project.supabase.co'
        const projectId = supabaseUrl.split('//')[1].split('.')[0]
        const sessionKey = `sb-${projectId}-auth-token`
        const sessionData = localStorage.getItem(sessionKey)

        if (sessionData) {
          try {
            const session = JSON.parse(sessionData)
            return session.user?.id === userId
          } catch (e) {
            return false
          }
        }

        // Also check global test auth flag
        const testAuth = (window as any).__WINGMAN_TEST_AUTH
        return testAuth?.authenticated && testAuth.userId === userId
      },
      expectedUserId,
      { timeout: 10000 }
    )

    console.log('🧪 Playwright: Authentication verified successfully')

  } catch (error) {
    console.warn('🧪 Playwright: Could not verify authentication state:', error)
    // Don't throw - authentication might still work for API calls
  }
}

/**
 * Create multiple test users for complex test scenarios
 */
export async function createTestUsers(
  page: Page, 
  userEmails: string[], 
  options: AuthHelperOptions = {}
): Promise<TestUser[]> {
  const users: TestUser[] = []

  for (const email of userEmails) {
    const user = await authenticateTestUser(page, email, options)
    users.push(user)
  }

  return users
}

/**
 * Clear all authentication state for cleanup
 */
export async function clearAuthState(page: Page): Promise<void> {
  try {
    console.log('🧪 Playwright: Clearing authentication state')

    await page.evaluate(() => {
      // Clear all localStorage
      localStorage.clear()

      // Clear test auth globals
      delete (window as any).__WINGMAN_TEST_AUTH

      console.log('🧪 Browser: Authentication state cleared')
    })

    // Optionally navigate to a public page
    await page.goto(process.env.TEST_BASE_URL || 'http://localhost:3000')
    await page.waitForLoadState('networkidle')

    console.log('🧪 Playwright: Authentication cleanup complete')

  } catch (error) {
    console.error('🧪 Playwright: Error clearing auth state:', error)
    // Don't throw - cleanup should be forgiving
  }
}

/**
 * Switch to a different authenticated user in the same test
 */
export async function switchUser(page: Page, email: string, options: AuthHelperOptions = {}): Promise<TestUser> {
  // Clear current auth state
  await clearAuthState(page)
  
  // Authenticate as new user
  return await authenticateTestUser(page, email, options)
}

/**
 * Check if test authentication is available on the backend
 */
export async function checkTestAuthAvailability(page: Page): Promise<boolean> {
  try {
    const apiUrl = process.env.TEST_API_URL || 'http://localhost:8000'
    const response = await page.request.get(`${apiUrl}/config/features`)
    
    if (!response.ok()) return false
    
    const features = await response.json()
    return features.features?.test_auth_enabled === true
  } catch (error) {
    console.warn('🧪 Playwright: Could not check test auth availability:', error)
    return false
  }
}

/**
 * Get authentication headers for API requests in tests
 */
export function getAuthHeaders(user: TestUser): Record<string, string> {
  const headers: Record<string, string> = {}
  
  if (user.accessToken) {
    headers['Authorization'] = `Bearer ${user.accessToken}`
  }
  
  if (user.userId) {
    headers['X-User-ID'] = user.userId
  }
  
  return headers
}

/**
 * Utility to make authenticated API requests in tests
 */
export async function makeAuthenticatedRequest(
  page: Page,
  user: TestUser,
  url: string,
  options: { method?: string; data?: any; headers?: Record<string, string> } = {}
) {
  const { method = 'GET', data, headers = {} } = options
  
  const authHeaders = getAuthHeaders(user)
  const requestOptions: any = {
    headers: { ...authHeaders, ...headers }
  }
  
  if (data) {
    requestOptions.data = data
  }
  
  return await page.request.fetch(url, {
    method,
    ...requestOptions
  })
}

// Export types for TypeScript
export type { TestUser, AuthHelperOptions }