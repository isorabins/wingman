/**
 * Service Worker for WingmanMatch
 * Phase 5: Caching strategy and offline support
 */

const CACHE_NAME = 'wingman-v1'
const STATIC_CACHE = 'wingman-static-v1'
const DYNAMIC_CACHE = 'wingman-dynamic-v1'

// Critical assets to precache
const PRECACHE_ASSETS = [
  '/',
  '/confidence-test',
  '/profile-setup',
  '/find-buddy',
  '/matches',
  '/dating-goals',
  // Static assets
  '/manifest.json',
  '/api/static/confidence-test/questions.v1.json',
  // Critical chunks (will be added during build)
]

// API routes to cache
const API_CACHE_PATTERNS = [
  /^\/api\/confidence-test/,
  /^\/api\/profile/,
  /^\/api\/matches/,
  /^\/api\/dating-goals/,
]

// Static file patterns
const STATIC_FILE_PATTERNS = [
  /\.(?:js|css|woff2?|png|jpg|jpeg|webp|svg|ico)$/,
]

// Cache strategies
const CACHE_STRATEGIES = {
  CACHE_FIRST: 'cache-first',
  NETWORK_FIRST: 'network-first',
  STALE_WHILE_REVALIDATE: 'stale-while-revalidate',
  NETWORK_ONLY: 'network-only',
  CACHE_ONLY: 'cache-only'
}

// Route-specific caching strategies
const ROUTE_STRATEGIES = new Map([
  // Static assets - cache first
  [STATIC_FILE_PATTERNS, CACHE_STRATEGIES.CACHE_FIRST],
  // API routes - network first with fallback
  [API_CACHE_PATTERNS, CACHE_STRATEGIES.NETWORK_FIRST],
  // HTML pages - stale while revalidate
  [/\/$/, CACHE_STRATEGIES.STALE_WHILE_REVALIDATE],
])

// Performance metrics
let performanceMetrics = {
  cacheHits: 0,
  cacheMisses: 0,
  networkRequests: 0,
  offlineRequests: 0
}

// Install event - precache critical assets
self.addEventListener('install', event => {
  console.log('SW: Installing service worker')
  
  event.waitUntil(
    Promise.all([
      // Precache static assets
      caches.open(STATIC_CACHE).then(cache => {
        console.log('SW: Precaching static assets')
        return cache.addAll(PRECACHE_ASSETS)
      }),
      // Skip waiting for old service worker
      self.skipWaiting()
    ])
  )
})

// Activate event - cleanup old caches
self.addEventListener('activate', event => {
  console.log('SW: Activating service worker')
  
  event.waitUntil(
    Promise.all([
      // Clean up old caches
      caches.keys().then(cacheNames => {
        return Promise.all(
          cacheNames
            .filter(cacheName => 
              cacheName !== CACHE_NAME && 
              cacheName !== STATIC_CACHE && 
              cacheName !== DYNAMIC_CACHE
            )
            .map(cacheName => {
              console.log('SW: Deleting old cache:', cacheName)
              return caches.delete(cacheName)
            })
        )
      }),
      // Take control of all clients
      self.clients.claim()
    ])
  )
})

// Fetch event - implement caching strategies
self.addEventListener('fetch', event => {
  const { request } = event
  const url = new URL(request.url)

  // Skip non-GET requests
  if (request.method !== 'GET') {
    return
  }

  // Skip chrome-extension and other protocols
  if (!url.protocol.startsWith('http')) {
    return
  }

  event.respondWith(handleRequest(request))
})

// Request handler with caching strategies
async function handleRequest(request) {
  const url = new URL(request.url)
  const strategy = getStrategyForRequest(request)

  try {
    switch (strategy) {
      case CACHE_STRATEGIES.CACHE_FIRST:
        return await cacheFirst(request)
      
      case CACHE_STRATEGIES.NETWORK_FIRST:
        return await networkFirst(request)
      
      case CACHE_STRATEGIES.STALE_WHILE_REVALIDATE:
        return await staleWhileRevalidate(request)
      
      case CACHE_STRATEGIES.NETWORK_ONLY:
        performanceMetrics.networkRequests++
        return await fetch(request)
      
      case CACHE_STRATEGIES.CACHE_ONLY:
        return await cacheOnly(request)
      
      default:
        return await networkFirst(request)
    }
  } catch (error) {
    console.warn('SW: Request failed:', error)
    return await handleOfflineRequest(request)
  }
}

// Determine caching strategy for request
function getStrategyForRequest(request) {
  const url = new URL(request.url)
  
  // Check static file patterns
  for (const [patterns, strategy] of ROUTE_STRATEGIES) {
    if (Array.isArray(patterns)) {
      if (patterns.some(pattern => pattern.test(url.pathname))) {
        return strategy
      }
    } else if (patterns.test(url.pathname)) {
      return strategy
    }
  }

  // Default strategy
  return CACHE_STRATEGIES.NETWORK_FIRST
}

