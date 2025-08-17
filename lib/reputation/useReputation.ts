/**
 * useReputation Hook
 * React hook for fetching and managing user reputation data
 */

import { useState, useEffect, useCallback, useRef } from 'react';
import { UseReputationOptions, UseReputationResult, ReputationResponse } from './types';
import { reputationService, ReputationError } from '@/services/reputationService';

export function useReputation(
  userId: string | null, 
  options: UseReputationOptions = {}
): UseReputationResult {
  const {
    useCache = true,
    refetchInterval = 0, // 0 means no auto-refetch
    enabled = true,
  } = options;

  const [reputation, setReputation] = useState<ReputationResponse | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<Error | null>(null);
  const [isStale, setIsStale] = useState(false);
  
  const intervalRef = useRef<NodeJS.Timeout | null>(null);
  const mountedRef = useRef(true);

  /**
   * Fetch reputation data
   */
  const fetchReputation = useCallback(async (showLoading: boolean = true) => {
    if (!userId || !enabled) return;

    if (showLoading) {
      setIsLoading(true);
    }
    setError(null);

    try {
      // Check cache first for immediate response
      const cached = reputationService.getCachedReputation(userId);
      if (cached && !reputation) {
        setReputation(cached);
        setIsStale(false);
      }

      // Fetch fresh data
      const freshData = await reputationService.getUserReputation(userId, useCache);
      
      if (mountedRef.current) {
        setReputation(freshData);
        setIsStale(false);
        setError(null);
      }
    } catch (err) {
      if (mountedRef.current) {
        const error = err instanceof ReputationError ? err : new Error('Failed to fetch reputation');
        setError(error);
        
        // If we have cached data, mark it as stale instead of clearing
        if (reputation) {
          setIsStale(true);
        }
      }
    } finally {
      if (mountedRef.current && showLoading) {
        setIsLoading(false);
      }
    }
  }, [userId, enabled, useCache, reputation]);

  /**
   * Manual refetch function
   */
  const refetch = useCallback(async () => {
    await fetchReputation(true);
  }, [fetchReputation]);

  /**
   * Initial fetch and setup auto-refetch
   */
  useEffect(() => {
    if (!userId || !enabled) {
      setReputation(null);
      setError(null);
      setIsLoading(false);
      return;
    }

    // Initial fetch
    fetchReputation(true);

    // Setup interval for auto-refetch
    if (refetchInterval > 0) {
      intervalRef.current = setInterval(() => {
        fetchReputation(false); // Background refetch without loading state
      }, refetchInterval);
    }

    return () => {
      if (intervalRef.current) {
        clearInterval(intervalRef.current);
        intervalRef.current = null;
      }
    };
  }, [userId, enabled, refetchInterval, fetchReputation]);

  /**
   * Cleanup on unmount
   */
  useEffect(() => {
    return () => {
      mountedRef.current = false;
      if (intervalRef.current) {
        clearInterval(intervalRef.current);
      }
    };
  }, []);

  return {
    reputation,
    isLoading,
    error,
    refetch,
    isStale,
  };
}

/**
 * Hook for multiple users' reputation data
 */
export function useMultipleReputations(
  userIds: string[],
  options: UseReputationOptions = {}
): Record<string, UseReputationResult> {
  const [results, setResults] = useState<Record<string, UseReputationResult>>({});

  useEffect(() => {
    const newResults: Record<string, UseReputationResult> = {};
    
    userIds.forEach(userId => {
      // This would ideally use a more efficient batch API call
      // For now, we'll use individual hooks
      newResults[userId] = {
        reputation: null,
        isLoading: true,
        error: null,
        refetch: async () => {},
        isStale: false,
      };
    });

    setResults(newResults);
  }, [userIds]);

  return results;
}