/**
 * Lazy-loaded Session Page Components
 * Split heavy session components for better performance
 */

import dynamic from 'next/dynamic';
import { SessionSkeleton } from '@/components/ui/skeletons/SessionSkeleton';

// Lazy load session components with proper loading states
export const LazySessionMetadata = dynamic(
  () => import('@/app/session/[id]/SessionMetadata').then(mod => ({ default: mod.SessionMetadata })),
  {
    loading: () => (
      <div style={{ height: '120px', background: '#f7fafc', borderRadius: '8px', marginBottom: '16px' }}>
        <SessionSkeleton />
      </div>
    ),
    ssr: false // Session metadata doesn't need SSR
  }
);

export const LazySessionParticipants = dynamic(
  () => import('@/app/session/[id]/SessionParticipants').then(mod => ({ default: mod.SessionParticipants })),
  {
    loading: () => (
      <div style={{ height: '200px', background: '#f7fafc', borderRadius: '8px', marginBottom: '16px' }}>
        <SessionSkeleton />
      </div>
    ),
    ssr: false
  }
);

export const LazyClientActions = dynamic(
  () => import('@/app/session/[id]/ClientActions').then(mod => ({ default: mod.ClientActions })),
  {
    loading: () => (
      <div style={{ height: '80px', background: '#f7fafc', borderRadius: '8px', marginBottom: '16px' }}>
        <SessionSkeleton />
      </div>
    ),
    ssr: false // Client actions are interactive and don't need SSR
  }
);

// Re-export for easier imports
export {
  LazySessionMetadata as SessionMetadata,
  LazySessionParticipants as SessionParticipants, 
  LazyClientActions as ClientActions,
};