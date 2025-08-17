/**
 * Intelligent Component Prefetching
 * Preloads components based on user journey patterns
 */

import { Router } from 'next/router';

interface PrefetchConfig {
  routes: string[];
  components: string[];
  delay: number;
  userBehaviorWeight: number;
}

interface UserBehavior {
  visitedRoutes: Set<string>;
  timeSpent: Record<string, number>;
  interactions: number;
  scrollDepth: number;
}

class ComponentPrefetcher {
  private behavior: UserBehavior = {
    visitedRoutes: new Set(),
    timeSpent: {},
    interactions: 0,
    scrollDepth: 0,
  };

  private prefetchQueue: Set<string> = new Set();
  private startTime: number = Date.now();

  // Route patterns based on user journey analysis
  private readonly JOURNEY_PATTERNS = {
    '/': ['/confidence-test', '/auth/signin'],
    '/confidence-test': ['/dating-goals', '/profile-setup', '/find-buddy'],
    '/dating-goals': ['/find-buddy', '/matches'],
    '/profile-setup': ['/confidence-test', '/find-buddy'],
    '/find-buddy': ['/matches', '/buddy-chat'],
    '/matches': ['/buddy-chat', '/session'],
    '/buddy-chat': ['/session'],
    '/session': ['/matches', '/buddy-chat'],
  } as const;

  // Component dependencies - which components are likely needed together
  private readonly COMPONENT_DEPENDENCIES = {
    'confidence-test': ['ReputationBadge', 'ProgressiveLoader'],
    'dating-goals': ['DatingGoalsChat', 'TopicProgress', 'GoalsCompletion'],
    'buddy-chat': ['MatchCard', 'ReputationBadge', 'LocationCapture'],
    'session': ['ReputationBadge', 'MatchCard'],
    'profile-setup': ['PhotoUpload', 'LocationCapture', 'ReactDropzone'],
  } as const;

  /**
   * Initialize prefetching for the current route
   */
  initializePrefetching(currentRoute: string): void {
    this.trackRouteVisit(currentRoute);
    this.scheduleIntelligentPrefetch(currentRoute);
    this.setupBehaviorTracking();
  }

  /**
   * Track user behavior to improve prefetching decisions
   */
  private trackRouteVisit(route: string): void {
    this.behavior.visitedRoutes.add(route);
    
    // Store in localStorage for persistence
    if (typeof window !== 'undefined') {
      const stored = localStorage.getItem('wingman_prefetch_behavior');
      let persistedBehavior = {};
      
      try {
        persistedBehavior = stored ? JSON.parse(stored) : {};
      } catch (error) {
        console.warn('Failed to parse prefetch behavior:', error);
      }

      const updated = {
        ...persistedBehavior,
        visitedRoutes: Array.from(this.behavior.visitedRoutes),
        lastVisit: Date.now(),
      };

      localStorage.setItem('wingman_prefetch_behavior', JSON.stringify(updated));
    }
  }

  /**
   * Calculate priority score for routes based on user behavior
   */
  private calculateRoutePriority(route: string, currentRoute: string): number {
    let score = 0;

    // Journey pattern score (40% weight)
    const patterns = this.JOURNEY_PATTERNS[currentRoute as keyof typeof this.JOURNEY_PATTERNS];
    if (patterns?.includes(route)) {
      score += 40;
    }

    // Historical visit frequency (30% weight)
    if (this.behavior.visitedRoutes.has(route)) {
      score += 30;
    }

    // Time spent on current route (20% weight) 
    const timeOnCurrent = Date.now() - this.startTime;
    if (timeOnCurrent > 30000) { // 30 seconds indicates engagement
      score += 20;
    }

    // User interaction level (10% weight)
    if (this.behavior.interactions > 3) {
      score += 10;
    }

    return score;
  }

  /**
   * Intelligently prefetch routes and components
   */
  private scheduleIntelligentPrefetch(currentRoute: string): void {
    setTimeout(() => {
      this.prefetchNextLikelyRoutes(currentRoute);
      this.prefetchComponentDependencies(currentRoute);
    }, 2000); // Delay to avoid impacting initial load
  }

