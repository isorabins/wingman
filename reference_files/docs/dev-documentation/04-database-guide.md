# 🗄️ Database Guide

Complete guide to working with the Fridays at Four Supabase database. This covers the schema, common operations, and best practices.

## 🏗️ Database Overview

We use **Supabase** (PostgreSQL) for all data persistence. Supabase provides:
- **PostgreSQL database** with full SQL capabilities
- **Real-time subscriptions** for live updates
- **Row Level Security (RLS)** for data isolation
- **Built-in authentication** and user management
- **RESTful API** auto-generated from schema

## 🔑 Connection & Access

### Environment Variables
```env
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_SERVICE_KEY=your-service-key-here
SUPABASE_ANON_KEY=your-anon-key-here
```

### Python Connection
```python
from supabase import create_client
from src.config import Config

# Service key (backend - full permissions)
supabase = create_client(Config.SUPABASE_URL, Config.SUPABASE_SERVICE_KEY)

# Anonymous key (frontend - RLS enforced)
supabase_anon = create_client(Config.SUPABASE_URL, Config.SUPABASE_ANON_KEY)
```

### Access Supabase Dashboard
1. Go to [supabase.com](https://supabase.com)
2. Log in with project credentials
3. Navigate to the Fridays at Four project
4. Use **Table Editor** for data browsing
5. Use **SQL Editor** for custom queries

## 📊 Core Tables Schema

### `creator_profiles` - User Profiles
**Purpose**: Store user information and preferences

```sql
CREATE TABLE creator_profiles (
    id UUID PRIMARY KEY,
    slack_email TEXT NOT NULL,
    zoom_email TEXT NOT NULL,
    first_name TEXT NOT NULL,
    last_name TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT NOW()
);
```

**Key Fields**:
- `id` - Primary key, used as `user_id` throughout the system
- `slack_email` / `zoom_email` - Integration identifiers
- `first_name` / `last_name` - User's name
- `created_at` - Timestamp of profile creation

**Common Queries**:
```python
# Get user profile
profile = supabase.table('creator_profiles')\
    .select('*')\
    .eq('id', user_id)\
    .single()\
    .execute()

# Create default profile
new_profile = {
    'id': user_id,
    'slack_email': f"{user_id}@auto-created.local",
    'zoom_email': f"{user_id}@auto-created.local",
    'first_name': 'New',
    'last_name': 'User'
}
supabase.table('creator_profiles').insert(new_profile).execute()
```

### `conversations` - Chat History
**Purpose**: Store all user-AI conversations

```sql
CREATE TABLE conversations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES creator_profiles(id),
    thread_id UUID NOT NULL,
    message_text TEXT NOT NULL,
    role TEXT NOT NULL,  -- 'user' | 'assistant'
    context JSONB,
    created_at TIMESTAMP DEFAULT NOW()
);
```

**Key Fields**:
- `user_id` - Foreign key to creator_profiles
- `thread_id` - Unique identifier for each conversation
- `created_at` - Timestamp of conversation creation

**Common Queries**:
```python
# Get recent conversation history
messages = supabase.table('conversations')\
    .select('*')\
    .eq('user_id', user_id)\
    .order('created_at', desc=False)\
    .limit(50)\
    .execute()

# Save new message
new_message = {
    'user_id': user_id,
    'thread_id': thread_id,
    'created_at': datetime.now(timezone.utc)
}
supabase.table('conversations').insert(new_message).execute()
```

### `project_overview` - Project Details
**Purpose**: Store user's creative project information

```sql
CREATE TABLE project_overview (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES creator_profiles(id),
    project_name TEXT NOT NULL,
    project_type TEXT NOT NULL,
    goals TEXT[],
    challenges TEXT[],
    success_metrics JSONB,
    created_at TIMESTAMP DEFAULT NOW()
);
```

**Key Fields**:
- `project_name` - User's project title
- `project_type` - Category (novel, screenplay, podcast, etc.)
- `goals` - Array of project goals
- `challenges` - Array of identified challenges
- `success_metrics` - JSON object with success criteria

**Common Queries**:
```python
# Get user's project
project = supabase.table('project_overview')\
    .select('*')\
    .eq('user_id', user_id)\
    .single()\
    .execute()

# Create new project overview
project_data = {
    'user_id': user_id,
    'project_name': 'My Novel',
    'project_type': 'Creative Writing',
    'goals': ['Finish first draft', 'Character development'],
    'challenges': ['Plot consistency', 'Time management']
}
supabase.table('project_overview').insert(project_data).execute()
```

### `memory` - Short-term Context
**Purpose**: Store immediate conversation context and temporary data

```sql
CREATE TABLE memory (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES creator_profiles(id),
    thread_id UUID NOT NULL,
    content TEXT NOT NULL,
    memory_type TEXT NOT NULL, -- 'message' | 'buffer_summary'
    metadata JSONB,
    created_at TIMESTAMP DEFAULT NOW()
);
```

**Key Fields**:
- `user_id` - Foreign key to creator_profiles
- `thread_id` - Unique identifier for each conversation
- `content` - Individual user/AI messages
- `memory_type` - Type of message (message or buffer_summary)
- `metadata` - Additional data (response_time, model_used, etc.)

## 🔧 Common Database Operations

### User Management

#### Create User Profile
```python
async def ensure_creator_profile(self, user_id: str):
    """Always call before operations to prevent FK violations"""
    result = self.supabase.table('creator_profiles')\
        .select('id').eq('id', user_id).execute()
    
    if not result.data:
        profile_data = {
            'id': user_id,
            'slack_email': f"{user_id}@auto-created.local",
            'zoom_email': f"{user_id}@auto-created.local", 
            'first_name': 'New',
            'last_name': 'User'
        }
        self.supabase.table('creator_profiles').insert(profile_data).execute()
```

#### Update User Preferences
```python
def update_user_preferences(user_id: str, preferences: dict):
    """Update user preferences"""
    supabase.table('creator_profiles')\
        .update({'preferences': preferences})\
        .eq('id', user_id)\
        .execute()
```

### Conversation Management

#### Save Conversation Message
```python
async def save_message(self, user_id: str, thread_id: str, content: str, memory_type: str):
    """Save a conversation message"""
    message_data = {
        'user_id': user_id,
        'thread_id': thread_id,
        'content': content,
        'memory_type': memory_type,
        'metadata': {
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'message_length': len(content)
        }
    }
    
    result = self.supabase.table('memory').insert(message_data).execute()
    return result.data[0] if result.data else None
```

#### Get Conversation History
```python
def get_conversation_history(user_id: str, limit: int = 50):
    """Get recent conversation history"""
    result = supabase.table('conversations')\
        .select('thread_id, created_at')\
        .eq('user_id', user_id)\
        .order('created_at', desc=False)\
        .limit(limit)\
        .execute()
    
    return result.data
```

### Project Management

#### Get User Project
```python
def get_user_project(user_id: str):
    """Get user's project overview"""
    result = supabase.table('project_overview')\
        .select('*')\
        .eq('user_id', user_id)\
        .execute()
    
    return result.data[0] if result.data else None
```

#### Update Project Phase
```python
def update_project_phase(user_id: str, new_phase: str):
    """Update project current phase"""
    supabase.table('project_overview')\
        .update({
            'current_phase': new_phase,
            'last_updated': datetime.now(timezone.utc).isoformat()
        })\
        .eq('user_id', user_id)\
        .execute()
```

## 🔍 Advanced Queries

### Get User Context for AI
```python
async def get_user_context(self, user_id: str):
    """Get comprehensive user context for AI"""
    
    # Get user profile
    profile = supabase.table('creator_profiles')\
        .select('first_name, last_name, preferences')\
        .eq('id', user_id)\
        .single()\
        .execute()
    
    # Get project overview
    project = supabase.table('project_overview')\
        .select('*')\
        .eq('user_id', user_id)\
        .execute()
    
    # Get recent conversations
    recent_messages = supabase.table('conversations')\
        .select('thread_id, created_at')\
        .eq('user_id', user_id)\
        .order('created_at', desc=True)\
        .limit(20)\
        .execute()
    
    # Get longterm memory
    longterm_insights = supabase.table('memory')\
        .select('content, relevance_score')\
        .eq('user_id', user_id)\
        .eq('memory_type', 'buffer_summary')\
        .order('relevance_score', desc=True)\
        .limit(5)\
        .execute()
    
    return {
        'profile': profile.data,
        'project': project.data[0] if project.data else None,
        'recent_messages': recent_messages.data,
        'longterm_insights': longterm_insights.data
    }
```

### Analytics Queries
```python
def get_user_analytics(user_id: str):
    """Get user engagement analytics"""
    
    # Message count by day (last 30 days)
    result = supabase.rpc('get_daily_message_counts', {
        'user_id_param': user_id,
        'days_back': 30
    }).execute()
    
    # Or raw SQL approach
    query = """
    SELECT 
        DATE(created_at) as date,
        COUNT(*) as message_count
    FROM conversations 
    WHERE user_id = %s 
    AND created_at >= NOW() - INTERVAL '30 days'
    GROUP BY DATE(created_at)
    ORDER BY date;
    """
    
    return result.data
```

## 🛡️ Security & Best Practices

### Row Level Security (RLS)
All tables have RLS policies that ensure users can only access their own data:

```sql
-- Example RLS policy for conversations
CREATE POLICY "Users can only see their own conversations"
ON conversations FOR ALL
USING (user_id = auth.uid());
```

### Safe Database Operations

#### Always Use Transactions for Related Operations
```python
# When creating related records, use transactions
async def create_user_with_project(user_data: dict, project_data: dict):
    try:
        # Start transaction
        with supabase.db.transaction():
            # Create profile first
            profile_result = supabase.table('creator_profiles')\
                .insert(user_data)\
                .execute()
            
            # Then create project with user_id
            project_data['user_id'] = profile_result.data[0]['id']
            project_result = supabase.table('project_overview')\
                .insert(project_data)\
                .execute()
            
            return profile_result.data[0], project_result.data[0]
    except Exception as e:
        # Transaction will auto-rollback
        raise e
```

#### Validate Foreign Keys
```python
# Always ensure referenced records exist
async def add_conversation_message(user_id: str, thread_id: str, content: str):
    # Ensure user profile exists first
    await ensure_creator_profile(user_id)
    
    # Then save message
    return await save_message(user_id, thread_id, content, 'message')
```

### Performance Optimization

#### Use Selective Queries
```python
# Good - only select needed fields
profile = supabase.table('creator_profiles')\
    .select('first_name, last_name')\
    .eq('id', user_id)\
    .single()\
    .execute()

# Avoid - selecting all fields
profile = supabase.table('creator_profiles')\
    .select('*')\
    .eq('id', user_id)\
    .single()\
    .execute()
```

#### Use Appropriate Indexes
```sql
-- Indexes already exist for common queries
CREATE INDEX idx_conversations_user_id_created_at 
ON conversations(user_id, created_at);

CREATE INDEX idx_memory_user_relevance 
ON memory(user_id, relevance_score DESC);
```

## 🧪 Testing Database Operations

### Test Data Cleanup
```python
def cleanup_test_user(test_user_id: str):
    """Clean up all data for a test user"""
    tables = [
        'conversations',
        'memory',
        'project_overview',
        'creator_profiles'  # Delete this last due to foreign keys
    ]
    
    for table in tables:
        try:
            supabase.table(table).delete().eq('user_id', test_user_id).execute()
        except Exception as e:
            print(f"Cleanup error for {table}: {e}")
```

### Database Health Check
```python
def check_database_health():
    """Verify database connectivity and basic operations"""
    try:
        # Test connection
        result = supabase.table('creator_profiles')\
            .select('id')\
            .limit(1)\
            .execute()
        
        print(f"✅ Database connected - found {len(result.data)} profiles")
        return True
    except Exception as e:
        print(f"❌ Database error: {e}")
        return False
```

## 🚨 Common Issues & Solutions

### Foreign Key Violations
**Problem**: `insert or update on table "conversations" violates foreign key constraint`

**Solution**: Always ensure parent records exist
```python
# Wrong
supabase.table('conversations').insert({
    'user_id': 'new-user-123',
    'thread_id': 'new-thread-123'
}).execute()

# Right
await ensure_creator_profile('new-user-123')
supabase.table('conversations').insert({
    'user_id': 'new-user-123', 
    'thread_id': 'new-thread-123'
}).execute()
```

### Connection Timeouts
**Problem**: Database queries timing out

**Solutions**:
- Check network connectivity
- Verify Supabase service status
- Use connection pooling
- Optimize slow queries

### RLS Permission Denied
**Problem**: `new row violates row-level security policy`

**Solution**: Use service key for backend operations
```python
# Use service key (not anon key) for backend operations
supabase = create_client(Config.SUPABASE_URL, Config.SUPABASE_SERVICE_KEY)
```

## 📚 Additional Resources

- **Supabase Documentation**: [supabase.com/docs](https://supabase.com/docs)
- **PostgreSQL Docs**: [postgresql.org/docs](https://postgresql.org/docs)
- **SQL Tutorial**: [w3schools.com/sql](https://w3schools.com/sql)

## 🎯 Next Steps

Now that you understand the database:

1. **Practice with queries** - Try the examples in the Supabase SQL editor
2. **Read the [API Reference](./05-api-reference.md)** to see how endpoints use the database
3. **Check out [Common Tasks](./03-common-tasks.md)** for typical database operations
4. **Review the [Troubleshooting Guide](./06-troubleshooting.md)** for database-specific issues

The database is the foundation of the entire system. Understanding it well will make you much more effective at debugging and implementing features! 🚀 