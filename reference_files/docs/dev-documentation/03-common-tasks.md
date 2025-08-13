# Common Development Tasks

## Bug Fixes

### Frontend Issues
```typescript
// Button not working
<button onClick={() => handleSubmit()} disabled={isLoading}>
  {isLoading ? 'Sending...' : 'Send Message'}
</button>

// Chat messages not displaying
{messages.map((msg, i) => (
  <div key={`${msg.id}-${i}`} className={messageStyles[msg.role]}>
    {msg.content}
  </div>
))}

// CORS errors - check backend main.py
ALLOWED_ORIGINS = [
    "https://app.fridaysatfour.co",
    "http://localhost:3000"
]
```

### Backend Issues
```bash
# API 500 errors - debug locally
python -m uvicorn src.main:app --reload --log-level debug

# Test endpoint
curl -X POST http://localhost:8000/query \
  -H "Content-Type: application/json" \
  -d '{"user_input": "test", "user_id": "'$(uuidgen)'", "thread_id": "'$(uuidgen)'"}'

# Claude API issues
python -c "
from src.config import Config
import anthropic
client = anthropic.Anthropic(api_key=Config.ANTHROPIC_API_KEY)
response = client.messages.create(
    model='claude-3-5-sonnet-20241022',
    max_tokens=100,
    messages=[{'role': 'user', 'content': 'Hello'}]
)
print(response.content)
"
```

## Feature Development

### New API Endpoints
```python
from pydantic import BaseModel

class UserStatsResponse(BaseModel):
    total_messages: int
    projects_count: int

@app.get("/user-stats/{user_id}", response_model=UserStatsResponse)
async def get_user_stats(user_id: str):
    stats = await get_user_statistics(user_id)
    return UserStatsResponse(**stats)
```

### Database Operations
```python
# Add new table
async def create_new_table():
    await supabase.table('new_table').insert({
        'user_id': user_id,
        'data': data_dict
    }).execute()

# Update existing records
await supabase.table('creator_profiles')\
    .update({'first_name': new_name})\
    .eq('id', user_id)\
    .execute()
```

### UI Components
```typescript
interface ProgressBarProps {
  progress: number; // 0-100
  className?: string;
}

export const ProgressBar: React.FC<ProgressBarProps> = ({ progress, className = '' }) => (
  <div className={`w-full bg-gray-200 rounded-full h-2 ${className}`}>
    <div 
      className="bg-blue-600 h-2 rounded-full transition-all duration-300"
      style={{ width: `${Math.min(100, Math.max(0, progress))}%` }}
    />
  </div>
);
```

## Testing

### Backend Tests
```bash
# Run test suite
python -m pytest new_tests/test-suite/ -v

# Test specific functionality
python test_onboarding_conversation.py
python cleanup_test_user.py

# Database connection test
python -c "
from src.simple_memory import SimpleMemory
memory = SimpleMemory('test-user-id')
print('Database connected:', bool(memory.supabase))
"
```

### Frontend Tests
```bash
npm test                    # Unit tests
npm run test:e2e           # End-to-end tests
npm run type-check         # TypeScript validation
```

## Deployment

### Backend Deployment
```bash
# Development (allowed)
git push origin dev

# Production (requires permission)
# Must ask: "Should I deploy this to production?"
git push heroku main
```

### Environment Variables
```bash
# Backend .env
ANTHROPIC_API_KEY=sk-ant-...
SUPABASE_URL=https://mxlmadjuauugvlukgrla.supabase.co
SUPABASE_SERVICE_KEY=eyJ...

# Frontend .env.local
NEXT_PUBLIC_SUPABASE_URL=https://mxlmadjuauugvlukgrla.supabase.co
NEXT_PUBLIC_BACKEND_API_URL=http://localhost:8000
```

## Database Migrations

### Schema Changes
```sql
-- Add new column
ALTER TABLE creator_profiles ADD COLUMN new_field TEXT;

-- Create new table
CREATE TABLE new_feature (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES creator_profiles(id),
    created_at TIMESTAMP DEFAULT NOW()
);
```

### Data Migration
```python
# Migrate existing data
async def migrate_data():
    users = await supabase.table('creator_profiles').select('*').execute()
    for user in users.data:
        await supabase.table('new_table').insert({
            'user_id': user['id'],
            'migrated_data': transform_data(user)
        }).execute()
```

## Performance Optimization

### Database Queries
```python
# Efficient queries
result = supabase.table('conversations')\
    .select('id, content, created_at')\  # Specific fields only
    .eq('user_id', user_id)\
    .order('created_at', desc=False)\
    .limit(50)\
    .execute()

# Avoid N+1 queries
users_with_projects = supabase.table('creator_profiles')\
    .select('*, project_overview(*)')\
    .execute()
```

### Frontend Optimization
```typescript
// Lazy loading
const LazyComponent = dynamic(() => import('./HeavyComponent'), {
  loading: () => <div>Loading...</div>
});

// Memoization
const MemoizedComponent = React.memo(({ data }) => (
  <div>{data.map(item => <Item key={item.id} {...item} />)}</div>
));
``` 