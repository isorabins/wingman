# ⚙️ System Patterns - Architecture & Design Intelligence

## 🚨 **CRITICAL DEVELOPMENT RULES - READ FIRST**

### 🛑 **DEPLOYMENT SAFETY RULES**
**PRODUCTION DEPLOYMENT FORBIDDEN**: Never deploy to production under any circumstances
- ❌ **NEVER**: `git push heroku main` or any production deployment commands
- ❌ **NEVER**: Manual Heroku deployments to production apps
- ✅ **DEV ONLY**: Only deploy to development with explicit user permission
- 🤝 Always ask: "Should I deploy this to dev?" before any deployment
- 🔒 **SAFETY**: All production deployments go through GitHub Actions only

### 🛑 **DATABASE SAFETY RULES**
**PRODUCTION DATABASE FORBIDDEN**: Never test or modify production data
- ❌ **NEVER**: Test code against production database
- ❌ **NEVER**: Write, modify, or delete production data during development
- ❌ **NEVER**: Use production database for debugging or experimentation
- ✅ **DEV ONLY**: Always use development database for testing
- 🧪 **TESTING**: All code testing must use dev database with proper cleanup
- 🔒 **SAFETY**: Production data is sacred - never touch it during development

---

# WingmanMatch System Patterns

## Architecture Overview

### High-Level System Design
```
Frontend (Next.js) ↔ Backend API (FastAPI) ↔ Database (Supabase) ↔ AI (Claude)
                                          ↕
                                    Memory & Assessment System
```

### Core Components
1. **API Layer** (`src/main.py`) - FastAPI application handling requests
2. **Assessment System** (`src/agents/confidence_agent.py`) - Dating confidence evaluation
3. **Agent Architecture** (`src/agents/base_agent.py`) - Shared agent patterns
4. **Scoring Functions** (`src/assessment/confidence_scoring.py`) - Pure archetype calculation
5. **Database Tools** (`src/database.py`) - Database interaction utilities

## Key Design Patterns

### 1. Assessment Architecture Pattern ✅ **NEWLY IMPLEMENTED**
**Location**: `src/agents/confidence_agent.py`, `src/assessment/confidence_scoring.py`

**Pattern**: Multi-stage assessment with archetype scoring and progress tracking
```python
class ConfidenceTestAgent(BaseAgent):
    """Dating confidence assessment with 12-question flow"""
    
    async def process_message(self, thread_id: str, message: str):
        """Handle assessment conversation with state management"""
        
        # Load current progress
        progress = await self.get_progress(thread_id)
        
        # Extract answer if in assessment mode
        if progress and not progress.get('is_completed'):
            answer = self.extract_answer(message)
            progress = await self.save_answer(progress, answer)
            
            if self.is_assessment_complete(progress):
                # Calculate final results
                results = calculate_confidence_assessment(
                    progress['current_responses'], 
                    self.total_questions
                )
                await self.save_results(results)
                return self.format_completion_response(results)
            else:
                # Continue to next question
                return await self.get_next_question(progress)
```

**Benefits**:
- **State Management**: Progress tracking with resume capability
- **Pure Functions**: Deterministic scoring separated from agent logic
- **Error Recovery**: Graceful handling of incomplete assessments
- **Database Integration**: Auto-dependency creation for user profiles

### 2. Archetype Scoring Pattern ✅ **NEWLY IMPLEMENTED**
**Location**: `src/assessment/confidence_scoring.py`

