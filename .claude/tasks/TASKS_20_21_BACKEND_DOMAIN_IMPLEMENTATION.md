# Tasks 20 & 21 Backend Domain Implementation Plan

## Mission: Complete Safety & Location Privacy Backend Systems

Implement comprehensive backend domains for Tasks 20 (Safety and Reporting) and Task 21 (Location Privacy) with security-first architecture, production-ready moderation systems, and enhanced matching algorithms with privacy controls.

## Architecture Context

**Existing Infrastructure:**
- FastAPI + Supabase PostgreSQL with RLS policies
- Redis-based rate limiting with TokenBucket algorithm
- Email notification system (Resend) with template support
- Haversine distance calculations with user_locations table
- Existing matching algorithm in WingmanMatcher service
- Comprehensive error handling and authentication patterns

**Database Schema Foundation:**
- `user_profiles` - Core user data with RLS policies
- `user_locations` - Geographic data with privacy modes
- `wingman_matches` - Match relationships with status tracking
- `chat_messages` - Messaging system with participant validation

## Task 20 Backend Domain: Safety & Reporting System

### 1. Database Schema Implementation

**New Tables:**
```sql
-- Moderation reports with comprehensive tracking
CREATE TABLE user_reports (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    reporter_id UUID NOT NULL REFERENCES user_profiles(id) ON DELETE CASCADE,
    reported_id UUID NOT NULL REFERENCES user_profiles(id) ON DELETE CASCADE,
    report_type TEXT NOT NULL CHECK (report_type IN ('harassment', 'inappropriate_content', 'fake_profile', 'safety_concern', 'spam', 'other')),
    message TEXT NOT NULL CHECK (length(message) >= 10 AND length(message) <= 1000),
    evidence_data JSONB DEFAULT '{}', -- Screenshots, conversation excerpts
    status TEXT NOT NULL DEFAULT 'pending' CHECK (status IN ('pending', 'under_review', 'resolved', 'dismissed')),
    priority TEXT NOT NULL DEFAULT 'medium' CHECK (priority IN ('low', 'medium', 'high', 'urgent')),
    resolution_notes TEXT,
    resolved_by UUID REFERENCES user_profiles(id),
    resolved_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- User blocks for immediate protection
CREATE TABLE user_blocks (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    blocker_id UUID NOT NULL REFERENCES user_profiles(id) ON DELETE CASCADE,
    blocked_id UUID NOT NULL REFERENCES user_profiles(id) ON DELETE CASCADE,
    block_reason TEXT CHECK (block_reason IN ('harassment', 'uncomfortable', 'not_interested', 'safety', 'other')),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(blocker_id, blocked_id)
);

-- Content moderation for message filtering
CREATE TABLE content_moderation (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    content_type TEXT NOT NULL CHECK (content_type IN ('message', 'profile_bio', 'profile_photo')),
    content_id UUID NOT NULL, -- References message_id, user_id, etc.
    flagged_content TEXT NOT NULL,
    moderation_result JSONB NOT NULL DEFAULT '{}', -- Profanity, toxicity scores
    action_taken TEXT CHECK (action_taken IN ('none', 'warned', 'filtered', 'blocked', 'removed')),
    moderator_id UUID REFERENCES user_profiles(id),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
```

**RLS Policies:**
```sql
-- Reports: Users can create reports, admins can view all
CREATE POLICY "users_can_create_reports" ON user_reports FOR INSERT WITH CHECK (auth.uid()::text = reporter_id::text);
CREATE POLICY "users_can_view_own_reports" ON user_reports FOR SELECT USING (auth.uid()::text = reporter_id::text);
CREATE POLICY "admins_can_view_all_reports" ON user_reports FOR ALL USING (auth.jwt() ->> 'role' = 'admin');

-- Blocks: Users can manage their own blocks
CREATE POLICY "users_can_manage_blocks" ON user_blocks FOR ALL USING (auth.uid()::text = blocker_id::text);

-- Content moderation: Admin access only
CREATE POLICY "admin_only_content_moderation" ON content_moderation FOR ALL USING (auth.jwt() ->> 'role' = 'admin');
```

### 2. API Endpoints Implementation

