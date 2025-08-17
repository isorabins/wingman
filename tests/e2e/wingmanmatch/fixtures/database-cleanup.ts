/**
 * Database Cleanup Utilities for WingmanMatch E2E Tests
 * 
 * Provides utilities for cleaning up test data and maintaining
 * database isolation between test runs
 */

import { Page } from '@playwright/test'
import { TEST_CONFIG, TestDataHelper } from '../helpers/test-data'

export interface CleanupTarget {
  userId?: string
  email?: string
  matchId?: string
  sessionId?: string
  cleanup_type: 'user' | 'match' | 'session' | 'all'
}

export interface CleanupResult {
  success: boolean
  cleaned_items: number
  errors: string[]
  timestamp: string
}

export class DatabaseCleaner {
  private static cleanupQueue: CleanupTarget[] = []
  private static isCleanupRunning = false
  
  /**
   * Add cleanup target to queue
   */
  static addCleanupTarget(target: CleanupTarget): void {
    this.cleanupQueue.push({
      ...target,
      cleanup_type: target.cleanup_type
    })
    console.log(`🗑️ Added cleanup target: ${target.cleanup_type} - ${target.userId || target.email || target.matchId}`)
  }
  
  /**
   * Cleanup a specific user and all related data
   */
  static async cleanupUser(page: Page, userId: string): Promise<CleanupResult> {
    console.log(`🧹 Starting cleanup for user: ${userId}`)
    
    const result: CleanupResult = {
      success: true,
      cleaned_items: 0,
      errors: [],
      timestamp: new Date().toISOString()
    }
    
    try {
      // Clean user profile
      await this.cleanupUserProfile(page, userId, result)
      
      // Clean user matches
      await this.cleanupUserMatches(page, userId, result)
      
      // Clean user chat messages
      await this.cleanupUserChatMessages(page, userId, result)
      
      // Clean user sessions
      await this.cleanupUserSessions(page, userId, result)
      
      // Clean user location data
      await this.cleanupUserLocation(page, userId, result)
      
      // Finally, remove the user record
      await this.cleanupUserRecord(page, userId, result)
      
      console.log(`✅ User cleanup completed: ${userId} (${result.cleaned_items} items)`)
      
    } catch (error) {
      result.success = false
      result.errors.push(`User cleanup failed: ${error}`)
      console.error(`❌ User cleanup failed for ${userId}:`, error)
    }
    
    return result
  }
  
  /**
   * Cleanup user profile data
   */
  private static async cleanupUserProfile(
    page: Page, 
    userId: string, 
    result: CleanupResult
  ): Promise<void> {
    try {
      // Delete from user_profiles table
      const response = await page.request.delete(
        `${TEST_CONFIG.apiUrl}/test/cleanup/user-profile/${userId}`,
        {
          headers: {
            'X-Test-Cleanup': 'true',
            'Content-Type': 'application/json'
          }
        }
      )
      
      if (response.ok()) {
        result.cleaned_items++
        console.log(`🗑️ Cleaned user profile: ${userId}`)
      } else {
        result.errors.push(`Failed to clean user profile: ${response.status()}`)
      }
    } catch (error) {
      result.errors.push(`User profile cleanup error: ${error}`)
    }
  }
  
  /**
   * Cleanup user matches
   */
  private static async cleanupUserMatches(
    page: Page, 
    userId: string, 
    result: CleanupResult
  ): Promise<void> {
    try {
      // Delete from wingman_matches table
      const response = await page.request.delete(
        `${TEST_CONFIG.apiUrl}/test/cleanup/user-matches/${userId}`,
        {
          headers: {
            'X-Test-Cleanup': 'true',
            'Content-Type': 'application/json'
          }
        }
      )
      
      if (response.ok()) {
        const data = await response.json()
        result.cleaned_items += data.matches_deleted || 0
        console.log(`🗑️ Cleaned user matches: ${userId} (${data.matches_deleted} matches)`)
      } else {
        result.errors.push(`Failed to clean user matches: ${response.status()}`)
      }
    } catch (error) {
      result.errors.push(`User matches cleanup error: ${error}`)
    }
  }
  
