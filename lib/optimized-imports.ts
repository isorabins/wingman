/**
 * Optimized Import System for WingmanMatch
 * Phase 2: Lazy-loaded components with code splitting
 */

import dynamic from 'next/dynamic'
import { ComponentType, LazyExoticComponent } from 'react'

// Common loading states
const ChakraSpinner = () => (
  <div style={{ 
    display: 'flex', 
    justifyContent: 'center', 
    alignItems: 'center', 
    height: '200px' 
  }}>
    <div style={{
      width: '32px',
      height: '32px',
      border: '3px solid #e2e8f0',
      borderTop: '3px solid #3182ce',
      borderRadius: '50%',
      animation: 'spin 1s linear infinite'
    }} />
  </div>
)

const MinimalSkeleton = ({ height = '200px' }: { height?: string }) => (
  <div style={{
    height,
    backgroundColor: '#f7fafc',
    borderRadius: '8px',
    animation: 'pulse 2s infinite'
  }} />
)

// Type-safe dynamic import wrapper
function createLazyComponent<T extends ComponentType<any>>(
  importFn: () => Promise<{ default: T }>,
  loadingComponent?: ComponentType,
  ssr = false
): LazyExoticComponent<T> {
  return dynamic(importFn, {
    loading: loadingComponent || ChakraSpinner,
    ssr
  })
}

// Phase 2: Core lazy-loaded components
export const LazyComponents = {
  // Heavy UI components (loaded on demand)
  LocationCapture: createLazyComponent(
    () => import('../components/LocationCapture'),
    () => <MinimalSkeleton height="250px" />,
    false
  ),
  
  DatingGoalsChat: createLazyComponent(
    () => import('../components/DatingGoalsChat'),
    () => <MinimalSkeleton height="400px" />,
    false
  ),
  
  ReputationBadge: createLazyComponent(
    () => import('../components/ReputationBadge'),
    () => <div style={{ width: '80px', height: '24px', backgroundColor: '#e2e8f0', borderRadius: '12px' }} />,
    false
  ),
  
  MatchCard: createLazyComponent(
    () => import('../components/MatchCard'),
    () => <MinimalSkeleton height="180px" />,
    false
  ),
  
  // Photo upload - heavy component with file handling
  PhotoUpload: createLazyComponent(
    () => import('../storage/photo_upload'),
    () => <MinimalSkeleton height="200px" />,
    false
  ),
  
  // Test mode indicator - non-critical
  TestModeIndicator: createLazyComponent(
    () => import('../components/TestModeIndicator'),
    () => null,
    false
  ),
}

// Phase 3: Route-level dynamic imports
export const LazyPages = {
  // Assessment flow - heavy AI integration
  ConfidenceTest: createLazyComponent(
    () => import('../app/confidence-test/page'),
    () => <MinimalSkeleton height="500px" />,
    false
  ),
  
  // Profile setup - complex form with validation
  ProfileSetup: createLazyComponent(
    () => import('../app/profile-setup/page'),
    () => <MinimalSkeleton height="600px" />,
    false
  ),
  
  // Dating goals - AI conversation interface
  DatingGoals: createLazyComponent(
    () => import('../app/dating-goals/page'),
    () => <MinimalSkeleton height="500px" />,
    false
  ),
  
  // Chat interface - real-time features
  BuddyChat: createLazyComponent(
    () => import('../app/buddy-chat/[matchId]/page'),
    () => <MinimalSkeleton height="600px" />,
    false
  ),
  
  // Session management - complex state
  SessionView: createLazyComponent(
    () => import('../app/session/[id]/page'),
    () => <MinimalSkeleton height="400px" />,
    false
  ),
  
  // Match finding - location services
  FindBuddy: createLazyComponent(
    () => import('../app/find-buddy/page'),
    () => <MinimalSkeleton height="500px" />,
    false
  ),
}

// Phase 4: Optimized Chakra UI imports
export const OptimizedChakra = {
  // Core layout components (keep in main bundle)
  Box: () => import('@chakra-ui/react').then(mod => ({ default: mod.Box })),
  VStack: () => import('@chakra-ui/react').then(mod => ({ default: mod.VStack })),
  HStack: () => import('@chakra-ui/react').then(mod => ({ default: mod.HStack })),
  Text: () => import('@chakra-ui/react').then(mod => ({ default: mod.Text })),
  Button: () => import('@chakra-ui/react').then(mod => ({ default: mod.Button })),
  
  // Form components (lazy load)
  FormComponents: createLazyComponent(
    () => import('@chakra-ui/react').then(mod => ({ 
      default: () => ({
        FormControl: mod.FormControl,
        FormLabel: mod.FormLabel,
        FormErrorMessage: mod.FormErrorMessage,
        Input: mod.Input,
        Textarea: mod.Textarea,
        Select: mod.Select,
        Checkbox: mod.Checkbox,
        Radio: mod.Radio,
        RadioGroup: mod.RadioGroup,
        Switch: mod.Switch,
      })
    })),
    undefined,
    false
  ),
  
  // Advanced components (lazy load)
  AdvancedComponents: createLazyComponent(
    () => import('@chakra-ui/react').then(mod => ({
      default: () => ({
        Modal: mod.Modal,
        ModalOverlay: mod.ModalOverlay,
        ModalContent: mod.ModalContent,
        ModalHeader: mod.ModalHeader,
        ModalBody: mod.ModalBody,
        ModalFooter: mod.ModalFooter,
        Toast: mod.useToast,
        Tooltip: mod.Tooltip,
        Popover: mod.Popover,
        PopoverTrigger: mod.PopoverTrigger,
        PopoverContent: mod.PopoverContent,
        Menu: mod.Menu,
        MenuButton: mod.MenuButton,
        MenuList: mod.MenuList,
        MenuItem: mod.MenuItem,
      })
    })),
    undefined,
    false
  ),
}

// Bundle size tracking
export const getBundleMetrics = () => {
  if (typeof window === 'undefined') return null
  
  const entries = performance.getEntriesByType('resource')
    .filter(entry => entry.name.includes('.js'))
    .map(entry => ({
      name: entry.name.split('/').pop(),
      size: (entry as any).transferSize || 0,
      loadTime: entry.duration
    }))
  
  const totalSize = entries.reduce((sum, entry) => sum + entry.size, 0)
  
  return {
    entries,
    totalSizeKB: totalSize / 1024,
    chunkCount: entries.length,
    withinBudget: totalSize <= 250 * 1024 // 250KB budget
  }
}

// Performance optimization utilities
export const preloadRoute = (route: string) => {
  if (typeof window !== 'undefined') {
    const link = document.createElement('link')
    link.rel = 'prefetch'
    link.href = route
    document.head.appendChild(link)
  }
}

export const preloadComponent = (componentName: keyof typeof LazyComponents) => {
  if (typeof window !== 'undefined') {
    // Trigger component preload
    LazyComponents[componentName].preload?.()
  }
}

// Auto-preload for high-priority routes
if (typeof window !== 'undefined') {
  // Preload critical routes after initial load
  setTimeout(() => {
    preloadRoute('/confidence-test')
    preloadRoute('/profile-setup')
  }, 2000)
}