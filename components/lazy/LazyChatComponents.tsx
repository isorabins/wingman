/**
 * Lazy-loaded Chat Components
 * Split chat interface components for better performance
 */

import dynamic from 'next/dynamic';
import { ChatSkeleton } from '@/components/ui/skeletons/ChatSkeleton';

// Lazy load chat components that are expensive to render
export const LazyVenueSuggestions = dynamic(
  () => import('@/components/VenueSuggestions').catch(() => 
    // Fallback component if VenueSuggestions doesn't exist yet
    ({ default: () => <div>Venue suggestions loading...</div> })
  ),
  {
    loading: () => (
      <div style={{ height: '300px', background: '#f7fafc', borderRadius: '8px', padding: '16px' }}>
        <ChatSkeleton />
      </div>
    ),
    ssr: false // Venue suggestions don't need SSR
  }
);

export const LazyMessageHistory = dynamic(
  () => import('@/components/MessageHistory').catch(() => 
    // Fallback for now since these components might not exist
    ({ default: () => <div>Message history loading...</div> })
  ),
  {
    loading: () => (
      <div style={{ height: '400px', background: '#f7fafc', borderRadius: '8px', padding: '16px' }}>
        <ChatSkeleton />
      </div>
    ),
    ssr: false
  }
);

export const LazyReputationBadge = dynamic(
  () => import('@/components/ReputationBadge').catch(() => 
    ({ default: () => <div style={{ width: '60px', height: '24px', background: '#e2e8f0', borderRadius: '12px' }} /> })
  ),
  {
    loading: () => (
      <div style={{ width: '60px', height: '24px', background: '#e2e8f0', borderRadius: '12px' }} />
    ),
    ssr: false // Reputation badges are not critical for initial load
  }
);

// Export individual components
export {
  LazyVenueSuggestions as VenueSuggestions,
  LazyMessageHistory as MessageHistory,
  LazyReputationBadge as ReputationBadge,
};