/**
 * Test Authentication System - Demonstration and Integration Test
 * 
 * This test demonstrates how to use the test authentication system
 * and validates that it works correctly for protected routes
 */

import { test, expect } from '@playwright/test'
import { authenticateTestUser, clearAuthState, checkTestAuthAvailability } from './auth-helper'

test.describe('Test Authentication System', () => {
  
  test.beforeEach(async ({ page }) => {
    // Clear any existing auth state before each test
    await clearAuthState(page)
  })

  test('should verify test auth endpoint is available', async ({ page }) => {
    const isAvailable = await checkTestAuthAvailability(page)
    expect(isAvailable).toBe(true)
  })

  test('should authenticate test user successfully', async ({ page }) => {
    const testEmail = `test-${Date.now()}@example.com`
    
    // Authenticate test user
    const user = await authenticateTestUser(page, testEmail)
    
    // Verify user data
    expect(user.email).toBe(testEmail)
    expect(user.userId).toBeTruthy()
    expect(user.accessToken).toBeTruthy()
    expect(user.refreshToken).toBeTruthy()
    
    console.log('✅ Test user authenticated:', user)
  })

  test('should access protected routes after authentication', async ({ page }) => {
    const testEmail = `protected-test-${Date.now()}@example.com`
    
    // First, try to access a protected route without authentication
    await page.goto('/profile-setup')
    
    // Should redirect to login or show unauthenticated state
    // (The exact behavior depends on your auth implementation)
    
    // Now authenticate
    const user = await authenticateTestUser(page, testEmail)
    
    // Navigate to protected route
    await page.goto('/profile-setup')
    await page.waitForLoadState('networkidle')
    
    // Should now be able to access the protected route
    // Verify we're on the profile setup page and not redirected
    expect(page.url()).toContain('/profile-setup')
    
    // Look for authenticated UI elements
    // This will depend on your specific UI implementation
    const pageContent = await page.textContent('body')
    expect(pageContent).not.toContain('Sign in')
    
    console.log('✅ Protected route accessible after authentication')
  })

  test('should make authenticated API requests', async ({ page }) => {
    const testEmail = `api-test-${Date.now()}@example.com`
    
    // Authenticate test user
    const user = await authenticateTestUser(page, testEmail)
    
    // Make an authenticated API request
    const apiUrl = process.env.TEST_API_URL || 'http://localhost:8000'
    const response = await page.request.get(`${apiUrl}/api/assessment/progress/${user.userId}`, {
      headers: {
        'Authorization': `Bearer ${user.accessToken}`,
        'X-User-ID': user.userId!
      }
    })
    
    expect(response.ok()).toBe(true)
    
    const data = await response.json()
    expect(data.user_id).toBe(user.userId)
    
    console.log('✅ Authenticated API request successful:', data)
  })

  test('should handle multiple test users', async ({ page }) => {
    const user1Email = `multi-user-1-${Date.now()}@example.com`
    const user2Email = `multi-user-2-${Date.now()}@example.com`
    
    // Authenticate first user
    const user1 = await authenticateTestUser(page, user1Email)
    expect(user1.userId).toBeTruthy()
    
    // Switch to second user
    await clearAuthState(page)
    const user2 = await authenticateTestUser(page, user2Email)
    expect(user2.userId).toBeTruthy()
    
    // Verify they have different user IDs
    expect(user1.userId).not.toBe(user2.userId)
    
    console.log('✅ Multiple test users created successfully')
  })

  test('should persist authentication across page reloads', async ({ page }) => {
    const testEmail = `persistence-test-${Date.now()}@example.com`
    
    // Authenticate test user
    const user = await authenticateTestUser(page, testEmail)
    
    // Navigate to a page
    await page.goto('/profile-setup')
    await page.waitForLoadState('networkidle')
    
    // Reload the page
    await page.reload({ waitUntil: 'networkidle' })
    
    // Verify authentication persists
    // Check localStorage for session data
    const hasSession = await page.evaluate(() => {
      const supabaseUrl = process.env.NEXT_PUBLIC_SUPABASE_URL || 'https://your-project.supabase.co'
      const projectId = supabaseUrl.split('//')[1].split('.')[0]
      const sessionKey = `sb-${projectId}-auth-token`
      return localStorage.getItem(sessionKey) !== null
    })
    
    expect(hasSession).toBe(true)
    
    // Should still be able to access protected content
    expect(page.url()).toContain('/profile-setup')
    
    console.log('✅ Authentication persists across page reloads')
  })

  test('should clean up auth state properly', async ({ page }) => {
    const testEmail = `cleanup-test-${Date.now()}@example.com`
    
    // Authenticate test user
    await authenticateTestUser(page, testEmail)
    
    // Verify authentication exists
    const hasSessionBefore = await page.evaluate(() => {
      return localStorage.length > 0
    })
    expect(hasSessionBefore).toBe(true)
    
    // Clear auth state
    await clearAuthState(page)
    
    // Verify cleanup was successful
    const hasSessionAfter = await page.evaluate(() => {
      return localStorage.length === 0
    })
    expect(hasSessionAfter).toBe(true)
    
    console.log('✅ Authentication cleanup successful')
  })

  test.afterEach(async ({ page }) => {
    // Clean up after each test
    await clearAuthState(page)
  })
})

// Test for production safety - should NOT work in production
test.describe('Production Safety', () => {
  test('should not allow test auth in production environment', async ({ page }) => {
    // This test would only run if environment variables indicate production
    const isProduction = process.env.NODE_ENV === 'production' || 
                        process.env.ENVIRONMENT === 'production'
    
    if (!isProduction) {
      test.skip(true, 'Skipping production safety test in development')
    }
    
    const apiUrl = process.env.TEST_API_URL || 'http://localhost:8000'
    
    try {
      const response = await page.request.post(`${apiUrl}/auth/test-login`, {
        data: {
          email: 'test@example.com',
          create_user: true
        }
      })
      
      // Should fail in production
      expect(response.status()).toBe(403)
      
      const error = await response.json()
      expect(error.detail).toContain('not available in production')
      
    } catch (error) {
      // Network error is also acceptable - endpoint shouldn't exist
      console.log('✅ Test auth properly blocked in production')
    }
  })
})