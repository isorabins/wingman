/**
 * Smart Caching System for WingmanMatch
 * Phase 4: Intelligent caching with TTL and invalidation
 */

interface CacheItem<T> {
  data: T
  timestamp: number
  ttl: number
  key: string
  tags: string[]
  accessCount: number
  lastAccessed: number
}

interface CacheStats {
  hits: number
  misses: number
  evictions: number
  totalSize: number
  efficiency: number
}

interface CacheOptions {
  ttl?: number // Time to live in milliseconds
  tags?: string[] // For grouped invalidation
  priority?: 'low' | 'normal' | 'high'
  compress?: boolean
  serialize?: boolean
}

class SmartCache {
  private cache = new Map<string, CacheItem<any>>()
  private stats: CacheStats = {
    hits: 0,
    misses: 0,
    evictions: 0,
    totalSize: 0,
    efficiency: 0
  }
  private maxSize: number
  private cleanupInterval: number

  constructor(maxSize = 100, cleanupIntervalMs = 5 * 60 * 1000) {
    this.maxSize = maxSize
    this.cleanupInterval = cleanupIntervalMs
    
    // Start cleanup timer
    if (typeof window !== 'undefined') {
      setInterval(() => this.cleanup(), this.cleanupInterval)
    }
  }

  // Set item in cache
  set<T>(key: string, data: T, options: CacheOptions = {}): void {
    const {
      ttl = 30 * 60 * 1000, // 30 minutes default
      tags = [],
      priority = 'normal',
      compress = false,
      serialize = true
    } = options

    try {
      let processedData = data

      // Serialize if needed
      if (serialize && typeof data === 'object') {
        processedData = JSON.parse(JSON.stringify(data))
      }

      // Compress large objects (simplified)
      if (compress && this.getObjectSize(processedData) > 10000) {
        // In a real implementation, you'd use LZ compression
        processedData = this.simpleCompress(processedData)
      }

      const item: CacheItem<T> = {
        data: processedData,
        timestamp: Date.now(),
        ttl,
        key,
        tags: [...tags, `priority:${priority}`],
        accessCount: 0,
        lastAccessed: Date.now()
      }

      // Evict if necessary
      if (this.cache.size >= this.maxSize) {
        this.evictLRU()
      }

      this.cache.set(key, item)
      this.updateStats()
    } catch (error) {
      console.warn('Cache set failed:', error)
    }
  }

  // Get item from cache
  get<T>(key: string): T | null {
    const item = this.cache.get(key) as CacheItem<T> | undefined

    if (!item) {
      this.stats.misses++
      this.updateStats()
      return null
    }

    // Check if expired
    if (this.isExpired(item)) {
      this.cache.delete(key)
      this.stats.misses++
      this.updateStats()
      return null
    }

    // Update access stats
    item.accessCount++
    item.lastAccessed = Date.now()
    
    this.stats.hits++
    this.updateStats()

    // Decompress if needed
    if (this.isCompressed(item.data)) {
      return this.simpleDecompress(item.data)
    }

    return item.data
  }

  // Check if key exists and is valid
  has(key: string): boolean {
    const item = this.cache.get(key)
    return item ? !this.isExpired(item) : false
  }

  // Delete specific key
  delete(key: string): boolean {
    return this.cache.delete(key)
  }

  // Clear all cache
  clear(): void {
    this.cache.clear()
    this.stats = {
      hits: 0,
      misses: 0,
      evictions: 0,
      totalSize: 0,
      efficiency: 0
    }
  }

  // Invalidate by tags
  invalidateByTag(tag: string): number {
    let invalidated = 0
    
    for (const [key, item] of this.cache.entries()) {
      if (item.tags.includes(tag)) {
        this.cache.delete(key)
        invalidated++
      }
    }

    this.updateStats()
    return invalidated
  }

  // Invalidate by pattern
  invalidateByPattern(pattern: RegExp): number {
    let invalidated = 0
    
    for (const [key] of this.cache.entries()) {
      if (pattern.test(key)) {
        this.cache.delete(key)
        invalidated++
      }
    }

    this.updateStats()
    return invalidated
  }

  // Get cache statistics
  getStats(): CacheStats & { keys: string[] } {
    return {
      ...this.stats,
      keys: Array.from(this.cache.keys())
    }
  }