**Core Safety Endpoints:**
```python
# POST /api/user/block - Block another user
@app.post("/api/user/block")
async def block_user(request: BlockUserRequest, current_user: dict = Depends(get_current_user)):
    """Block user and remove from matching algorithm"""

# POST /api/user/report - Report user for moderation
@app.post("/api/user/report") 
async def report_user(request: ReportUserRequest, current_user: dict = Depends(get_current_user)):
    """Report user with evidence and trigger moderation workflow"""

# GET /api/user/blocks - List blocked users
@app.get("/api/user/blocks")
async def get_blocked_users(current_user: dict = Depends(get_current_user)):
    """Retrieve user's block list for frontend management"""

# DELETE /api/user/block/{blocked_id} - Unblock user
@app.delete("/api/user/block/{blocked_id}")
async def unblock_user(blocked_id: str, current_user: dict = Depends(get_current_user)):
    """Remove block and allow matching again"""
```

### 3. Safety-Enhanced Matching Algorithm

**WingmanMatcher Integration:**
```python
# Enhanced matching with safety filters
async def find_safe_match(user_id: str) -> Optional[WingmanMatch]:
    """Find match excluding blocked users and reported accounts"""
    
    # Get user's block list
    blocks = await get_user_blocks(user_id)
    blocked_user_ids = [block.blocked_id for block in blocks]
    
    # Get users who blocked this user
    blocked_by = await get_blocked_by_users(user_id)
    
    # Exclude from matching algorithm
    excluded_users = set(blocked_user_ids + blocked_by + [user_id])
    
    # Apply geographic and experience filters with safety exclusions
    candidates = await find_candidates_with_safety_filter(user_id, excluded_users)
    
    return select_best_match(candidates)
```

### 4. Content Filtering System

**Profanity Filter Implementation:**
```python
class ContentModerator:
    """Local content moderation without external APIs"""
    
    def __init__(self):
        self.profanity_words = self._load_profanity_list()
        self.harassment_patterns = self._load_harassment_patterns()
    
    async def moderate_message(self, message: str, user_id: str) -> ModerationResult:
        """Moderate chat message for inappropriate content"""
        
        # Check profanity
        profanity_score = self._check_profanity(message)
        
        # Check harassment patterns
        harassment_score = self._check_harassment(message)
        
        # Determine action
        if profanity_score > 0.8 or harassment_score > 0.7:
            return ModerationResult(action="block", filtered_message=self._filter_content(message))
        elif profanity_score > 0.5:
            return ModerationResult(action="filter", filtered_message=self._filter_content(message))
        
        return ModerationResult(action="allow", filtered_message=message)
```

### 5. Rate Limiting Enhancement

**Message Rate Limiting:**
```python
# Enhanced rate limiting for chat messages
CHAT_RATE_LIMITS = {
    "/api/chat/send": RateLimitConfig(
        requests=1,  # 1 message
        window_seconds=0.5,  # per 0.5 seconds
        burst_allowance=3  # allow burst of 3
    )
}

# Report/block rate limiting
SAFETY_RATE_LIMITS = {
    "/api/user/report": RateLimitConfig(
        requests=5,  # 5 reports
        window_seconds=3600,  # per hour
        burst_allowance=7
    ),
    "/api/user/block": RateLimitConfig(
        requests=10,  # 10 blocks
        window_seconds=3600,  # per hour  
        burst_allowance=15
    )
}
```

## Task 21 Backend Domain: Location Privacy System

### 1. Enhanced Location Schema

**user_locations Table Enhancement:**
```sql
-- Add privacy and travel preference columns
ALTER TABLE user_locations ADD COLUMN IF NOT EXISTS privacy_mode TEXT DEFAULT 'precise' CHECK (privacy_mode IN ('precise', 'city_only', 'hidden'));
ALTER TABLE user_locations ADD COLUMN IF NOT EXISTS max_travel_miles INTEGER DEFAULT 25 CHECK (max_travel_miles >= 5 AND max_travel_miles <= 100);
ALTER TABLE user_locations ADD COLUMN IF NOT EXISTS location_sharing_consent BOOLEAN DEFAULT false;
ALTER TABLE user_locations ADD COLUMN IF NOT EXISTS last_location_update TIMESTAMP WITH TIME ZONE DEFAULT NOW();
ALTER TABLE user_locations ADD COLUMN IF NOT EXISTS auto_update_enabled BOOLEAN DEFAULT false;

-- Add index for privacy-aware queries
CREATE INDEX IF NOT EXISTS idx_user_locations_privacy ON user_locations(privacy_mode, max_travel_miles);
```

