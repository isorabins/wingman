"use client"

import { useEffect } from 'react'
import { PerformanceMonitor } from '../lib/performance/monitor'
import { useIntelligentPreload } from '../hooks/useIntelligentPreload'

export default function PerformanceTracker() {
  // Initialize intelligent preloading
  useIntelligentPreload()

  useEffect(() => {
    // Initialize performance monitoring
    PerformanceMonitor.initialize()

    // Track page load performance
    const trackPageLoad = () => {
      if (document.readyState === 'complete') {
        setTimeout(() => {
          const navigationTiming = PerformanceMonitor.getNavigationTiming()
          const bundleInfo = PerformanceMonitor.getBundleSize()
          
          if (process.env.NODE_ENV === 'development') {
            console.log('📊 Page Load Performance:', {
              loadTime: navigationTiming?.loadTime,
              domContentLoaded: navigationTiming?.domContentLoaded,
              timeToInteractive: navigationTiming?.timeToInteractive,
              bundleSize: `${(bundleInfo.totalSize / 1024).toFixed(2)} KB`,
              chunks: bundleInfo.chunks.length
            })
          }
        }, 1000) // Wait for metrics to stabilize
      } else {
        window.addEventListener('load', trackPageLoad, { once: true })
      }
    }

    trackPageLoad()

    // Track route changes for SPA navigation
    let lastUrl = window.location.href
    const observer = new MutationObserver(() => {
      const currentUrl = window.location.href
      if (currentUrl !== lastUrl) {
        lastUrl = currentUrl
        
        // Track SPA navigation performance
        setTimeout(() => {
          if (process.env.NODE_ENV === 'development') {
            console.log('🔄 SPA Navigation:', {
              url: currentUrl,
              timestamp: Date.now()
            })
          }
        }, 100)
      }
    })

    observer.observe(document, { subtree: true, childList: true })

    // Performance budget monitoring
    const checkPerformanceBudget = () => {
      const metrics = PerformanceMonitor.getMetrics()
      const bundleInfo = PerformanceMonitor.getBundleSize()
      
      const violations = []
      
      // Check Core Web Vitals
      const fcp = metrics.find(m => m.name === 'FCP')
      const lcp = metrics.find(m => m.name === 'LCP')
      const cls = metrics.find(m => m.name === 'CLS')
      const fid = metrics.find(m => m.name === 'FID')
      
      if (fcp && fcp.value > 1500) violations.push(`FCP: ${fcp.value.toFixed(0)}ms > 1500ms`)
      if (lcp && lcp.value > 2500) violations.push(`LCP: ${lcp.value.toFixed(0)}ms > 2500ms`)
      if (cls && cls.value > 0.1) violations.push(`CLS: ${cls.value.toFixed(3)} > 0.1`)
      if (fid && fid.value > 100) violations.push(`FID: ${fid.value.toFixed(0)}ms > 100ms`)
      
      // Check bundle size
      const bundleSizeKB = bundleInfo.totalSize / 1024
      if (bundleSizeKB > 250) violations.push(`Bundle: ${bundleSizeKB.toFixed(0)}KB > 250KB`)
      
      if (violations.length > 0 && process.env.NODE_ENV === 'development') {
        console.warn('⚠️ Performance Budget Violations:', violations)
      }
    }

    // Check budget after initial load
    setTimeout(checkPerformanceBudget, 5000)

    // Cleanup
    return () => {
      observer.disconnect()
    }
  }, [])

  useEffect(() => {
    // Report performance metrics on page unload (for analytics)
    const handleBeforeUnload = () => {
      const report = PerformanceMonitor.generateReport()
      
      // In production, this would send to analytics
      if (process.env.NODE_ENV === 'development') {
        console.log('📈 Performance Report on Unload:', report)
      }
      
      // Example: Send to analytics service
      // analytics.track('page_performance', {
      //   metrics: PerformanceMonitor.getMetrics(),
      //   bundleInfo: PerformanceMonitor.getBundleSize(),
      //   navigationTiming: PerformanceMonitor.getNavigationTiming()
      // })
    }

    window.addEventListener('beforeunload', handleBeforeUnload)
    
    return () => {
      window.removeEventListener('beforeunload', handleBeforeUnload)
    }
  }, [])

  // Performance tracker is invisible - only runs monitoring logic
  return null
}