**Pattern**: Pure functions for archetype calculation and experience levels
```python
def score_responses(responses: Dict[str, str]) -> Dict[str, float]:
    """Calculate archetype scores from assessment responses"""
    
    archetype_scores = {
        'Analyzer': 0.0, 'Sprinter': 0.0, 'Ghost': 0.0,
        'Scholar': 0.0, 'Naturalist': 0.0, 'Protector': 0.0
    }
    
    for question_num, answer in responses.items():
        question_index = int(question_num.split('_')[1]) - 1
        archetype_weights = QUESTION_ARCHETYPE_MAPPING[question_index]
        
        # Add weighted scores for each archetype
        for archetype, weight in archetype_weights[answer].items():
            archetype_scores[archetype] += weight
    
    return archetype_scores

def determine_primary_archetype(scores: Dict[str, float]) -> str:
    """Determine primary archetype with tie-breaking"""
    max_score = max(scores.values())
    tied_archetypes = [arch for arch, score in scores.items() if score == max_score]
    
    # Tie-breaking priority order
    if len(tied_archetypes) > 1:
        priority_order = ['Analyzer', 'Scholar', 'Naturalist', 'Protector', 'Sprinter', 'Ghost']
        for archetype in priority_order:
            if archetype in tied_archetypes:
                return archetype
    
    return tied_archetypes[0]
```

**Benefits**:
- **Pure Functions**: No side effects, easy to test and reason about
- **Deterministic**: Same inputs always produce same outputs
- **Flexible**: Easy to adjust archetype weights and add new archetypes
- **Testable**: Comprehensive unit test coverage for all edge cases

### 3. BaseAgent Inheritance Pattern ✅ **IMPLEMENTED**
**Location**: `src/agents/base_agent.py`, `src/agents/confidence_agent.py`

**Pattern**: Shared agent functionality with specialized implementations
```python
class BaseAgent:
    """Base class for all conversational agents"""
    
    def __init__(self, supabase_client, user_id: str):
        self.supabase_client = supabase_client
        self.user_id = user_id
        self.llm_router = LLMRouter()
    
    async def process_message(self, thread_id: str, message: str):
        """Template method - implemented by subclasses"""
        raise NotImplementedError
    
    async def ensure_user_profile(self):
        """Auto-dependency creation for user profiles"""
        # Shared logic for all agents

class ConfidenceTestAgent(BaseAgent):
    """Specialized agent for confidence assessment"""
    
    def __init__(self, supabase_client, user_id: str):
        super().__init__(supabase_client, user_id)
        self.total_questions = 12
        self.archetype_count = 6
    
    async def process_message(self, thread_id: str, message: str):
        """Confidence assessment specific implementation"""
        # Assessment-specific logic
```

**Benefits**:
- **Code Reuse**: Common functionality shared across agents
- **Consistency**: All agents follow same patterns for database operations
- **Extensibility**: Easy to add new agent types with consistent behavior
- **Maintainability**: Changes to base patterns apply to all agents

### 4. Assessment Progress Tracking Pattern ✅ **IMPLEMENTED**
**Location**: `src/agents/confidence_agent.py`

**Pattern**: Session management with resume capability
```python
async def get_progress(self, thread_id: str) -> Optional[Dict]:
    """Retrieve current assessment progress"""
    result = self.supabase_client.table('confidence_test_progress')\
        .select('*')\
        .eq('user_id', self.user_id)\
        .eq('thread_id', thread_id)\
        .execute()
    
    if result.data:
        return result.data[0]
    return None

async def save_progress(self, thread_id: str, progress_data: Dict):
    """Save current progress with upsert pattern"""
    progress_data.update({
        'user_id': self.user_id,
        'thread_id': thread_id,
        'updated_at': datetime.utcnow().isoformat()
    })
    
    self.supabase_client.table('confidence_test_progress')\
        .upsert(progress_data)\
        .execute()
```

**Benefits**:
- **Resume Capability**: Users can continue interrupted assessments
- **Progress Visibility**: Clear tracking of completion percentage
- **Data Persistence**: Progress saved across sessions
- **Error Recovery**: Graceful handling of connection issues

### 5. Database Schema Pattern ✅ **IMPLEMENTED**
**Location**: `supabase/migrations_wm/002_add_confidence_test_progress.sql`