  /**
   * Cleanup user chat messages
   */
  private static async cleanupUserChatMessages(
    page: Page, 
    userId: string, 
    result: CleanupResult
  ): Promise<void> {
    try {
      // Delete from chat_messages table
      const response = await page.request.delete(
        `${TEST_CONFIG.apiUrl}/test/cleanup/user-messages/${userId}`,
        {
          headers: {
            'X-Test-Cleanup': 'true',
            'Content-Type': 'application/json'
          }
        }
      )
      
      if (response.ok()) {
        const data = await response.json()
        result.cleaned_items += data.messages_deleted || 0
        console.log(`🗑️ Cleaned user messages: ${userId} (${data.messages_deleted} messages)`)
      } else {
        result.errors.push(`Failed to clean user messages: ${response.status()}`)
      }
    } catch (error) {
      result.errors.push(`User messages cleanup error: ${error}`)
    }
  }
  
  /**
   * Cleanup user sessions
   */
  private static async cleanupUserSessions(
    page: Page, 
    userId: string, 
    result: CleanupResult
  ): Promise<void> {
    try {
      // Delete from wingman_sessions table
      const response = await page.request.delete(
        `${TEST_CONFIG.apiUrl}/test/cleanup/user-sessions/${userId}`,
        {
          headers: {
            'X-Test-Cleanup': 'true',
            'Content-Type': 'application/json'
          }
        }
      )
      
      if (response.ok()) {
        const data = await response.json()
        result.cleaned_items += data.sessions_deleted || 0
        console.log(`🗑️ Cleaned user sessions: ${userId} (${data.sessions_deleted} sessions)`)
      } else {
        result.errors.push(`Failed to clean user sessions: ${response.status()}`)
      }
    } catch (error) {
      result.errors.push(`User sessions cleanup error: ${error}`)
    }
  }
  
  /**
   * Cleanup user location data
   */
  private static async cleanupUserLocation(
    page: Page, 
    userId: string, 
    result: CleanupResult
  ): Promise<void> {
    try {
      // Delete from user_locations table
      const response = await page.request.delete(
        `${TEST_CONFIG.apiUrl}/test/cleanup/user-location/${userId}`,
        {
          headers: {
            'X-Test-Cleanup': 'true',
            'Content-Type': 'application/json'
          }
        }
      )
      
      if (response.ok()) {
        result.cleaned_items++
        console.log(`🗑️ Cleaned user location: ${userId}`)
      } else {
        result.errors.push(`Failed to clean user location: ${response.status()}`)
      }
    } catch (error) {
      result.errors.push(`User location cleanup error: ${error}`)
    }
  }
  
  /**
   * Cleanup user record (auth.users)
   */
  private static async cleanupUserRecord(
    page: Page, 
    userId: string, 
    result: CleanupResult
  ): Promise<void> {
    try {
      // Delete from auth.users table (requires service role)
      const response = await page.request.delete(
        `${TEST_CONFIG.apiUrl}/test/cleanup/user-record/${userId}`,
        {
          headers: {
            'X-Test-Cleanup': 'true',
            'Content-Type': 'application/json'
          }
        }
      )
      
      if (response.ok()) {
        result.cleaned_items++
        console.log(`🗑️ Cleaned user record: ${userId}`)
      } else {
        result.errors.push(`Failed to clean user record: ${response.status()}`)
      }
    } catch (error) {
      result.errors.push(`User record cleanup error: ${error}`)
    }
  }
  
