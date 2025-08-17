/**
 * Test Authentication Helper for Playwright Integration Tests
 * 
 * This module provides utilities for authenticating users in test environments
 * using the backend test authentication endpoint. Only works in development mode.
 */

import { supabase } from './supabase-client'

interface TestAuthResponse {
  success: boolean
  access_token: string
  refresh_token: string
  user_id: string
  session_expires_at: string
  message: string
}

interface TestAuthOptions {
  email: string
  createUser?: boolean
  apiUrl?: string
}

/**
 * Authenticate a test user via the backend test endpoint
 * This bypasses the normal magic link flow for fast test authentication
 * 
 * @param options - Test authentication options
 * @returns Promise with auth response data
 */
export async function testLogin(options: TestAuthOptions): Promise<TestAuthResponse> {
  const {
    email,
    createUser = true,
    apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'
  } = options

  console.log(`🧪 TEST AUTH: Attempting to authenticate ${email}`)

  try {
    // Call the backend test auth endpoint
    const response = await fetch(`${apiUrl}/auth/test-login`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        email,
        create_user: createUser
      })
    })

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}))
      throw new Error(`Test auth failed: ${response.status} - ${errorData.detail || 'Unknown error'}`)
    }

    const authData: TestAuthResponse = await response.json()

    if (!authData.success) {
      throw new Error(`Test auth unsuccessful: ${authData.message}`)
    }

    // Set the session in the Supabase client
    // This makes the frontend auth context recognize the user as authenticated
    await setTestSession(authData)

    console.log(`🧪 TEST AUTH: Successfully authenticated ${email} with user ID ${authData.user_id}`)
    
    return authData
  } catch (error) {
    console.error('🧪 TEST AUTH: Authentication failed:', error)
    throw error
  }
}

/**
 * Set a test session in the Supabase client
 * This updates the client state to recognize the user as authenticated
 * 
 * @param authData - Authentication response from test endpoint
 */
async function setTestSession(authData: TestAuthResponse): Promise<void> {
  try {
    // Create a mock session object that matches Supabase's session format
    const testSession = {
      access_token: authData.access_token,
      refresh_token: authData.refresh_token,
      expires_at: Math.floor(new Date(authData.session_expires_at).getTime() / 1000),
      expires_in: 24 * 60 * 60, // 24 hours in seconds
      token_type: 'bearer',
      user: {
        id: authData.user_id,
        email: extractEmailFromUserId(authData.user_id, email), // Use original email
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

    // Set the session in Supabase client
    const { data, error } = await supabase.auth.setSession({
      access_token: authData.access_token,
      refresh_token: authData.refresh_token
    })

    if (error) {
      console.warn('🧪 TEST AUTH: Warning setting Supabase session:', error)
      // Continue anyway - the session data is stored for API calls
    }

    // Also store in localStorage for persistence across page reloads
    if (typeof window !== 'undefined') {
      const sessionKey = `sb-${supabase.supabaseUrl.split('//')[1].split('.')[0]}-auth-token`
      localStorage.setItem(sessionKey, JSON.stringify(testSession))
    }

    console.log('🧪 TEST AUTH: Session set in Supabase client')
  } catch (error) {
    console.error('🧪 TEST AUTH: Error setting session:', error)
    throw error
  }
}

/**
 * Helper to extract email from user ID (fallback implementation)
 * In real implementation, this would be passed from the auth response
 */
function extractEmailFromUserId(userId: string, originalEmail?: string): string {
  // Use the original email if available, otherwise create a predictable format
  return originalEmail || `test-user-${userId.slice(-8)}@example.com`
}

/**
 * Clear test authentication session
 * Useful for cleanup after tests
 */
export async function testLogout(): Promise<void> {
  try {
    console.log('🧪 TEST AUTH: Clearing test session')
    
    // Sign out from Supabase client
    await supabase.auth.signOut()
    
    // Clear localStorage
    if (typeof window !== 'undefined') {
      const sessionKey = `sb-${supabase.supabaseUrl.split('//')[1].split('.')[0]}-auth-token`
      localStorage.removeItem(sessionKey)
    }
    
    console.log('🧪 TEST AUTH: Session cleared')
  } catch (error) {
    console.error('🧪 TEST AUTH: Error clearing session:', error)
    // Don't throw - logout should be forgiving
  }
}

/**
 * Check if test authentication is available
 * Returns true if the backend test auth endpoint is accessible
 */
export async function isTestAuthAvailable(apiUrl?: string): Promise<boolean> {
  const baseUrl = apiUrl || process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'
  
  try {
    const response = await fetch(`${baseUrl}/config/features`)
    if (!response.ok) return false
    
    const features = await response.json()
    return features.features?.test_auth_enabled === true
  } catch (error) {
    console.warn('🧪 TEST AUTH: Could not check test auth availability:', error)
    return false
  }
}

/**
 * Utility for Playwright tests to authenticate and wait for auth state
 * 
 * @param email - Email to authenticate
 * @param page - Playwright page object (optional, for browser context)
 */
export async function playwrightTestLogin(email: string, page?: any): Promise<TestAuthResponse> {
  const authData = await testLogin({ email })
  
  // If page is provided, wait for auth state change in browser
  if (page) {
    try {
      // Wait for auth context to update (max 5 seconds)
      await page.waitForFunction(
        () => {
          const authContext = (window as any).__WINGMAN_AUTH_CONTEXT
          return authContext?.user?.id || false
        },
        { timeout: 5000 }
      )
      console.log('🧪 TEST AUTH: Browser auth context updated')
    } catch (error) {
      console.warn('🧪 TEST AUTH: Auth context did not update in browser:', error)
      // Continue anyway - the session is still valid for API calls
    }
  }
  
  return authData
}

// Export types for TypeScript users
export type { TestAuthResponse, TestAuthOptions }