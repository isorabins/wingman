# Frontend Performance Optimization - WingmanMatch

## Implementation Plan: 6-Phase Complete Performance Optimization

### Current Tech Stack Analysis
- **Framework**: Next.js 14.0.4 with App Router
- **UI Framework**: Chakra UI 2.8.2 with Emotion
- **State Management**: React 18.2.0 with React Hook Form
- **Backend Integration**: FastAPI with Supabase PostgreSQL
- **Testing**: Vitest + Playwright for comprehensive test coverage

### Performance Targets
- **Lighthouse Performance**: ≥90 on all core pages
- **Bundle Size Reduction**: 40%+ from baseline  
- **Core Web Vitals**: FCP <1.5s, LCP <2.5s, TTI <3s
- **User Experience**: Professional loading states and smooth transitions

---

## Phase 1: Bundle Analysis & Baseline Establishment

### 1.1 Bundle Analysis Setup
```typescript
// tools/bundle-analyzer.ts - Webpack Bundle Analyzer integration
import { BundleAnalyzerPlugin } from 'webpack-bundle-analyzer'

export const getBundleAnalysisConfig = (analyze: boolean) => ({
  webpack: (config: any) => {
    if (analyze) {
      config.plugins.push(
        new BundleAnalyzerPlugin({
          analyzerMode: 'static',
          openAnalyzer: false,
          reportFilename: 'bundle-analysis.html'
        })
      )
    }
    return config
  }
})
```

### 1.2 Performance Monitoring Setup
```typescript
// lib/performance/monitor.ts - Core Web Vitals tracking
export class PerformanceMonitor {
  static trackWebVitals() {
    // FCP, LCP, CLS, FID, TTI monitoring
    // Integration with analytics for baseline establishment
  }
  
  static measureBundleSize() {
    // JavaScript bundle size tracking
    // Asset loading performance metrics
  }
}
```

### 1.3 Baseline Metrics Collection
- Current bundle size analysis for all chunks
- Page-by-page performance audit with Lighthouse
- Core Web Vitals baseline for target pages:
  - Homepage (`/`)
  - Confidence Test (`/confidence-test`)
  - Profile Setup (`/profile-setup`) 
  - Buddy Chat (`/buddy-chat/[matchId]`)
  - Sessions (`/session/[id]`)

---

## Phase 2: Core Component Lazy Loading

### 2.1 Page-Level Dynamic Imports
```typescript
// app/loading.tsx - Global loading component
export default function Loading() {
  return (
    <Box display="flex" justifyContent="center" alignItems="center" height="100vh">
      <Spinner size="xl" color="blue.500" />
      <Text ml={4}>Loading Wingman...</Text>
    </Box>
  )
}

// Dynamic imports for heavy pages
const ProfileSetup = dynamic(() => import('./profile-setup/page'), {
  loading: () => <Loading />,
  ssr: false
})

const ConfidenceTest = dynamic(() => import('./confidence-test/page'), {
  loading: () => <Loading />,
  ssr: false
})
```

### 2.2 Component-Level Lazy Loading
```typescript
// components/LazyComponents.tsx - High-level component lazy loading
export const LazyLocationCapture = dynamic(() => import('./LocationCapture'), {
  loading: () => <Skeleton height="200px" />,
  ssr: false
})

export const LazyDatingGoalsChat = dynamic(() => import('./DatingGoalsChat'), {
  loading: () => <ChatSkeleton />,
  ssr: false
})

export const LazyReputationBadge = dynamic(() => import('./ReputationBadge'), {
  loading: () => <Badge>Loading...</Badge>,
  ssr: false
})
```

### 2.3 Heavy Feature Lazy Loading
```typescript
// lib/lazy-features.ts - Feature-based code splitting
export const LazyPhotoUpload = dynamic(() => import('../storage/photo_upload'), {
  loading: () => <Box>Preparing photo upload...</Box>,
  ssr: false
})

export const LazyLocationService = dynamic(() => import('../services/locationService'), {
  loading: () => <Text>Loading location services...</Text>,
  ssr: false
})
```

---

## Phase 3: Route-Level Code Splitting