  /**
   * Cleanup all test data
   */
  static async cleanupAll(page: Page): Promise<CleanupResult> {
    console.log(`🧹 Starting full test data cleanup`)
    
    const result: CleanupResult = {
      success: true,
      cleaned_items: 0,
      errors: [],
      timestamp: new Date().toISOString()
    }
    
    try {
      // Cleanup all test users (users with test emails)
      const response = await page.request.delete(
        `${TEST_CONFIG.apiUrl}/test/cleanup/all`,
        {
          headers: {
            'X-Test-Cleanup': 'true',
            'Content-Type': 'application/json'
          },
          data: {
            confirm: true,
            test_email_patterns: [
              '%.wingman.test@%',
              'test.%.@wingman.test',
              'test-%@example.com'
            ]
          }
        }
      )
      
      if (response.ok()) {
        const data = await response.json()
        result.cleaned_items = data.total_cleaned || 0
        console.log(`✅ Full cleanup completed: ${result.cleaned_items} items cleaned`)
      } else {
        result.success = false
        result.errors.push(`Full cleanup failed: ${response.status()}`)
      }
      
    } catch (error) {
      result.success = false
      result.errors.push(`Full cleanup error: ${error}`)
      console.error(`❌ Full cleanup failed:`, error)
    }
    
    return result
  }
  
  /**
   * Process cleanup queue
   */
  static async processCleanupQueue(page: Page): Promise<CleanupResult[]> {
    if (this.isCleanupRunning) {
      console.log(`⏳ Cleanup already running, skipping queue processing`)
      return []
    }
    
    this.isCleanupRunning = true
    console.log(`🚀 Processing cleanup queue: ${this.cleanupQueue.length} items`)
    
    const results: CleanupResult[] = []
    
    try {
      for (const target of this.cleanupQueue) {
        let result: CleanupResult
        
        switch (target.cleanup_type) {
          case 'user':
            result = await this.cleanupUser(page, target.userId!)
            break
          case 'match':
            result = await this.cleanupMatch(page, target.matchId!)
            break
          case 'session':
            result = await this.cleanupSession(page, target.sessionId!)
            break
          case 'all':
            result = await this.cleanupAll(page)
            break
          default:
            result = {
              success: false,
              cleaned_items: 0,
              errors: [`Unknown cleanup type: ${target.cleanup_type}`],
              timestamp: new Date().toISOString()
            }
        }
        
        results.push(result)
      }
      
      // Clear the queue
      this.cleanupQueue = []
      
    } finally {
      this.isCleanupRunning = false
    }
    
    console.log(`✅ Cleanup queue processed: ${results.length} operations completed`)
    return results
  }
  
  /**
   * Cleanup specific match
   */
  private static async cleanupMatch(page: Page, matchId: string): Promise<CleanupResult> {
    const result: CleanupResult = {
      success: true,
      cleaned_items: 0,
      errors: [],
      timestamp: new Date().toISOString()
    }
    
    try {
      const response = await page.request.delete(
        `${TEST_CONFIG.apiUrl}/test/cleanup/match/${matchId}`,
        {
          headers: {
            'X-Test-Cleanup': 'true',
            'Content-Type': 'application/json'
          }
        }
      )
      
      if (response.ok()) {
        result.cleaned_items++
        console.log(`🗑️ Cleaned match: ${matchId}`)
      } else {
        result.success = false
        result.errors.push(`Failed to clean match: ${response.status()}`)
      }
    } catch (error) {
      result.success = false
      result.errors.push(`Match cleanup error: ${error}`)
    }
    
    return result
  }
  
  /**
   * Cleanup specific session
   */
  private static async cleanupSession(page: Page, sessionId: string): Promise<CleanupResult> {
    const result: CleanupResult = {
      success: true,
      cleaned_items: 0,
      errors: [],
      timestamp: new Date().toISOString()
    }
    
    try {
      const response = await page.request.delete(
        `${TEST_CONFIG.apiUrl}/test/cleanup/session/${sessionId}`,
        {
          headers: {
            'X-Test-Cleanup': 'true',
            'Content-Type': 'application/json'
          }
        }
      )
      
      if (response.ok()) {
        result.cleaned_items++
        console.log(`🗑️ Cleaned session: ${sessionId}`)
      } else {
        result.success = false
        result.errors.push(`Failed to clean session: ${response.status()}`)
      }
    } catch (error) {
      result.success = false
      result.errors.push(`Session cleanup error: ${error}`)
    }
    
    return result
  }
  
