/**
 * Reputation Service
 * Handles API calls for user reputation data with caching and error handling
 */

import { ReputationResponse, ReputationError, ReputationCache } from '@/lib/reputation/types';

class ReputationService {
  private cache: ReputationCache = {};
  private readonly CACHE_TTL = 5 * 60 * 1000; // 5 minutes
  private readonly API_BASE = '/api/user/reputation';

  /**
   * Fetch user reputation from API with caching
   */
  async getUserReputation(userId: string, useCache: boolean = true): Promise<ReputationResponse> {
    // Check cache first if enabled
    if (useCache && this.isCacheValid(userId)) {
      return this.cache[userId].data;
    }

    try {
      const response = await fetch(`${this.API_BASE}/${userId}?use_cache=${useCache}`, {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
          'X-Test-User-ID': 'test-user-123', // For development
        },
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new ReputationError(
          errorData.detail || `Failed to fetch reputation: ${response.status}`,
          response.status,
          errorData.code
        );
      }

      const data: ReputationResponse = await response.json();
      
      // Validate response structure
      if (!this.isValidReputationResponse(data)) {
        throw new ReputationError('Invalid reputation data received from server');
      }

      // Cache the response
      if (useCache) {
        this.cacheReputation(userId, data);
      }

      return data;
    } catch (error) {
      if (error instanceof ReputationError) {
        throw error;
      }
      
      // Network or other errors
      throw new ReputationError(
        error instanceof Error ? error.message : 'Failed to fetch reputation data'
      );
    }
  }

  /**
   * Get cached reputation data if available and valid
   */
  getCachedReputation(userId: string): ReputationResponse | null {
    if (this.isCacheValid(userId)) {
      return this.cache[userId].data;
    }
    return null;
  }

  /**
   * Invalidate cache for a specific user
   */
  invalidateCache(userId: string): void {
    delete this.cache[userId];
  }

  /**
   * Clear all cached reputation data
   */
  clearCache(): void {
    this.cache = {};
  }

  /**
   * Get badge color based on reputation score
   * This mirrors the backend logic for consistency
   */
  getBadgeColor(score: number): 'green' | 'gold' | 'red' {
    if (score >= 10) return 'gold';
    if (score >= 0) return 'green';
    return 'red';
  }

  /**
   * Get badge label for accessibility
   */
  getBadgeLabel(score: number, completedSessions: number, noShows: number): string {
    const color = this.getBadgeColor(score);
    const reputation = color === 'gold' ? 'Excellent' : color === 'green' ? 'Good' : 'Needs Improvement';
    return `${reputation} reputation: ${score} points, ${completedSessions} completed sessions, ${noShows} no-shows`;
  }

  /**
   * Private: Check if cached data is still valid
   */
  private isCacheValid(userId: string): boolean {
    const cached = this.cache[userId];
    if (!cached) return false;
    
    const now = Date.now();
    return (now - cached.timestamp) < cached.ttl;
  }

  /**
   * Private: Cache reputation data
   */
  private cacheReputation(userId: string, data: ReputationResponse): void {
    this.cache[userId] = {
      data,
      timestamp: Date.now(),
      ttl: this.CACHE_TTL,
    };
  }

  /**
   * Private: Validate reputation response structure
   */
  private isValidReputationResponse(data: any): data is ReputationResponse {
    return (
      data &&
      typeof data.score === 'number' &&
      typeof data.badge_color === 'string' &&
      ['green', 'gold', 'red'].includes(data.badge_color) &&
      typeof data.completed_sessions === 'number' &&
      typeof data.no_shows === 'number' &&
      typeof data.cache_timestamp === 'string'
    );
  }
}

// Export singleton instance
export const reputationService = new ReputationService();