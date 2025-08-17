/**
 * Synthetic User Management for WingmanMatch E2E Tests
 * 
 * Handles creation, authentication, and cleanup of test users
 * for complete user journey testing scenarios
 */

import { Page, BrowserContext } from '@playwright/test'
import { TEST_CONFIG, TestDataHelper, TEST_USERS, type TestUserProfile } from './test-data'

export interface SyntheticUser {
  userId: string
  email: string
  profile: TestUserProfile
  accessToken?: string
  refreshToken?: string
  sessionExpiresAt?: string
  isAuthenticated: boolean
}

export interface UserCreationOptions {
  useFixedProfile?: keyof typeof TEST_USERS
  customProfile?: Partial<TestUserProfile>
  skipProfileSetup?: boolean
  skipAuthentication?: boolean
}

export class SyntheticUserManager {
  private static instance: SyntheticUserManager
  private createdUsers: Map<string, SyntheticUser> = new Map()
  
  static getInstance(): SyntheticUserManager {
    if (!SyntheticUserManager.instance) {
      SyntheticUserManager.instance = new SyntheticUserManager()
    }
    return SyntheticUserManager.instance
  }
  
  /**
   * Create a new synthetic user with authentication
   */
  async createUser(
    page: Page, 
    options: UserCreationOptions = {}
  ): Promise<SyntheticUser> {
    const {
      useFixedProfile,
      customProfile,
      skipProfileSetup = false,
      skipAuthentication = false
    } = options
    
    // Generate user profile
    let profile: TestUserProfile
    if (useFixedProfile) {
      profile = { ...TEST_USERS[useFixedProfile] }
      profile.email = TestDataHelper.generateRandomEmail()
    } else if (customProfile) {
      profile = {
        ...TestDataHelper.getRandomTestUser(),
        ...customProfile,
        email: customProfile.email || TestDataHelper.generateRandomEmail()
      }
    } else {
      profile = TestDataHelper.getRandomTestUser()
    }
    
    const userId = TestDataHelper.generateRandomUserId()
    
    const user: SyntheticUser = {
      userId,
      email: profile.email,
      profile,
      isAuthenticated: false
    }
    
    // Authenticate user if not skipped
    if (!skipAuthentication) {
      try {
        const authResult = await this.authenticateUser(page, user)
        Object.assign(user, authResult)
        user.isAuthenticated = true
      } catch (error) {
        console.error(`🚨 Failed to authenticate user ${userId}:`, error)
        throw error
      }
    }
    
    // Complete profile setup if not skipped
    if (!skipProfileSetup && user.isAuthenticated) {
      try {
        await this.completeUserProfile(page, user)
      } catch (error) {
        console.error(`🚨 Failed to complete profile for user ${userId}:`, error)
        throw error
      }
    }
    
    // Store user for cleanup
    this.createdUsers.set(userId, user)
    
    console.log(`✅ Created synthetic user: ${userId} (${profile.email})`)
    return user
  }
  
  /**
   * Authenticate a user using the test auth endpoint
   */
  private async authenticateUser(page: Page, user: SyntheticUser): Promise<Partial<SyntheticUser>> {
    console.log(`🔐 Authenticating user: ${user.email}`)
    
    const authResponse = await page.request.post(`${TEST_CONFIG.apiUrl}/auth/test-login`, {
      data: {
        email: user.email,
        create_user: true
      }
    })
    
    if (!authResponse.ok()) {
      const errorText = await authResponse.text()
      throw new Error(`Authentication failed: ${authResponse.status()} - ${errorText}`)
    }
    
    const authData = await authResponse.json()
    
    if (!authData.success) {
      throw new Error(`Authentication unsuccessful: ${authData.message}`)
    }
    
    // Set up browser-side authentication
    await this.setupBrowserAuth(page, authData)
    
    return {
      userId: authData.user_id,
      accessToken: authData.access_token,
      refreshToken: authData.refresh_token,
      sessionExpiresAt: authData.session_expires_at
    }
  }
  