// Cache-first strategy
async function cacheFirst(request) {
  const cache = await caches.open(STATIC_CACHE)
  const cached = await cache.match(request)
  
  if (cached) {
    performanceMetrics.cacheHits++
    return cached
  }

  performanceMetrics.cacheMisses++
  const response = await fetch(request)
  
  if (response.ok) {
    cache.put(request, response.clone())
  }
  
  return response
}

// Network-first strategy
async function networkFirst(request) {
  const cache = await caches.open(DYNAMIC_CACHE)
  
  try {
    performanceMetrics.networkRequests++
    const response = await fetch(request)
    
    if (response.ok) {
      // Cache successful responses
      cache.put(request, response.clone())
    }
    
    return response
  } catch (error) {
    // Fallback to cache
    const cached = await cache.match(request)
    if (cached) {
      performanceMetrics.cacheHits++
      return cached
    }
    throw error
  }
}

// Stale while revalidate strategy
async function staleWhileRevalidate(request) {
  const cache = await caches.open(DYNAMIC_CACHE)
  const cached = await cache.match(request)
  
  // Fetch in background
  const fetchPromise = fetch(request)
    .then(response => {
      if (response.ok) {
        cache.put(request, response.clone())
      }
      return response
    })
    .catch(() => {})

  // Return cached version immediately if available
  if (cached) {
    performanceMetrics.cacheHits++
    return cached
  }

  // Otherwise wait for network
  performanceMetrics.networkRequests++
  return await fetchPromise
}

// Cache-only strategy
async function cacheOnly(request) {
  const cache = await caches.open(STATIC_CACHE)
  const cached = await cache.match(request)
  
  if (cached) {
    performanceMetrics.cacheHits++
    return cached
  }
  
  throw new Error('Resource not in cache')
}

// Offline request handler
async function handleOfflineRequest(request) {
  const url = new URL(request.url)
  performanceMetrics.offlineRequests++
  
  // Try to find in any cache
  const cacheNames = await caches.keys()
  for (const cacheName of cacheNames) {
    const cache = await caches.open(cacheName)
    const cached = await cache.match(request)
    if (cached) {
      return cached
    }
  }

  // Return offline page for HTML requests
  if (request.headers.get('accept')?.includes('text/html')) {
    return new Response(`
      <!DOCTYPE html>
      <html>
        <head>
          <title>Wingman - Offline</title>
          <meta name="viewport" content="width=device-width, initial-scale=1">
          <style>
            body { 
              font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
              text-align: center; 
              padding: 50px;
              background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
              color: white;
              margin: 0;
            }
            .container { max-width: 400px; margin: 0 auto; }
            h1 { font-size: 2em; margin-bottom: 1em; }
            p { font-size: 1.1em; line-height: 1.5; margin-bottom: 2em; }
            .retry-btn {
              background: rgba(255,255,255,0.2);
              border: 2px solid white;
              color: white;
              padding: 12px 24px;
              border-radius: 25px;
              cursor: pointer;
              font-size: 1em;
              transition: background 0.3s;
            }
            .retry-btn:hover { background: rgba(255,255,255,0.3); }
          </style>
        </head>
        <body>
          <div class="container">
            <h1>You're Offline</h1>
            <p>It looks like you've lost your internet connection. Some features may not be available, but you can still browse cached content.</p>
            <button class="retry-btn" onclick="window.location.reload()">Try Again</button>
          </div>
        </body>
      </html>
    `, {
      status: 200,
      headers: { 'Content-Type': 'text/html' }
    })
  }

  // Return 503 for other requests
  return new Response('Service Unavailable', { status: 503 })
}

// Message handler for cache management
self.addEventListener('message', event => {
  const { type, payload } = event.data
  
  switch (type) {
    case 'GET_CACHE_STATUS':
      event.ports[0].postMessage({
        caches: {
          static: STATIC_CACHE,
          dynamic: DYNAMIC_CACHE
        },
        metrics: performanceMetrics
      })
      break
      
    case 'CLEAR_CACHE':
      Promise.all([
        caches.delete(DYNAMIC_CACHE),
        payload?.clearStatic && caches.delete(STATIC_CACHE)
      ]).then(() => {
        event.ports[0].postMessage({ success: true })
      })
      break
      
    case 'PRECACHE_ROUTES':
      if (payload?.routes) {
        const cache = caches.open(DYNAMIC_CACHE)
        cache.then(c => c.addAll(payload.routes))
          .then(() => event.ports[0].postMessage({ success: true }))
          .catch(error => event.ports[0].postMessage({ error: error.message }))
      }
      break
  }
})

// Background sync for offline actions
self.addEventListener('sync', event => {
  if (event.tag === 'background-sync') {
    event.waitUntil(handleBackgroundSync())
  }
})

async function handleBackgroundSync() {
  // Handle queued offline actions
  console.log('SW: Performing background sync')
  
  // This would handle things like:
  // - Queued form submissions
  // - Cached API requests
  // - Analytics events
}

// Performance optimization: Preload critical routes
self.addEventListener('message', event => {
  if (event.data && event.data.type === 'PRELOAD_ROUTE') {
    const { route } = event.data
    const request = new Request(route)
    handleRequest(request)
  }
})

console.log('SW: Service worker script loaded')