### 2. Privacy-Aware Distance API

**Enhanced Distance Service:**
```python
class PrivacyAwareDistanceService:
    """Distance calculations respecting user privacy settings"""
    
    async def find_candidates_with_privacy(
        self, 
        user_id: str, 
        respect_privacy: bool = True
    ) -> List[BuddyCandidate]:
        """Find candidates respecting privacy preferences"""
        
        user_location = await self.get_user_location_with_privacy(user_id)
        if not user_location:
            return []
        
        # Query based on user's travel preference
        radius_miles = user_location.max_travel_miles
        
        # Privacy-aware candidate search
        candidates = await self._search_with_privacy_filter(
            user_id=user_id,
            user_lat=user_location.lat,
            user_lng=user_location.lng,
            radius_miles=radius_miles,
            privacy_mode=user_location.privacy_mode
        )
        
        return candidates
    
    async def _search_with_privacy_filter(self, **kwargs) -> List[BuddyCandidate]:
        """Search respecting both user's and candidates' privacy settings"""
        
        # Build query excluding hidden users
        query = """
        SELECT 
            ul.user_id,
            ul.city,
            up.experience_level,
            up.confidence_archetype,
            CASE 
                WHEN ul.privacy_mode = 'precise' THEN 
                    public.haversine_miles(%s, %s, ul.lat, ul.lng)
                WHEN ul.privacy_mode = 'city_only' THEN
                    CASE WHEN ul.city = %s THEN 5.0 ELSE 50.0 END
                ELSE 999.0  -- hidden users get max distance
            END as distance_miles
        FROM public.user_locations ul
        JOIN public.user_profiles up ON ul.user_id = up.id
        WHERE 
            ul.user_id != %s
            AND ul.privacy_mode != 'hidden'
            AND up.experience_level IS NOT NULL
            AND distance_miles <= %s
        ORDER BY distance_miles ASC
        LIMIT 20
        """
        
        # Execute privacy-aware search
        return await self._execute_privacy_search(query, kwargs)
```

### 3. Location Privacy API

**Privacy Control Endpoints:**
```python
# PUT /api/user/location/privacy - Update privacy settings
@app.put("/api/user/location/privacy")
async def update_location_privacy(
    request: LocationPrivacyRequest, 
    current_user: dict = Depends(get_current_user)
):
    """Update user location privacy preferences"""

# GET /api/user/location/privacy - Get privacy settings  
@app.get("/api/user/location/privacy")
async def get_location_privacy(current_user: dict = Depends(get_current_user)):
    """Retrieve current location privacy settings"""

# POST /api/user/location/update - Periodic location update
@app.post("/api/user/location/update")
async def update_user_location(
    request: LocationUpdateRequest,
    current_user: dict = Depends(get_current_user)
):
    """Update user location with consent verification"""
```

### 4. Enhanced Matching with Privacy

**Privacy-Integrated WingmanMatcher:**
```python
class PrivacyAwareWingmanMatcher(WingmanMatcher):
    """Enhanced matcher respecting location privacy"""
    
    async def create_auto_match_with_privacy(self, user_id: str) -> Optional[WingmanMatch]:
        """Create match respecting all privacy preferences"""
        
        # Get user privacy settings
        privacy_settings = await self.get_user_privacy_settings(user_id)
        
        # Apply privacy filters to candidate search
        candidates = await self.distance_service.find_candidates_with_privacy(
            user_id=user_id,
            respect_privacy=True
        )
        
        # Filter by experience level and recency (existing logic)
        filtered_candidates = await self.apply_experience_and_recency_filters(
            user_id, candidates
        )
        
        # Apply safety filters (Task 20 integration)
        safe_candidates = await self.apply_safety_filters(user_id, filtered_candidates)
        
        # Select best match with privacy compatibility
        return await self.select_privacy_compatible_match(user_id, safe_candidates)
```

## Integration Points

### 1. Email Notification Enhancement

**Safety-Related Notifications:**
```python
# Integrate with existing email service
async def send_safety_notification(user_email: str, notification_type: str, details: dict):
    """Send safety-related email notifications"""
    
    templates = {
        "report_received": "Your report has been received and is under review",
        "action_taken": "Action has been taken on your report", 
        "account_flagged": "Your account requires attention",
        "safety_reminder": "Safety tips for your upcoming wingman session"
    }
    
    await email_service.send_safety_notification(user_email, templates[notification_type], details)
```

