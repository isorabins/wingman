# Troubleshooting

## Emergency Checklist
1. `curl {base_url}/health` - Check backend
2. Check recent deployments/commits
3. Check error logs (backend, frontend, database)
4. Check external services (Supabase, Anthropic)
5. Reproduce locally

## Frontend Issues

### React/Next.js
```bash
# Module not found
rm -rf node_modules package-lock.json .next
npm install && npm run build

# TypeScript errors
npm run type-check
npm install @types/{package-name}

# Hydration errors - check for client-only code
useEffect(() => {
  // Client-side only code here
}, []);
```

### API Integration
```javascript
// CORS errors - check backend main.py ALLOWED_ORIGINS
// API calls failing - add error logging
try {
  const response = await fetch('/api/query', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(data)
  });
  
  if (!response.ok) {
    const errorText = await response.text();
    console.error('API Error:', response.status, errorText);
  }
} catch (error) {
  console.error('Network Error:', error);
}

// Streaming issues
const reader = response.body.getReader();
try {
  while (true) {
    const { done, value } = await reader.read();
    if (done) break;
    const chunk = decoder.decode(value, { stream: true });
    // Process chunk...
  }
} finally {
  reader.releaseLock();
}
```

## Backend Issues

### FastAPI
```bash
# Server won't start
python --version  # Should be 3.11+
source activate-env.sh  # Critical: conda env
pip install -r requirements.txt
python -m uvicorn src.main:app --reload --log-level debug

# Import errors
echo $PYTHONPATH
cd /path/to/fridays-at-four  # Run from project root
find src -name "__init__.py"  # Check __init__.py files exist

# Environment variables not loading
ls -la .env  # Check .env exists in project root
python -c "
from src.config import Config
print('Supabase URL:', Config.SUPABASE_URL[:20] + '...')
print('Anthropic Key:', bool(Config.ANTHROPIC_API_KEY))
"

# Check for common .env issues
cat .env | grep -v '^#' | grep '='
```

### Claude API Issues

#### Issue: "Invalid API key" errors
**Symptoms**: 401 Unauthorized responses from Anthropic

**Solutions**:
```python
# Test API key directly
import anthropic

client = anthropic.Anthropic(api_key="your-key-here")
try:
    response = client.messages.create(
        model="claude-3-sonnet-20240229",
        max_tokens=10,
        messages=[{"role": "user", "content": "Hi"}]
    )
    print("API key works!")
except Exception as e:
    print(f"API key error: {e}")
```

#### Issue: Rate limiting
**Symptoms**: 429 "Rate limit exceeded" responses

**Solutions**:
1. **Check usage** in Anthropic dashboard
2. **Implement backoff** in your code
3. **Cache responses** when possible

```python
import time
import random

async def call_claude_with_backoff(client, **kwargs):
    max_retries = 3
    for attempt in range(max_retries):
        try:
            return await client.messages.create(**kwargs)
        except anthropic.RateLimitError:
            if attempt == max_retries - 1:
                raise
            wait_time = (2 ** attempt) + random.uniform(0, 1)
            await asyncio.sleep(wait_time)
```

#### Issue: Slow responses
**Symptoms**: API calls taking >10 seconds

**Solutions**:
1. **Check prompt caching** - Are you using cached contexts?
2. **Reduce max_tokens** if you don't need long responses
3. **Use streaming** for better perceived performance

```python
# Enable prompt caching
messages = [
    {
        "role": "system", 
        "content": [
            {
                "type": "text",
                "text": large_context,
                "cache_control": {"type": "ephemeral"}
            }
        ]
    },
    {"role": "user", "content": user_message}
]
```

## 🗄️ Database Issues

### Supabase Connection Problems

#### Issue: "Connection refused" errors
**Symptoms**: Can't connect to Supabase, timeouts

**Solutions**:
```python
# Test connection
from supabase import create_client
from src.config import Config

try:
    supabase = create_client(Config.SUPABASE_URL, Config.SUPABASE_SERVICE_KEY)
    result = supabase.table('creator_profiles').select('id').limit(1).execute()
    print(f"Connection successful: {len(result.data)} profiles found")
except Exception as e:
    print(f"Connection failed: {e}")
```

**Common fixes**:
1. **Check credentials** - SUPABASE_URL and keys are correct
2. **Check network** - Can you reach supabase.com?
3. **Check Supabase status** - Is the service down?

#### Issue: "Permission denied" errors
**Symptoms**: RLS policy violations, access denied

**Solutions**:
```python
# Use service key for backend operations
supabase = create_client(
    Config.SUPABASE_URL, 
    Config.SUPABASE_SERVICE_KEY  # Not SUPABASE_ANON_KEY
)

# Check RLS policies in Supabase dashboard
# SQL Editor -> Check policies on tables
```