**Pattern**: Comprehensive assessment data storage
```sql
-- Main results table
CREATE TABLE confidence_test_results (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES user_profiles(id) ON DELETE CASCADE,
    test_responses JSONB NOT NULL,
    archetype_scores JSONB NOT NULL,
    assigned_archetype TEXT NOT NULL,
    experience_level TEXT NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Progress tracking table
CREATE TABLE confidence_test_progress (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES user_profiles(id) ON DELETE CASCADE,
    thread_id TEXT NOT NULL,
    flow_step TEXT NOT NULL DEFAULT 'start',
    current_responses JSONB DEFAULT '{}',
    completion_percentage INTEGER DEFAULT 0,
    is_completed BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
```

**Benefits**:
- **JSONB Storage**: Flexible storage for responses and scores
- **Foreign Key Integrity**: Proper relationships with user profiles
- **Progress Tracking**: Separate table for session management
- **Audit Trail**: Created/updated timestamps for debugging

### 6. Experience Level Calculation Pattern ✅ **IMPLEMENTED**
**Location**: `src/assessment/confidence_scoring.py`

**Pattern**: Engagement-based experience level determination
```python
def calculate_experience_level(scores: Dict[str, float], total_questions: int) -> str:
    """Calculate experience level based on engagement scores"""
    
    total_possible = total_questions * 1.0  # Maximum score per question
    total_actual = sum(scores.values())
    engagement_percentage = (total_actual / total_possible) * 100
    
    if engagement_percentage < 60:
        return "beginner"
    elif engagement_percentage < 85:
        return "intermediate"
    else:
        return "advanced"
```

**Benefits**:
- **Objective Measurement**: Based on actual engagement, not self-reporting
- **Clear Thresholds**: Defined boundaries for experience levels
- **Scalable**: Easy to adjust thresholds based on user data
- **Actionable**: Levels guide appropriate challenge recommendations

## Error Handling Patterns

### 1. Graceful Assessment Degradation
```python
async def process_message(self, thread_id: str, message: str):
    """Handle assessment with comprehensive error recovery"""
    try:
        progress = await self.get_progress(thread_id)
        # Assessment logic...
    except Exception as e:
        logger.error(f"Assessment error: {e}")
        return self.get_fallback_response()
```

### 2. Auto-Recovery for Database Operations
```python
async def ensure_user_profile(self):
    """Auto-create missing user profile dependencies"""
    try:
        # Check if profile exists
        result = self.supabase_client.table('user_profiles')\
            .select('id').eq('id', self.user_id).execute()
        
        if not result.data:
            # Auto-create with safe defaults
            await self.create_default_profile()
    except Exception as e:
        logger.error(f"Profile creation error: {e}")
```

### 3. Input Validation and Sanitization
```python
def extract_answer(self, message: str) -> Optional[str]:
    """Extract and validate assessment answers"""
    message_clean = message.strip().upper()
    
    # Look for A, B, C, D, E, F answers
    valid_answers = ['A', 'B', 'C', 'D', 'E', 'F']
    for answer in valid_answers:
        if answer in message_clean:
            return answer
    
    return None  # Invalid answer, will prompt for clarification
```

## Performance Patterns

### 1. Pure Function Optimization
- All scoring functions are pure (no side effects)
- Deterministic calculations for consistent results
- Easy to cache and parallelize if needed

### 2. Efficient Database Operations
```python
# Upsert pattern for progress updates
.upsert(progress_data, on_conflict='user_id,thread_id')

# Specific field selection
.select('flow_step, current_responses, completion_percentage')

# Proper indexing on frequently queried fields
.eq('user_id', user_id).eq('thread_id', thread_id)
```

### 3. Memory Management
- Progress tracking prevents data loss
- Session-based cleanup for interrupted assessments
- Efficient JSONB storage for complex data structures

## Testing Patterns

### 1. Unit Testing for Pure Functions
```python
def test_archetype_scoring():
    """Test deterministic scoring calculations"""
    responses = {"question_1": "A", "question_2": "B"}
    scores = score_responses(responses)
    
    assert isinstance(scores, dict)
    assert len(scores) == 6  # All archetypes
    assert all(isinstance(score, float) for score in scores.values())
```