### 2. Chat System Integration

**Safety-Enhanced Chat:**
```python
# Enhance existing chat endpoints with safety checks
@app.post("/api/chat/send")
async def send_message_with_safety(request: ChatMessageRequest, current_user: dict = Depends(get_current_user)):
    """Send chat message with content moderation and safety checks"""
    
    # Check if users have blocked each other
    is_blocked = await check_block_status(current_user["id"], request.recipient_id)
    if is_blocked:
        raise HTTPException(status_code=403, detail="Unable to send message")
    
    # Moderate message content
    moderation_result = await content_moderator.moderate_message(
        request.message, current_user["id"]
    )
    
    if moderation_result.action == "block":
        raise HTTPException(status_code=400, detail="Message contains inappropriate content")
    
    # Use filtered message
    filtered_message = moderation_result.filtered_message
    
    # Continue with existing message sending logic...
```

## Implementation Phases

### Phase 1: Database Schema & Basic APIs (Priority 1)
1. Create moderation tables with RLS policies
2. Implement basic block/report endpoints
3. Add location privacy columns and indexes
4. Create Pydantic models for all new endpoints

### Phase 2: Safety Integration (Priority 1)
1. Integrate safety filters into WingmanMatcher
2. Implement content moderation system
3. Add safety-enhanced rate limiting
4. Create email notifications for safety events

### Phase 3: Privacy-Aware Matching (Priority 1)  
1. Implement privacy-aware distance calculations
2. Update matching algorithm with privacy filters
3. Create location privacy management APIs
4. Integrate privacy settings with frontend

### Phase 4: Advanced Features (Priority 2)
1. Advanced content filtering algorithms
2. Automated moderation workflows
3. Privacy analytics and compliance
4. Performance optimization for large-scale privacy queries

## Quality Standards

### Security Requirements
- All endpoints require authentication
- RLS policies prevent unauthorized data access
- Rate limiting prevents abuse
- Input validation prevents injection attacks
- Privacy settings are immutable without explicit consent

### Performance Standards
- Privacy-aware queries execute in <100ms
- Content moderation adds <50ms to message processing
- Safety filters don't slow matching by >200ms
- Database indexes support efficient privacy filtering

### Monitoring & Compliance
- Safety event logging for audit trails
- Privacy setting change notifications
- Automated flagging of suspicious patterns
- GDPR-compliant data handling for location data

## Testing Strategy

### Unit Tests
- Content moderation accuracy
- Privacy filter logic
- Safety integration points
- Database query performance

### Integration Tests
- End-to-end block/report workflows
- Privacy-aware matching scenarios
- Email notification delivery
- Rate limiting enforcement

### Security Tests
- RLS policy enforcement
- Authentication bypass attempts
- Data leakage prevention
- Privacy setting isolation

## Success Metrics

**Safety System:**
- 99%+ report processing within 24 hours
- <1% false positive content filtering
- Zero blocked user breakthrough incidents
- 95%+ user satisfaction with safety features

**Privacy System:**
- 100% privacy preference compliance
- <100ms latency for privacy-aware queries
- Zero location data leaks
- 90%+ user adoption of privacy controls

## Deliverables

1. **Database Migration**: Complete schema with RLS policies
2. **Safety APIs**: Block, report, and moderation endpoints
3. **Privacy APIs**: Location privacy and preference management
4. **Enhanced Matching**: Safety and privacy integrated algorithms
5. **Content Moderation**: Local profanity and harassment filtering
6. **Email Integration**: Safety notification templates
7. **Rate Limiting**: Enhanced limits for safety and privacy endpoints
8. **Comprehensive Tests**: Unit, integration, and security test suites
9. **Documentation**: API documentation and deployment guide
10. **Implementation Report**: Complete technical delivery summary

## Timeline

**Week 1**: Database schema, basic APIs, and authentication
**Week 2**: Safety integration, content moderation, and matching enhancement  
**Week 3**: Privacy-aware systems, location management, and email integration
**Week 4**: Testing, optimization, and production deployment

This comprehensive backend domain implementation will deliver production-ready safety and privacy systems with security-first architecture, performance optimization, and seamless integration with existing Wingman platform infrastructure.