#### Issue: Foreign key constraint violations
**Symptoms**: "violates foreign key constraint" errors

**Solutions**:
```python
# Always ensure parent records exist
async def safe_insert_conversation(user_id: str, message: str):
    # Ensure user profile exists first
    await ensure_creator_profile(user_id)
    
    # Then insert conversation
    result = supabase.table('conversations').insert({
        'user_id': user_id,
        'message_text': message,
        'role': 'user'
    }).execute()
    
    return result.data[0]
```

### Query Performance Issues

#### Issue: Slow database queries
**Symptoms**: API responses taking >2 seconds

**Solutions**:
```python
# Use selective queries
# Good
result = supabase.table('conversations')\
    .select('message_text, role, created_at')\
    .eq('user_id', user_id)\
    .limit(20)\
    .execute()

# Bad
result = supabase.table('conversations')\
    .select('*')\
    .eq('user_id', user_id)\
    .execute()
```

**Check query performance**:
1. **Supabase Dashboard** -> SQL Editor -> EXPLAIN ANALYZE
2. **Add indexes** for commonly queried columns
3. **Limit result sets** appropriately

## 🚀 Deployment Issues

### Frontend Deployment (Vercel)

#### Issue: Build failures
**Symptoms**: Vercel deployment fails during build

**Solutions**:
```bash
# Test build locally
npm run build

# Check build logs in Vercel dashboard
# Common issues:
# - TypeScript errors
# - Missing environment variables
# - Import path issues
```

#### Issue: Environment variables not working
**Symptoms**: API calls fail in production but work locally

**Solutions**:
1. **Check Vercel environment variables** in dashboard
2. **Ensure variables start with NEXT_PUBLIC_** for client-side access
3. **Redeploy** after adding environment variables

### Backend Deployment (Railway/Render)

#### Issue: Server crashes on startup
**Symptoms**: Deployment succeeds but health check fails

**Solutions**:
```bash
# Check deployment logs
# Look for:
# - Import errors
# - Missing environment variables
# - Port binding issues

# Ensure server binds to correct port
python -m uvicorn src.main:app --host 0.0.0.0 --port $PORT
```

#### Issue: Database migrations not applied
**Symptoms**: Schema errors, missing tables

**Solutions**:
1. **Check Supabase migrations** were applied
2. **Verify database URL** in production environment
3. **Run migrations manually** if needed

## 🔍 Debugging Tools & Techniques

### Logging and Monitoring

#### Enable Debug Logging
```python
# In main.py
import logging

logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)
logger.debug("Debug message here")
```

#### Frontend Debugging
```javascript
// Enable verbose logging
console.log('API Request:', requestData);
console.log('API Response:', responseData);

// Use browser dev tools
// Network tab - Check request/response details
// Console tab - Check for JavaScript errors
// Application tab - Check localStorage/sessionStorage
```

### Testing in Production

#### Safe Production Testing
```python
# Use test user IDs that won't affect real users
TEST_USER_IDS = [
    "test-user-debug-123",
    "test-user-staging-456"
]

if user_id in TEST_USER_IDS:
    logger.info(f"Debug mode for test user {user_id}")
```

#### Health Monitoring
```bash
# Monitor key endpoints
curl -f https://fridays-at-four-c9c6b7a513be.herokuapp.com/health || echo "Health check failed"

# Test core functionality
curl -X POST https://fridays-at-four-c9c6b7a513be.herokuapp.com/query \
  -H "Content-Type: application/json" \
  -d '{"question":"test","user_id":"test","user_timezone":"UTC","thread_id":"test"}'
```

## 📊 Performance Debugging

### Identifying Bottlenecks

#### Backend Performance
```python
import time

async def timed_operation(operation_name: str, func):
    start_time = time.time()
    try:
        result = await func()
        duration = time.time() - start_time
        logger.info(f"{operation_name} took {duration:.2f}s")
        return result
    except Exception as e:
        duration = time.time() - start_time
        logger.error(f"{operation_name} failed after {duration:.2f}s: {e}")
        raise

# Usage
result = await timed_operation("Database query", 
    lambda: supabase.table('conversations').select('*').execute()
)
```

#### Frontend Performance
```javascript
// Measure API call performance
const startTime = performance.now();
const response = await fetch('/api/query', options);
const endTime = performance.now();
console.log(`API call took ${endTime - startTime} milliseconds`);
```

## 🆘 When to Escalate

### Immediate Escalation
- **Complete system outage** (health endpoint fails)
- **Data loss or corruption** 
- **Security breach suspected**
- **Cannot fix critical issue within 2 hours**