### 3.1 Advanced Route Splitting
```typescript
// lib/route-optimization.ts - Route-based optimization
export const routeConfig = {
  '/': { preload: ['confidence-test'], prefetch: true },
  '/confidence-test': { preload: ['profile-setup'], chunks: ['assessment'] },
  '/profile-setup': { preload: ['find-buddy'], chunks: ['profile', 'upload'] },
  '/buddy-chat/[matchId]': { chunks: ['chat', 'real-time'], ssr: false },
  '/session/[id]': { chunks: ['session', 'management'], ssr: true }
}

// next.config.js enhancements
const nextConfig = {
  experimental: {
    optimizeCss: true,
    scrollRestoration: true
  },
  compiler: {
    removeConsole: process.env.NODE_ENV === 'production'
  }
}
```

### 3.2 Intelligent Preloading
```typescript
// hooks/useIntelligentPreload.ts - Smart preloading based on user behavior
export const useIntelligentPreload = () => {
  useEffect(() => {
    // Preload next likely page based on current route
    const preloadMap = {
      '/': () => import('../app/confidence-test/page'),
      '/confidence-test': () => import('../app/profile-setup/page'),
      '/profile-setup': () => import('../app/find-buddy/page')
    }
    
    const currentPath = window.location.pathname
    const preloader = preloadMap[currentPath]
    if (preloader) {
      setTimeout(preloader, 2000) // Preload after 2s of inactivity
    }
  }, [])
}
```

### 3.3 Critical Resource Prioritization
```typescript
// components/ResourceOptimizer.tsx - Critical resource management
export const ResourceOptimizer = () => (
  <Head>
    {/* Critical CSS inlining */}
    <style dangerouslySetInnerHTML={{
      __html: criticalCSS
    }} />
    
    {/* Preload critical assets */}
    <link rel="preload" href="/api/static/confidence-test/questions.v1.json" as="fetch" />
    <link rel="prefetch" href="/profile-setup" />
    
    {/* Resource hints for performance */}
    <link rel="dns-prefetch" href="https://api.supabase.co" />
    <link rel="preconnect" href="https://fonts.googleapis.com" />
  </Head>
)
```

---

## Phase 4: Dependency Optimization

### 4.1 Bundle Size Reduction
```typescript
// lib/optimized-imports.ts - Tree-shaking and selective imports
// Replace full Chakra UI with targeted imports
export { 
  Box, 
  Button, 
  Text, 
  Input, 
  VStack,
  HStack,
  useToast 
} from '@chakra-ui/react'

// Optimize Lucide React imports
export { 
  ChevronLeft,
  User,
  MapPin,
  Camera,
  Send 
} from 'lucide-react/dist/esm/icons'

// Replace heavy dependencies
export const OptimizedDropzone = dynamic(() => 
  import('react-dropzone').then(mod => ({ default: mod.useDropzone }))
)
```

### 4.2 Vendor Bundle Optimization
```typescript
// next.config.js - Advanced webpack optimization
const nextConfig = {
  webpack: (config) => {
    config.optimization.splitChunks = {
      chunks: 'all',
      cacheGroups: {
        vendor: {
          test: /[\\/]node_modules[\\/]/,
          name: 'vendors',
          chunks: 'all',
        },
        chakra: {
          test: /[\\/]node_modules[\\/]@chakra-ui[\\/]/,
          name: 'chakra',
          chunks: 'all',
        },
        supabase: {
          test: /[\\/]node_modules[\\/]@supabase[\\/]/,
          name: 'supabase',
          chunks: 'all',
        }
      }
    }
    return config
  }
}
```

### 4.3 Runtime Optimization
```typescript
// lib/runtime-optimization.ts - Runtime performance improvements
export const RuntimeOptimizer = {
  // Debounced API calls
  debouncedApiCall: debounce((fn: Function) => fn(), 300),
  
  // Memoized expensive calculations
  memoizedDistanceCalculation: useMemo(() => calculateDistance, [coordinates]),
  
  // Optimized state updates
  optimizedStateUpdate: useCallback((update: any) => {
    setState(prev => ({ ...prev, ...update }))
  }, [])
}
```

---

## Phase 5: Advanced Performance Features

### 5.1 Progressive Loading System
```typescript
// components/ProgressiveLoader.tsx - Advanced loading states
export const ProgressiveLoader = ({ 
  stages = ['Connecting...', 'Loading data...', 'Almost ready...'],
  duration = 2000 
}) => {
  const [currentStage, setCurrentStage] = useState(0)
  
  useEffect(() => {
    const interval = setInterval(() => {
      setCurrentStage(prev => 
        prev < stages.length - 1 ? prev + 1 : prev
      )
    }, duration / stages.length)
    
    return () => clearInterval(interval)
  }, [stages.length, duration])
  
  return (
    <VStack spacing={4}>
      <Spinner size="lg" />
      <Text>{stages[currentStage]}</Text>
      <Progress value={(currentStage + 1) / stages.length * 100} />
    </VStack>
  )
}
```