  // Export cache data for persistence
  export(): Record<string, any> {
    const exported: Record<string, any> = {}
    
    for (const [key, item] of this.cache.entries()) {
      if (!this.isExpired(item)) {
        exported[key] = {
          data: item.data,
          timestamp: item.timestamp,
          ttl: item.ttl,
          tags: item.tags
        }
      }
    }

    return exported
  }

  // Import cache data from persistence
  import(data: Record<string, any>): void {
    for (const [key, item] of Object.entries(data)) {
      if (item && typeof item === 'object') {
        const cacheItem: CacheItem<any> = {
          key,
          data: item.data,
          timestamp: item.timestamp || Date.now(),
          ttl: item.ttl || 30 * 60 * 1000,
          tags: item.tags || [],
          accessCount: 0,
          lastAccessed: Date.now()
        }

        if (!this.isExpired(cacheItem)) {
          this.cache.set(key, cacheItem)
        }
      }
    }

    this.updateStats()
  }

  // Prefetch data with intelligent loading
  async prefetch<T>(
    key: string, 
    loader: () => Promise<T>, 
    options: CacheOptions = {}
  ): Promise<T> {
    // Check if already cached
    const cached = this.get<T>(key)
    if (cached !== null) {
      return cached
    }

    try {
      const data = await loader()
      this.set(key, data, options)
      return data
    } catch (error) {
      console.warn(`Prefetch failed for key ${key}:`, error)
      throw error
    }
  }

  // Batch operations
  setMany(items: Array<{ key: string; data: any; options?: CacheOptions }>): void {
    for (const item of items) {
      this.set(item.key, item.data, item.options)
    }
  }

  getMany<T>(keys: string[]): Array<{ key: string; data: T | null }> {
    return keys.map(key => ({
      key,
      data: this.get<T>(key)
    }))
  }

  // Private helper methods
  private isExpired(item: CacheItem<any>): boolean {
    return Date.now() - item.timestamp > item.ttl
  }

  private evictLRU(): void {
    let oldestKey = ''
    let oldestTime = Date.now()

    for (const [key, item] of this.cache.entries()) {
      if (item.lastAccessed < oldestTime) {
        oldestTime = item.lastAccessed
        oldestKey = key
      }
    }

    if (oldestKey) {
      this.cache.delete(oldestKey)
      this.stats.evictions++
    }
  }

  private cleanup(): void {
    const now = Date.now()
    const toDelete: string[] = []

    for (const [key, item] of this.cache.entries()) {
      if (now - item.timestamp > item.ttl) {
        toDelete.push(key)
      }
    }

    for (const key of toDelete) {
      this.cache.delete(key)
    }

    this.updateStats()
  }

  private updateStats(): void {
    this.stats.totalSize = this.cache.size
    this.stats.efficiency = this.stats.hits / (this.stats.hits + this.stats.misses) || 0
  }

  private getObjectSize(obj: any): number {
    return JSON.stringify(obj).length
  }

  private simpleCompress(data: any): any {
    // Simplified compression - in production use proper compression
    return {
      __compressed: true,
      data: JSON.stringify(data)
    }
  }

  private simpleDecompress(data: any): any {
    if (this.isCompressed(data)) {
      return JSON.parse(data.data)
    }
    return data
  }

  private isCompressed(data: any): boolean {
    return data && typeof data === 'object' && data.__compressed === true
  }
}

// Specialized caches for WingmanMatch
export class WingmanCacheManager {
  private static instance: WingmanCacheManager
  private profileCache = new SmartCache(50) // User profiles
  private assessmentCache = new SmartCache(30) // Assessment data
  private matchCache = new SmartCache(100) // Match data
  private apiCache = new SmartCache(200) // API responses
  private assetCache = new SmartCache(500) // Static assets

  static getInstance(): WingmanCacheManager {
    if (!WingmanCacheManager.instance) {
      WingmanCacheManager.instance = new WingmanCacheManager()
    }
    return WingmanCacheManager.instance
  }

  // Profile caching
  setProfile(userId: string, profile: any): void {
    this.profileCache.set(`profile:${userId}`, profile, {
      ttl: 60 * 60 * 1000, // 1 hour
      tags: ['profile', 'user-data'],
      priority: 'high'
    })
  }