  /**
   * Prefetch routes that user is likely to visit next
   */
  private prefetchNextLikelyRoutes(currentRoute: string): void {
    const possibleRoutes = this.JOURNEY_PATTERNS[currentRoute as keyof typeof this.JOURNEY_PATTERNS] || [];
    
    const prioritizedRoutes = possibleRoutes
      .map(route => ({
        route,
        priority: this.calculateRoutePriority(route, currentRoute)
      }))
      .sort((a, b) => b.priority - a.priority)
      .slice(0, 2); // Only prefetch top 2 routes

    prioritizedRoutes.forEach(({ route }) => {
      if (!this.prefetchQueue.has(route)) {
        this.prefetchRoute(route);
      }
    });
  }

  /**
   * Prefetch components that are likely needed for current route
   */
  private prefetchComponentDependencies(currentRoute: string): void {
    const routeKey = currentRoute.split('/')[1] || 'home';
    const dependencies = this.COMPONENT_DEPENDENCIES[routeKey as keyof typeof this.COMPONENT_DEPENDENCIES];

    if (dependencies) {
      dependencies.forEach(component => {
        this.prefetchComponent(component);
      });
    }
  }

  /**
   * Prefetch a specific route
   */
  private prefetchRoute(route: string): void {
    if (typeof window !== 'undefined' && 'requestIdleCallback' in window) {
      // Use requestIdleCallback for non-blocking prefetch
      requestIdleCallback(() => {
        import('next/router').then(({ default: Router }) => {
          Router.prefetch(route);
          this.prefetchQueue.add(route);
          
          if (process.env.NODE_ENV === 'development') {
            console.log(`🚀 Prefetched route: ${route}`);
          }
        });
      });
    }
  }

  /**
   * Prefetch a specific component
   */
  private prefetchComponent(componentName: string): void {
    if (typeof window !== 'undefined' && 'requestIdleCallback' in window) {
      requestIdleCallback(() => {
        // Dynamic import for component prefetching
        switch (componentName) {
          case 'ReputationBadge':
            import('@/components/ReputationBadge');
            break;
          case 'MatchCard':
            import('@/components/MatchCard');
            break;
          case 'DatingGoalsChat':
            import('@/components/DatingGoalsChat');
            break;
          case 'TopicProgress':
            import('@/components/TopicProgress');
            break;
          case 'PhotoUpload':
            import('@/components/LazyComponents').then(m => m.LazyPhotoUpload);
            break;
          case 'LocationCapture':
            import('@/components/LocationCapture');
            break;
          // Add more components as needed
        }
        
        if (process.env.NODE_ENV === 'development') {
          console.log(`🔄 Prefetched component: ${componentName}`);
        }
      });
    }
  }

  /**
   * Setup behavior tracking for better prefetch decisions
   */
  private setupBehaviorTracking(): void {
    if (typeof window === 'undefined') return;

    // Track scroll depth
    const handleScroll = () => {
      const scrollPercent = (window.scrollY / (document.body.scrollHeight - window.innerHeight)) * 100;
      this.behavior.scrollDepth = Math.max(this.behavior.scrollDepth, scrollPercent);
    };

    // Track interactions
    const handleInteraction = () => {
      this.behavior.interactions++;
    };

    // Add event listeners
    window.addEventListener('scroll', handleScroll, { passive: true });
    window.addEventListener('click', handleInteraction, { passive: true });
    window.addEventListener('keydown', handleInteraction, { passive: true });

    // Cleanup on page unload
    window.addEventListener('beforeunload', () => {
      window.removeEventListener('scroll', handleScroll);
      window.removeEventListener('click', handleInteraction);
      window.removeEventListener('keydown', handleInteraction);
    });
  }

  /**
   * Get prefetch statistics for performance monitoring
   */
  getPrefetchStats(): { 
    prefetchedRoutes: number; 
    behaviorScore: number; 
    timeSpent: number;
  } {
    return {
      prefetchedRoutes: this.prefetchQueue.size,
      behaviorScore: this.behavior.interactions + (this.behavior.scrollDepth / 10),
      timeSpent: Date.now() - this.startTime,
    };
  }
}

// Singleton instance
export const componentPrefetcher = new ComponentPrefetcher();

/**
 * Hook for easy prefetching in React components
 */
export const usePrefetch = (currentRoute: string) => {
  if (typeof window !== 'undefined') {
    componentPrefetcher.initializePrefetching(currentRoute);
  }

  return {
    stats: componentPrefetcher.getPrefetchStats(),
  };
};