### 5.2 Smart Caching Layer
```typescript
// lib/cache/smart-cache.ts - Intelligent caching system
export class SmartCache {
  private static cache = new Map()
  private static ttl = new Map()
  
  static set(key: string, value: any, ttlMs = 300000) { // 5min default
    this.cache.set(key, value)
    this.ttl.set(key, Date.now() + ttlMs)
  }
  
  static get(key: string) {
    if (this.ttl.get(key) < Date.now()) {
      this.cache.delete(key)
      this.ttl.delete(key)
      return null
    }
    return this.cache.get(key)
  }
  
  static prefetch(key: string, fetcher: () => Promise<any>) {
    if (!this.cache.has(key)) {
      fetcher().then(data => this.set(key, data))
    }
  }
}
```

### 5.3 Optimistic UI Updates
```typescript
// hooks/useOptimisticUpdate.ts - Optimistic UI pattern
export const useOptimisticUpdate = <T>(
  initialData: T,
  apiCall: (data: T) => Promise<T>
) => {
  const [data, setData] = useState(initialData)
  const [isLoading, setIsLoading] = useState(false)
  
  const updateOptimistically = useCallback(async (optimisticUpdate: Partial<T>) => {
    // Apply optimistic update immediately
    setData(prev => ({ ...prev, ...optimisticUpdate }))
    setIsLoading(true)
    
    try {
      // Confirm with API
      const confirmedData = await apiCall({ ...data, ...optimisticUpdate })
      setData(confirmedData)
    } catch (error) {
      // Rollback on error
      setData(initialData)
      throw error
    } finally {
      setIsLoading(false)
    }
  }, [data, initialData, apiCall])
  
  return { data, updateOptimistically, isLoading }
}
```

### 5.4 Virtual Scrolling for Lists
```typescript
// components/VirtualizedList.tsx - Performance for large lists
export const VirtualizedChatList = ({ messages }: { messages: Message[] }) => {
  const [visibleRange, setVisibleRange] = useState({ start: 0, end: 20 })
  
  return (
    <Box height="400px" overflowY="auto" onScroll={handleScroll}>
      {messages.slice(visibleRange.start, visibleRange.end).map(message => (
        <MessageComponent key={message.id} message={message} />
      ))}
    </Box>
  )
}
```

---

## Phase 6: Performance Validation & Monitoring

### 6.1 Automated Performance Testing
```typescript
// tests/performance/lighthouse.spec.ts - Automated Lighthouse testing
import { test, expect } from '@playwright/test'

test.describe('Performance Validation', () => {
  test('Homepage Lighthouse Score ≥90', async ({ page }) => {
    await page.goto('/')
    const lighthouse = await page.lighthouse()
    expect(lighthouse.performance).toBeGreaterThanOrEqual(90)
  })
  
  test('Core Web Vitals Within Targets', async ({ page }) => {
    await page.goto('/')
    const vitals = await page.evaluate(() => ({
      fcp: performance.getEntriesByName('first-contentful-paint')[0],
      lcp: performance.getEntriesByName('largest-contentful-paint')[0]
    }))
    
    expect(vitals.fcp.startTime).toBeLessThan(1500) // <1.5s
    expect(vitals.lcp.startTime).toBeLessThan(2500) // <2.5s
  })
})
```

### 6.2 Real-time Performance Monitoring
```typescript
// lib/monitoring/performance-monitor.ts - Production monitoring
export class ProductionPerformanceMonitor {
  static initializeMonitoring() {
    // Web Vitals tracking
    getCLS(this.reportMetric)
    getFID(this.reportMetric)
    getFCP(this.reportMetric)
    getLCP(this.reportMetric)
    getTTFB(this.reportMetric)
  }
  
  private static reportMetric(metric: Metric) {
    // Send to analytics/monitoring service
    analytics.track('performance_metric', {
      name: metric.name,
      value: metric.value,
      rating: metric.rating
    })
  }
  
  static trackBundlePerformance() {
    const navigation = performance.getEntriesByType('navigation')[0]
    const paintEntries = performance.getEntriesByType('paint')
    
    return {
      loadTime: navigation.loadEventEnd - navigation.fetchStart,
      domContentLoaded: navigation.domContentLoadedEventEnd - navigation.fetchStart,
      firstPaint: paintEntries.find(entry => entry.name === 'first-paint')?.startTime,
      firstContentfulPaint: paintEntries.find(entry => entry.name === 'first-contentful-paint')?.startTime
    }
  }
}
```