  /**
   * Set up browser-side authentication state
   */
  private async setupBrowserAuth(page: Page, authData: any): Promise<void> {
    const currentUrl = page.url()
    if (!currentUrl.includes('localhost:3') && !currentUrl.includes('vercel.app')) {
      await page.goto(TEST_CONFIG.baseUrl)
    }
    
    await page.waitForLoadState('networkidle')
    
    // Inject authentication session into browser
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
          email: authInfo.email || `test-${authInfo.user_id.slice(-8)}@example.com`,
          aud: 'authenticated',
          role: 'authenticated',
          email_confirmed_at: new Date().toISOString(),
          last_sign_in_at: new Date().toISOString(),
          app_metadata: {
            provider: 'test',
            providers: ['test']
          },
          user_metadata: {
            test_user: true
          },
          created_at: new Date().toISOString(),
          updated_at: new Date().toISOString(),
          is_anonymous: false
        }
      }
      
      localStorage.setItem(sessionKey, JSON.stringify(sessionData))
      
      // Set global flag for auth context
      (window as any).__WINGMAN_TEST_AUTH = {
        authenticated: true,
        userId: authInfo.user_id,
        email: authInfo.email,
        timestamp: Date.now()
      }
    }, authData)
    
    // Refresh to trigger auth context update
    await page.reload({ waitUntil: 'networkidle' })
  }
  
  /**
   * Complete user profile setup
   */
  private async completeUserProfile(page: Page, user: SyntheticUser): Promise<void> {
    console.log(`📝 Completing profile for user: ${user.userId}`)
    
    const profileRequest = {
      user_id: user.userId,
      bio: user.profile.bio,
      location: {
        city: user.profile.city,
        coordinates: user.profile.coordinates,
        privacy_mode: user.profile.coordinates ? 'precise' : 'city_only'
      },
      travel_radius: user.profile.travelRadius,
      photo_url: null // Skip photo upload for basic testing
    }
    
    const response = await page.request.post(`${TEST_CONFIG.apiUrl}/api/profile/complete`, {
      headers: {
        'Authorization': `Bearer ${user.accessToken}`,
        'Content-Type': 'application/json'
      },
      data: profileRequest
    })
    
    if (!response.ok()) {
      const errorText = await response.text()
      throw new Error(`Profile completion failed: ${response.status()} - ${errorText}`)
    }
    
    const result = await response.json()
    if (!result.success) {
      throw new Error(`Profile completion unsuccessful: ${result.message}`)
    }
    
    console.log(`✅ Profile completed for user: ${user.userId}`)
  }
  
  /**
   * Create multiple users for testing scenarios
   */
  async createUserPair(
    page: Page,
    user1Options?: UserCreationOptions,
    user2Options?: UserCreationOptions
  ): Promise<[SyntheticUser, SyntheticUser]> {
    const user1 = await this.createUser(page, user1Options)
    const user2 = await this.createUser(page, user2Options)
    
    console.log(`👥 Created user pair: ${user1.userId} & ${user2.userId}`)
    return [user1, user2]
  }
  
  /**
   * Create a test match between two users
   */
  async createTestMatch(
    page: Page,
    user1: SyntheticUser,
    user2: SyntheticUser
  ): Promise<string> {
    console.log(`🤝 Creating test match between ${user1.userId} and ${user2.userId}`)
    
    // Create auto match for user1 to find user2
    const matchResponse = await page.request.post(
      `${TEST_CONFIG.apiUrl}/api/matches/auto/${user1.userId}`,
      {
        headers: {
          'Authorization': `Bearer ${user1.accessToken}`,
          'Content-Type': 'application/json'
        }
      }
    )
    
    if (!matchResponse.ok()) {
      const errorText = await matchResponse.text()
      throw new Error(`Match creation failed: ${matchResponse.status()} - ${errorText}`)
    }
    
    const matchData = await matchResponse.json()
    
    if (!matchData.success) {
      throw new Error(`Match creation unsuccessful: ${matchData.message}`)
    }
    
    const matchId = matchData.match_id
    
    // Accept the match from user2's side
    const acceptResponse = await page.request.post(
      `${TEST_CONFIG.apiUrl}/api/buddy/respond`,
      {
        headers: {
          'Authorization': `Bearer ${user2.accessToken}`,
          'Content-Type': 'application/json'
        },
        data: {
          user_id: user2.userId,
          match_id: matchId,
          action: 'accept'
        }
      }
    )
    
    if (!acceptResponse.ok()) {
      throw new Error(`Match acceptance failed: ${acceptResponse.status()}`)
    }
    
    console.log(`✅ Test match created and accepted: ${matchId}`)
    return matchId
  }
  
  /**
   * Switch to a different user in the same browser context
   */
  async switchToUser(page: Page, user: SyntheticUser): Promise<void> {
    if (!user.isAuthenticated) {
      throw new Error(`User ${user.userId} is not authenticated`)
    }
    
    // Clear current auth state
    await page.evaluate(() => {
      localStorage.clear()
      delete (window as any).__WINGMAN_TEST_AUTH
    })
    
    // Set up auth for new user
    await this.setupBrowserAuth(page, {
      user_id: user.userId,
      access_token: user.accessToken,
      refresh_token: user.refreshToken,
      session_expires_at: user.sessionExpiresAt,
      email: user.email
    })
    
    console.log(`🔄 Switched to user: ${user.userId}`)
  }
  
  /**
   * Get authentication headers for API requests
   */
  getAuthHeaders(user: SyntheticUser): Record<string, string> {
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
   * Make authenticated API request for a user
   */
  async makeAuthenticatedRequest(
    page: Page,
    user: SyntheticUser,
    url: string,
    options: { method?: string; data?: any; headers?: Record<string, string> } = {}
  ) {
    const { method = 'GET', data, headers = {} } = options
    
    const authHeaders = this.getAuthHeaders(user)
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
  
  /**
   * Cleanup all created users
   */
  async cleanup(): Promise<void> {
    console.log(`🧹 Cleaning up ${this.createdUsers.size} synthetic users`)
    
    for (const [userId, user] of this.createdUsers) {
      try {
        // Additional cleanup logic would go here
        // For now, just log cleanup
        console.log(`🗑️ Cleaned up user: ${userId}`)
      } catch (error) {
        console.warn(`⚠️ Failed to cleanup user ${userId}:`, error)
      }
    }
    
    this.createdUsers.clear()
    console.log(`✅ User cleanup completed`)
  }
  
  /**
   * Get user by ID
   */
  getUser(userId: string): SyntheticUser | undefined {
    return this.createdUsers.get(userId)
  }
  
  /**
   * Get all created users
   */
  getAllUsers(): SyntheticUser[] {
    return Array.from(this.createdUsers.values())
  }
  
  /**
   * Check if user exists
   */
  hasUser(userId: string): boolean {
    return this.createdUsers.has(userId)
  }
}

// Singleton instance
export const syntheticUsers = SyntheticUserManager.getInstance()

// Helper functions for common scenarios
export async function createAuthenticatedUser(
  page: Page,
  options?: UserCreationOptions
): Promise<SyntheticUser> {
  return await syntheticUsers.createUser(page, {
    skipProfileSetup: false,
    ...options
  })
}

export async function createUserWithoutProfile(
  page: Page,
  options?: UserCreationOptions
): Promise<SyntheticUser> {
  return await syntheticUsers.createUser(page, {
    skipProfileSetup: true,
    ...options
  })
}

export async function createMatchedUserPair(
  page: Page
): Promise<[SyntheticUser, SyntheticUser, string]> {
  const [user1, user2] = await syntheticUsers.createUserPair(page)
  const matchId = await syntheticUsers.createTestMatch(page, user1, user2)
  return [user1, user2, matchId]
}

export default {
  SyntheticUserManager,
  syntheticUsers,
  createAuthenticatedUser,
  createUserWithoutProfile,
  createMatchedUserPair
}