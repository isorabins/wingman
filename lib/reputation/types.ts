/**
 * TypeScript interfaces for the Reputation System
 * Defines types for API responses and component props
 */

export type BadgeColor = 'green' | 'gold' | 'red';

export interface ReputationResponse {
  score: number;
  badge_color: BadgeColor;
  completed_sessions: number;
  no_shows: number;
  cache_timestamp: string;
}

export interface ReputationBadgeProps {
  userId: string;
  size?: 'sm' | 'md' | 'lg';
  variant?: 'solid' | 'outline' | 'subtle';
  showScore?: boolean;
  showTooltip?: boolean;
  className?: string;
}

export interface UseReputationOptions {
  useCache?: boolean;
  refetchInterval?: number;
  enabled?: boolean;
}

export interface UseReputationResult {
  reputation: ReputationResponse | null;
  isLoading: boolean;
  error: Error | null;
  refetch: () => Promise<void>;
  isStale: boolean;
}

export class ReputationError extends Error {
  public status?: number;
  public code?: string;

  constructor(message: string, status?: number, code?: string) {
    super(message);
    this.name = 'ReputationError';
    this.status = status;
    this.code = code;
  }
}

export interface ReputationCache {
  [userId: string]: {
    data: ReputationResponse;
    timestamp: number;
    ttl: number;
  };
}