  getProfile(userId: string): any {
    return this.profileCache.get(`profile:${userId}`)
  }

  // Assessment caching
  setAssessmentProgress(userId: string, progress: any): void {
    this.assessmentCache.set(`assessment:${userId}`, progress, {
      ttl: 24 * 60 * 60 * 1000, // 24 hours
      tags: ['assessment', 'progress'],
      priority: 'high'
    })
  }

  getAssessmentProgress(userId: string): any {
    return this.assessmentCache.get(`assessment:${userId}`)
  }

  // Match caching
  setMatches(userId: string, matches: any[]): void {
    this.matchCache.set(`matches:${userId}`, matches, {
      ttl: 10 * 60 * 1000, // 10 minutes
      tags: ['matches', 'user-data'],
      priority: 'normal'
    })
  }

  getMatches(userId: string): any[] | null {
    return this.matchCache.get(`matches:${userId}`)
  }

  // API response caching
  setApiResponse(endpoint: string, params: any, response: any): void {
    const key = `api:${endpoint}:${JSON.stringify(params)}`
    this.apiCache.set(key, response, {
      ttl: 5 * 60 * 1000, // 5 minutes
      tags: ['api', endpoint.split('/')[1]],
      priority: 'normal'
    })
  }

  getApiResponse(endpoint: string, params: any): any {
    const key = `api:${endpoint}:${JSON.stringify(params)}`
    return this.apiCache.get(key)
  }

  // Asset caching
  setAsset(url: string, data: any): void {
    this.assetCache.set(`asset:${url}`, data, {
      ttl: 24 * 60 * 60 * 1000, // 24 hours
      tags: ['assets', 'static'],
      priority: 'low'
    })
  }

  getAsset(url: string): any {
    return this.assetCache.get(`asset:${url}`)
  }

  // Cache invalidation
  invalidateUser(userId: string): void {
    this.profileCache.invalidateByPattern(new RegExp(`^profile:${userId}`))
    this.assessmentCache.invalidateByPattern(new RegExp(`^assessment:${userId}`))
    this.matchCache.invalidateByPattern(new RegExp(`^matches:${userId}`))
  }

  invalidateAssessments(): void {
    this.assessmentCache.invalidateByTag('assessment')
  }

  invalidateMatches(): void {
    this.matchCache.invalidateByTag('matches')
  }

  // Analytics and debugging
  getCacheStats(): Record<string, any> {
    return {
      profile: this.profileCache.getStats(),
      assessment: this.assessmentCache.getStats(),
      match: this.matchCache.getStats(),
      api: this.apiCache.getStats(),
      asset: this.assetCache.getStats(),
    }
  }

  // Persistence (localStorage)
  exportToStorage(): void {
    if (typeof window !== 'undefined') {
      try {
        const data = {
          profile: this.profileCache.export(),
          assessment: this.assessmentCache.export(),
          match: this.matchCache.export(),
          api: this.apiCache.export(),
          timestamp: Date.now()
        }
        localStorage.setItem('wingman_cache', JSON.stringify(data))
      } catch (error) {
        console.warn('Cache export failed:', error)
      }
    }
  }

  importFromStorage(): void {
    if (typeof window !== 'undefined') {
      try {
        const stored = localStorage.getItem('wingman_cache')
        if (stored) {
          const data = JSON.parse(stored)
          
          // Check if data is recent (not older than 24 hours)
          if (Date.now() - data.timestamp < 24 * 60 * 60 * 1000) {
            this.profileCache.import(data.profile || {})
            this.assessmentCache.import(data.assessment || {})
            this.matchCache.import(data.match || {})
            this.apiCache.import(data.api || {})
          }
        }
      } catch (error) {
        console.warn('Cache import failed:', error)
      }
    }
  }
}

// Export singleton instance
export const cacheManager = WingmanCacheManager.getInstance()

// Auto-save to localStorage every 5 minutes
if (typeof window !== 'undefined') {
  setInterval(() => {
    cacheManager.exportToStorage()
  }, 5 * 60 * 1000)

  // Load from localStorage on startup
  cacheManager.importFromStorage()
}