### 6.3 Performance Budget Enforcement
```typescript
// tools/performance-budget.ts - Budget enforcement
export const performanceBudget = {
  // Bundle size limits
  maxBundleSize: 250, // KB
  maxChunkSize: 100, // KB
  maxAssetSize: 50, // KB
  
  // Performance metrics
  maxFCP: 1500, // ms
  maxLCP: 2500, // ms
  maxTTI: 3000, // ms
  maxCLS: 0.1,
  maxFID: 100, // ms
  
  // Lighthouse scores
  minPerformanceScore: 90,
  minAccessibilityScore: 95,
  minBestPracticesScore: 90,
  minSEOScore: 95
}

export const validatePerformanceBudget = async (page: Page) => {
  const metrics = await page.lighthouse()
  const budgetViolations = []
  
  if (metrics.performance < performanceBudget.minPerformanceScore) {
    budgetViolations.push(`Performance: ${metrics.performance} < ${performanceBudget.minPerformanceScore}`)
  }
  
  return budgetViolations
}
```

---

## Implementation Timeline

### Week 1: Foundation & Analysis
- **Day 1-2**: Bundle analysis setup and baseline metrics
- **Day 3-4**: Performance monitoring implementation  
- **Day 5-7**: Phase 1 completion and validation

### Week 2: Core Optimizations
- **Day 1-3**: Component lazy loading implementation
- **Day 4-5**: Route-level code splitting
- **Day 6-7**: Phase 2-3 testing and refinement

### Week 3: Advanced Features
- **Day 1-3**: Dependency optimization and bundle reduction
- **Day 4-5**: Progressive loading and caching systems
- **Day 6-7**: Phase 4-5 integration and testing

### Week 4: Validation & Monitoring
- **Day 1-3**: Performance testing automation
- **Day 4-5**: Production monitoring setup
- **Day 6-7**: Final validation and documentation

---

## Success Metrics & Validation

### Lighthouse Performance Targets
- **Homepage**: ≥90 performance score
- **Confidence Test**: ≥90 performance score  
- **Profile Setup**: ≥85 performance score (heavy forms)
- **Buddy Chat**: ≥85 performance score (real-time features)
- **Sessions**: ≥90 performance score

### Bundle Size Reduction Goals
- **Main Bundle**: 40% reduction from baseline
- **Page Chunks**: 50% reduction through code splitting
- **Vendor Chunks**: 30% reduction through optimization
- **Asset Loading**: 60% improvement in load times

### Core Web Vitals Compliance
- **First Contentful Paint (FCP)**: <1.5s on all pages
- **Largest Contentful Paint (LCP)**: <2.5s on all pages  
- **Time to Interactive (TTI)**: <3s on all pages
- **Cumulative Layout Shift (CLS)**: <0.1 across the application
- **First Input Delay (FID)**: <100ms for all interactions

### User Experience Improvements
- **Loading States**: Professional, informative loading indicators
- **Smooth Transitions**: 60fps animations and transitions
- **Perceived Performance**: 50% improvement in perceived speed
- **Error Handling**: Graceful degradation with meaningful feedback
- **Accessibility**: WCAG 2.1 AA compliance maintained

---

## Risk Mitigation

### Technical Risks
- **Bundle Fragmentation**: Careful chunk strategy to avoid over-splitting
- **Runtime Performance**: Monitoring for performance regressions
- **Feature Compatibility**: Ensuring lazy loading doesn't break functionality
- **SEO Impact**: Maintaining SSR for critical pages

### Mitigation Strategies
- **Incremental Rollout**: Phase-by-phase implementation with validation
- **A/B Testing**: Performance comparison before/after optimization
- **Fallback Mechanisms**: Graceful degradation for optimization failures
- **Monitoring Alerts**: Real-time performance regression detection

This comprehensive plan will transform WingmanMatch into a high-performance, production-ready application that delivers exceptional user experience while maintaining all existing functionality.