### 2. Integration Testing for Agent Flow
```python
async def test_assessment_flow():
    """Test complete assessment conversation"""
    agent = ConfidenceTestAgent(supabase_client, test_user_id)
    
    # Test question progression
    response1 = await agent.process_message(thread_id, "start assessment")
    assert "Question 1" in response1
    
    response2 = await agent.process_message(thread_id, "A")
    assert "Question 2" in response2
```

### 3. Database Integration Testing
- Test against development database only
- Comprehensive cleanup after tests
- Validate foreign key relationships
- Test auto-dependency creation patterns

## NEW: Profile Setup Architecture Patterns ✅ **NEWLY IMPLEMENTED (Task 7)**

### 7. Profile Completion API Pattern ✅ **NEWLY IMPLEMENTED**
**Location**: `src/main.py`, `app/profile-setup/page.tsx`

**Pattern**: Complete profile setup with photo upload, location privacy, and comprehensive validation
```python
class LocationData(BaseModel):
    """Location with privacy controls"""
    lat: Optional[Decimal] = Field(None, ge=-90, le=90)
    lng: Optional[Decimal] = Field(None, ge=-180, le=180)
    city: Optional[str] = Field(None, min_length=2, max_length=100)
    privacy_mode: Literal["precise", "city_only"] = "precise"

class ProfileCompleteRequest(BaseModel):
    """Complete profile setup request"""
    user_id: str
    bio: str = Field(..., min_length=10, max_length=400)
    location: LocationData
    travel_radius: int = Field(20, ge=1, le=50)
    photo_url: Optional[str] = None

@app.post("/api/profile/complete")
async def complete_profile(request: ProfileCompleteRequest):
    """Complete user profile with comprehensive validation"""
    # Input sanitization and validation
    bio_clean = await sanitize_bio_content(request.bio)
    
    # Auto-dependency creation
    await ensure_user_profile_exists(db_client, request.user_id)
    
    # Database operations (two-table update)
    profile_update = {'bio': bio_clean, 'photo_url': request.photo_url}
    location_data = {'lat': lat, 'lng': lng, 'privacy_mode': privacy_mode}
    
    # Return ready_for_matching flag
    return {"ready_for_matching": True, "user_id": request.user_id}
```

**Benefits**:
- **Privacy Controls**: Precise vs city-only location sharing
- **Input Validation**: PII detection, coordinate validation, file type checking
- **Auto-dependency Creation**: Follows established database patterns
- **Security First**: File upload validation, input sanitization, RLS policies

### 8. Photo Upload Security Pattern ✅ **NEWLY IMPLEMENTED**
**Location**: `storage/photo_upload.ts`, `supabase/migrations_wm/003_add_storage_setup.sql`

**Pattern**: Secure file uploads with comprehensive validation and RLS policies
```typescript
class PhotoUploadService {
    async uploadPhoto(file: File, userId: string): Promise<PhotoUploadResult> {
        // Multi-layer validation
        const validation = await this.validatePhotoFile(file);
        if (!validation.valid) return { success: false, error: validation.error };
        
        // Secure file path generation
        const filePath = this.generateFilePath(userId, file.name);
        
        // Upload with progress tracking
        const { data, error } = await this.supabase.storage
            .from('profile-photos')
            .upload(filePath, file, { cacheControl: '3600', upsert: false });
        
        return { success: true, photoUrl: urlData.publicUrl };
    }
    
    validatePhotoFile(file: File): { valid: boolean; error?: string } {
        // Size validation (5MB limit)
        if (file.size > MAX_FILE_SIZE) return { valid: false, error: 'File too large' };
        
        // MIME type validation
        if (!ALLOWED_MIME_TYPES.includes(file.type)) return { valid: false, error: 'Invalid type' };
        
        // File header validation (prevents disguised executables)
        // ... binary header checking logic
    }
}
```

**Benefits**:
- **Multi-layer Validation**: MIME type, size, and binary header checking
- **RLS Security**: User-scoped file access with proper policies
- **Progress Tracking**: Real-time upload progress for UX
- **Error Recovery**: Comprehensive error handling and retry logic