  /**
   * Register user for cleanup on test completion
   */
  static registerUserForCleanup(userId: string): void {
    this.addCleanupTarget({
      userId,
      cleanup_type: 'user'
    })
  }
  
  /**
   * Register match for cleanup on test completion
   */
  static registerMatchForCleanup(matchId: string): void {
    this.addCleanupTarget({
      matchId,
      cleanup_type: 'match'
    })
  }
  
  /**
   * Check if cleanup endpoints are available
   */
  static async checkCleanupAvailability(page: Page): Promise<boolean> {
    try {
      const response = await page.request.get(
        `${TEST_CONFIG.apiUrl}/test/cleanup/status`,
        {
          headers: {
            'X-Test-Cleanup': 'true'
          }
        }
      )
      
      return response.ok()
    } catch (error) {
      console.warn(`⚠️ Cleanup availability check failed:`, error)
      return false
    }
  }
  
  /**
   * Get cleanup statistics
   */
  static async getCleanupStats(page: Page): Promise<any> {
    try {
      const response = await page.request.get(
        `${TEST_CONFIG.apiUrl}/test/cleanup/stats`,
        {
          headers: {
            'X-Test-Cleanup': 'true'
          }
        }
      )
      
      if (response.ok()) {
        return await response.json()
      }
    } catch (error) {
      console.warn(`⚠️ Failed to get cleanup stats:`, error)
    }
    
    return null
  }
}

/**
 * Global cleanup helper for test framework integration
 */
export class GlobalTestCleanup {
  private static cleanupResults: CleanupResult[] = []
  
  /**
   * Setup global cleanup hooks
   */
  static setupGlobalCleanup(page: Page): void {
    // This would be called from global setup
    console.log(`🔧 Global cleanup hooks established`)
  }
  
  /**
   * Execute global cleanup
   */
  static async executeGlobalCleanup(page: Page): Promise<void> {
    console.log(`🧹 Executing global test cleanup`)
    
    try {
      // Check if cleanup is available
      const isAvailable = await DatabaseCleaner.checkCleanupAvailability(page)
      
      if (!isAvailable) {
        console.warn(`⚠️ Cleanup endpoints not available, skipping cleanup`)
        return
      }
      
      // Process any queued cleanup items
      const queueResults = await DatabaseCleaner.processCleanupQueue(page)
      this.cleanupResults.push(...queueResults)
      
      // Get cleanup statistics
      const stats = await DatabaseCleaner.getCleanupStats(page)
      if (stats) {
        console.log(`📊 Cleanup stats:`, stats)
      }
      
      console.log(`✅ Global cleanup completed`)
      
    } catch (error) {
      console.error(`❌ Global cleanup failed:`, error)
    }
  }
  
  /**
   * Get cleanup summary
   */
  static getCleanupSummary(): any {
    const totalCleaned = this.cleanupResults.reduce((sum, result) => sum + result.cleaned_items, 0)
    const totalErrors = this.cleanupResults.reduce((sum, result) => sum + result.errors.length, 0)
    const successRate = this.cleanupResults.length > 0 
      ? (this.cleanupResults.filter(r => r.success).length / this.cleanupResults.length) * 100 
      : 100
    
    return {
      total_operations: this.cleanupResults.length,
      total_cleaned_items: totalCleaned,
      total_errors: totalErrors,
      success_rate: successRate,
      results: this.cleanupResults
    }
  }
}

export default {
  DatabaseCleaner,
  GlobalTestCleanup
}