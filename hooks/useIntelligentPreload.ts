/**
 * Intelligent Route Preloading Hook
 * Phase 3: Smart prefetching based on user behavior
 */

import React, { useEffect, useRef, useState } from 'react'
import { useRouter } from 'next/navigation'

interface PreloadConfig {
  routes: string[]
  delay?: number
  triggerOnHover?: boolean
  triggerOnScroll?: boolean
  maxPreloads?: number
}

interface UserBehaviorMetrics {
  pageViews: Record<string, number>
  timeSpent: Record<string, number>
  lastVisited: Record<string, number>
  scrollDepth: number
  interactions: number
}

export const useIntelligentPreload = (config: PreloadConfig) => {
  const router = useRouter()
  const [preloadedRoutes, setPreloadedRoutes] = useState<Set<string>>(new Set())
  const [userMetrics, setUserMetrics] = useState<UserBehaviorMetrics>({
    pageViews: {},
    timeSpent: {},
    lastVisited: {},
    scrollDepth: 0,
    interactions: 0
  })
  
  const startTime = useRef(Date.now())
  const intersectionObserver = useRef<IntersectionObserver>()

  // Load user behavior data from localStorage
  useEffect(() => {
    if (typeof window !== 'undefined') {
      const stored = localStorage.getItem('wingman_user_metrics')
      if (stored) {
        try {
          setUserMetrics(JSON.parse(stored))
        } catch (error) {
          console.warn('Failed to parse user metrics:', error)
        }
      }
    }
  }, [])

  // Save metrics to localStorage
  useEffect(() => {
    if (typeof window !== 'undefined') {
      localStorage.setItem('wingman_user_metrics', JSON.stringify(userMetrics))
    }
  }, [userMetrics])

  // Track page view
  useEffect(() => {
    const currentPath = window.location.pathname
    setUserMetrics(prev => ({
      ...prev,
      pageViews: {
        ...prev.pageViews,
        [currentPath]: (prev.pageViews[currentPath] || 0) + 1
      },
      lastVisited: {
        ...prev.lastVisited,
        [currentPath]: Date.now()
      }
    }))

    // Track time spent on page
    return () => {
      const timeSpent = Date.now() - startTime.current
      setUserMetrics(prev => ({
        ...prev,
        timeSpent: {
          ...prev.timeSpent,
          [currentPath]: (prev.timeSpent[currentPath] || 0) + timeSpent
        }
      }))
    }
  }, [])

  // Intelligent route scoring
  const getRouteScore = (route: string): number => {
    const pageViews = userMetrics.pageViews[route] || 0
    const timeSpent = userMetrics.timeSpent[route] || 0
    const lastVisited = userMetrics.lastVisited[route] || 0
    const recency = Date.now() - lastVisited

    // Score based on frequency, engagement, and recency
    const frequencyScore = Math.min(pageViews * 10, 50)
    const engagementScore = Math.min(timeSpent / 1000, 30) // seconds to score
    const recencyScore = Math.max(0, 20 - (recency / (1000 * 60 * 60 * 24))) // days

    return frequencyScore + engagementScore + recencyScore
  }

  // Preload a specific route
  const preloadRoute = (route: string) => {
    if (preloadedRoutes.has(route) || preloadedRoutes.size >= (config.maxPreloads || 5)) {
      return
    }

    try {
      router.prefetch(route)
      setPreloadedRoutes(prev => new Set([...prev, route]))
      
      // Analytics
      if (process.env.NODE_ENV === 'development') {
        console.log(`Preloaded route: ${route} (score: ${getRouteScore(route)})`)
      }
    } catch (error) {
      console.warn(`Failed to preload route ${route}:`, error)
    }
  }

  // Smart preloading based on user behavior
  useEffect(() => {
    const timer = setTimeout(() => {
      // Sort routes by predicted user interest
      const scoredRoutes = config.routes
        .map(route => ({ route, score: getRouteScore(route) }))
        .sort((a, b) => b.score - a.score)

      // Preload top-scoring routes
      scoredRoutes.slice(0, config.maxPreloads || 3).forEach(({ route }) => {
        preloadRoute(route)
      })
    }, config.delay || 2000)

    return () => clearTimeout(timer)
  }, [config.routes, userMetrics])

  // Hover-based preloading
  const handleLinkHover = (route: string) => {
    if (config.triggerOnHover && !preloadedRoutes.has(route)) {
      preloadRoute(route)
    }
  }

  // Scroll-based preloading
  useEffect(() => {
    if (!config.triggerOnScroll) return

    const handleScroll = () => {
      const scrollPercent = (window.scrollY / (document.body.scrollHeight - window.innerHeight)) * 100
      
      setUserMetrics(prev => ({
        ...prev,
        scrollDepth: Math.max(prev.scrollDepth, scrollPercent)
      }))

      // Preload next routes when user scrolls 70%
      if (scrollPercent > 70) {
        config.routes.slice(0, 2).forEach(preloadRoute)
      }
    }

    window.addEventListener('scroll', handleScroll, { passive: true })
    return () => window.removeEventListener('scroll', handleScroll)
  }, [config.triggerOnScroll, config.routes])

  // Intersection observer for link visibility
  useEffect(() => {
    if (!config.triggerOnHover) return

    intersectionObserver.current = new IntersectionObserver(
      (entries) => {
        entries.forEach(entry => {
          if (entry.isIntersecting) {
            const route = entry.target.getAttribute('data-route')
            if (route) {
              setTimeout(() => preloadRoute(route), 1000)
            }
          }
        })
      },
      { threshold: 0.5 }
    )

    return () => {
      intersectionObserver.current?.disconnect()
    }
  }, [config.triggerOnHover])

  // Enhanced link component with preloading
  const PreloadLink = ({ 
    href, 
    children, 
    className,
    priority = false,
    ...props 
  }: {
    href: string
    children: React.ReactNode
    className?: string
    priority?: boolean
    [key: string]: any
  }) => {
    const linkRef = useRef<HTMLAnchorElement>(null)

    useEffect(() => {
      if (priority) {
        preloadRoute(href)
      }

      if (config.triggerOnHover && linkRef.current) {
        intersectionObserver.current?.observe(linkRef.current)
      }

      return () => {
        if (linkRef.current) {
          intersectionObserver.current?.unobserve(linkRef.current)
        }
      }
    }, [href, priority])

    return React.createElement('a', {
      ref: linkRef,
      href,
      'data-route': href,
      className,
      onMouseEnter: () => handleLinkHover(href),
      onClick: (e: React.MouseEvent) => {
        e.preventDefault()
        setUserMetrics(prev => ({
          ...prev,
          interactions: prev.interactions + 1
        }))
        router.push(href)
      },
      ...props
    }, children)
  }

  // User flow prediction
  const predictNextRoute = (): string | null => {
    const currentPath = window.location.pathname
    
    // Common flow patterns
    const flowPatterns: Record<string, string[]> = {
      '/': ['/confidence-test', '/profile-setup'],
      '/confidence-test': ['/profile-setup', '/dating-goals'],
      '/profile-setup': ['/find-buddy', '/dating-goals'],
      '/find-buddy': ['/matches', '/buddy-chat'],
      '/matches': ['/buddy-chat', '/session'],
      '/dating-goals': ['/find-buddy', '/matches']
    }

    const possibleNext = flowPatterns[currentPath] || []
    if (possibleNext.length === 0) return null

    // Return highest-scoring next route
    return possibleNext
      .map(route => ({ route, score: getRouteScore(route) }))
      .sort((a, b) => b.score - a.score)[0]?.route || possibleNext[0]
  }

  // Preload predicted next route
  useEffect(() => {
    const nextRoute = predictNextRoute()
    if (nextRoute) {
      setTimeout(() => preloadRoute(nextRoute), 3000)
    }
  }, [userMetrics.pageViews])

  return {
    preloadRoute,
    preloadedRoutes: Array.from(preloadedRoutes),
    userMetrics,
    PreloadLink,
    predictNextRoute
  }
}

// High-priority routes for WingmanMatch user journey
export const CRITICAL_ROUTES = [
  '/confidence-test',
  '/profile-setup', 
  '/find-buddy',
  '/matches',
  '/dating-goals'
]

export const SECONDARY_ROUTES = [
  '/buddy-chat',
  '/session',
  '/auth/signin'
]

// Default preload configuration
export const DEFAULT_PRELOAD_CONFIG: PreloadConfig = {
  routes: [...CRITICAL_ROUTES, ...SECONDARY_ROUTES],
  delay: 2000,
  triggerOnHover: true,
  triggerOnScroll: true,
  maxPreloads: 5
}