### 9. Location Privacy Pattern ✅ **NEWLY IMPLEMENTED**
**Location**: `app/profile-setup/page.tsx`, Frontend geolocation integration

**Pattern**: Privacy-first location handling with user control
```typescript
const LocationCapture: React.FC = () => {
    const [privacyMode, setPrivacyMode] = useState<'precise' | 'city_only'>('precise');
    const [location, setLocation] = useState<LocationData>();
    
    const handleGeolocation = async () => {
        if (navigator.geolocation) {
            navigator.geolocation.getCurrentPosition(
                (position) => {
                    const { latitude, longitude } = position.coords;
                    if (privacyMode === 'precise') {
                        setLocation({ lat: latitude, lng: longitude, privacy_mode: 'precise' });
                    } else {
                        // Use city centroid instead of precise coordinates
                        reverseGeocode(latitude, longitude).then(city => {
                            setLocation({ city, privacy_mode: 'city_only' });
                        });
                    }
                },
                () => showManualLocationInput() // Fallback to manual entry
            );
        }
    };
    
    return (
        <VStack>
            <Switch isChecked={privacyMode === 'precise'} onChange={handlePrivacyToggle}>
                Share exact location
            </Switch>
            <Button onClick={handleGeolocation}>Get My Location</Button>
            {/* Manual city input as fallback */}
        </VStack>
    );
};
```

**Benefits**:
- **User Control**: Clear privacy toggle with explanation
- **Graceful Fallback**: Manual city entry when geolocation fails
- **Privacy by Design**: City-only mode stores no precise coordinates
- **Accessibility**: Proper ARIA labels and keyboard navigation

### 10. Form Validation Pattern ✅ **NEWLY IMPLEMENTED**
**Location**: `app/profile-setup/page.tsx`, React Hook Form + Zod integration

**Pattern**: Comprehensive form validation with real-time feedback
```typescript
const profileSchema = z.object({
    bio: z.string()
        .min(10, 'Bio must be at least 10 characters')
        .max(400, 'Bio cannot exceed 400 characters')
        .refine(validateNoPII, 'Bio cannot contain phone numbers or email addresses'),
    location: z.object({
        lat: z.number().min(-90).max(90).optional(),
        lng: z.number().min(-180).max(180).optional(),
        city: z.string().optional(),
        privacy_mode: z.enum(['precise', 'city_only'])
    }).refine(validateLocationData, 'Either coordinates or city required'),
    travel_radius: z.number().min(1).max(50),
    photo_file: z.instanceof(File).optional()
});

const ProfileSetupForm: React.FC = () => {
    const { register, handleSubmit, formState: { errors }, watch } = useForm({
        resolver: zodResolver(profileSchema)
    });
    
    const bioValue = watch('bio');
    const bioLength = bioValue?.length || 0;
    
    return (
        <form onSubmit={handleSubmit(onSubmit)}>
            <FormControl isInvalid={!!errors.bio}>
                <Textarea {...register('bio')} placeholder="Tell us about yourself..." />
                <Text fontSize="sm" color={bioLength > 400 ? 'red.500' : 'gray.500'}>
                    {bioLength}/400 characters
                </Text>
                <FormErrorMessage>{errors.bio?.message}</FormErrorMessage>
            </FormControl>
        </form>
    );
};
```

**Benefits**:
- **Real-time Validation**: Live character counting and error feedback
- **PII Protection**: Automatic detection of phone numbers and emails
- **Type Safety**: Full TypeScript integration with Zod schemas
- **Accessibility**: Proper error announcements and focus management

---

**🎯 STATUS: PROFILE SETUP ARCHITECTURE COMPLETE**

*Task 7 complete: Full profile setup system with photo upload, location privacy, form validation, and security measures. All patterns are production-ready and integrate seamlessly with existing WingmanMatch architecture. Ready for buddy matching implementation.*