### How to Escalate
1. **Create detailed GitHub issue** with:
   - Steps to reproduce
   - Error messages/logs
   - What you've tried
   - Impact on users
2. **Include relevant logs** and screenshots
3. **Tag project owner** if urgent

## 📝 Documentation Updates

When you solve an issue:
1. **Update this troubleshooting guide** with the solution
2. **Add prevention tips** to relevant guides
3. **Create GitHub issue** for any systemic problems found

## 📚 Additional Resources

- **Supabase Status**: [status.supabase.com](https://status.supabase.com)
- **Anthropic Status**: [status.anthropic.com](https://status.anthropic.com)
- **Vercel Status**: [vercel-status.com](https://vercel-status.com)
- **FastAPI Docs**: [fastapi.tiangolo.com](https://fastapi.tiangolo.com)

## 🎯 Prevention Tips

1. **Test locally first** - Always test changes before deploying
2. **Monitor logs regularly** - Set up alerts for errors
3. **Keep dependencies updated** - But test updates in staging first
4. **Document your changes** - Help the next developer
5. **Use staging environment** - Test deployments before production

Remember: **Most issues have been solved before. Check existing GitHub issues and this guide first!** 🚀 

# Troubleshooting

## Environment Issues

### ImportError: cannot import name 'create_client' from 'supabase'
**Cause**: Environment not properly activated  
**Fix**: `source activate-env.sh` (uses conda env 'faf')

### ModuleNotFoundError: No module named 'src'
**Cause**: Running from wrong directory or improper environment  
**Fix**: `cd` to project root, then `source activate-env.sh`

### Port already in use
**Fix**: Use different port: `faf-dev --port 8001`

## Database Issues

### UUID validation errors
**Cause**: Using string literals instead of proper UUIDs  
**Fix**: Use `str(uuid.uuid4())` not `"test_user_001"`

### Foreign key violations
**Cause**: Missing creator_profiles record  
**Fix**: Call `ensure_creator_profile(user_id)` before operations

### Connection timeouts
**Check**:
- Supabase service status
- Network connectivity  
- Environment variables correct

## Memory System Issues

### AI forgets context across sessions
**Cause**: Querying by `thread_id` instead of `user_id`  
**Fix**: Update queries to use `user_id` for cross-session continuity

### Duplicate message detection
**Cause**: Saving messages before response completion  
**Fix**: Move `save_message()` to AFTER streaming completes

### Context too large errors  
**Fix**: Check memory table size, run summarization job

## Claude API Issues

### Rate limit exceeded
**Result**: Automatically falls back to backup models (Gemini)  
**Check**: LLM router logs for fallback usage

### Invalid API key
**Check**: Environment variables in `.env` file
**Production**: Verify keys in Heroku config

### Timeout errors
**Typical**: Network issues or Claude service problems  
**Check**: [status.anthropic.com](https://status.anthropic.com)

## Testing Issues

### Tests fail with database errors
**Check**:
- Using DEV database URL: `mxlmadjuauugvlukgrla.supabase.co`
- Never test against production: `wqfwsrpjzjqoqejlxhbx.supabase.co`
- Proper UUID format in test data

### Test data not cleaning up
**Fix**: Use `cleanup_test_user.py` after tests

### Async test issues
**Common**: Mixing sync/async operations  
**Fix**: Use `await` for all database and API calls

## Performance Issues

### Slow response times
**Check**:
- Database connection pooling
- Memory table size (may need summarization)
- Claude API response times

### Memory leaks
**Check**: Long-running conversations not being summarized

## Production Issues

### Health check failing
**Check**:
1. Heroku app status
2. Database connectivity  
3. Environment variables set
4. Recent deployments

### Users losing conversation history
**Common cause**: Memory queries by thread_id instead of user_id  
**Fix**: Update to user-scoped queries

## Debugging Commands

```bash
# Check environment
conda info --envs
python -c "from supabase import create_client; print('✅ Working')"

# Test database connection
python -c "from src.config import Config; print(Config.SUPABASE_URL)"

# Check logs
heroku logs --tail -a your-app-name
tail -f local.log

# Run specific tests
python new_tests/real_world_tests/test_specific.py
```

## Quick Fixes

```python
# Fix common import issues
import sys
sys.path.append('/Applications/fridays-at-four')

# Check UUID format
import uuid
test_id = str(uuid.uuid4())  # ✅ Correct
test_id = "test_user_001"    # ❌ Wrong

# Memory query fix
# ❌ Wrong
messages = supabase.table('memory').eq('thread_id', thread_id)
# ✅ Correct  
messages = supabase.table('memory').eq('user_id', user_id)
``` 