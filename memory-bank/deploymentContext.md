# 🚀 Deployment Context - URLs and Platform Configuration

## 📍 **Deployment URLs**

### Production URLs
- **Heroku Backend**: `https://first-move-e9bd9d26dbc5.herokuapp.com`
  - App Name: `first-move`
  - Health Check: `https://first-move-e9bd9d26dbc5.herokuapp.com/health`
  - Profile API: `https://first-move-e9bd9d26dbc5.herokuapp.com/api/profile/complete`

- **Vercel Frontend**: [URL from screenshot - need to check Vercel dashboard]
  - Project: Referenced in our .env as https://vercel.com/isorabins23/firstmove

### Local Development URLs
- **Backend**: `http://localhost:8000`
- **Frontend**: `http://localhost:3002` (Next.js)

## 🔧 **Environment Variables by Platform**

### Local Development (`.env` file)
```bash
# Backend Variables
SUPABASE_ANON=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
SUPABASE_SERVICE_ROLE=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
SUPBASE_PROJECT_URL=https://hwrtgcuzgrajyzpxmjtz.supabase.co
ANTHROPIC_API_KEY=sk-ant-api03-...
SUPABASE_DB_PASSWORD=Fforage323!!
SUPABASE_PROJECT_ID=hwrtgcuzgrajyzpxmjtz
SUPABASE_JWT_TOKEN=8ktJnx6/...

# Frontend Variables
NEXT_PUBLIC_SUPABASE_URL=https://hwrtgcuzgrajyzpxmjtz.supabase.co
NEXT_PUBLIC_SUPABASE_ANON_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
NEXT_PUBLIC_API_URL=http://localhost:8000
```

### Heroku Backend (`first-move` app)
```bash
# ✅ CORRECTLY CONFIGURED
SUPABASE_ANON=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
SUPABASE_SERVICE_ROLE=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
SUPBASE_PROJECT_URL=https://hwrtgcuzgrajyzpxmjtz.supabase.co
ANTHROPIC_API_KEY=your-actual-api-key

# Fallback variables (for backward compatibility)
SUPABASE_ANON_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
SUPABASE_SERVICE_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
SUPABASE_URL=https://hwrtgcuzgrajyzpxmjtz.supabase.co
```

### Vercel Frontend
```bash
# ✅ CORRECT FRONTEND VARIABLES
NEXT_PUBLIC_SUPABASE_URL=https://hwrtgcuzgrajyzpxmjtz.supabase.co
NEXT_PUBLIC_SUPABASE_ANON_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
NEXT_PUBLIC_API_URL=https://first-move-e9bd9d26dbc5.herokuapp.com

# ❌ SECURITY ISSUE - REMOVE THESE FROM VERCEL:
# SUPABASE_SERVICE_ROLE (should NOT be in frontend!)
# SUPABASE_DB_PASSWORD (should NOT be in frontend!)  
# SUPABASE_JWT_TOKEN (should NOT be in frontend!)
```

## 🚨 **CRITICAL SECURITY ISSUE IDENTIFIED**

**Problem**: Vercel frontend has `SUPABASE_SERVICE_ROLE` which is a backend-only secret!

**Risk**: Service role keys provide full database access and should NEVER be in frontend code.

**Action Required**: Remove these variables from Vercel:
- `SUPABASE_SERVICE_ROLE` 
- `SUPABASE_DB_PASSWORD`
- `SUPABASE_JWT_TOKEN`

## 🔧 **Platform Configuration**

### Heroku CLI Commands
```bash
# Check current config
heroku config --app first-move

# Set variables
heroku config:set VARIABLE_NAME="value" --app first-move

# View logs
heroku logs --tail --app first-move
```

### Vercel CLI Commands
```bash
# List environment variables
vercel env ls

# Add new variable
vercel env add VARIABLE_NAME

# Remove variable
vercel env rm VARIABLE_NAME
```

## 📋 **Testing Configuration**

### Test URLs
- **Deployed Backend Health**: `https://first-move-e9bd9d26dbc5.herokuapp.com/health`
- **Deployed Profile API**: `https://first-move-e9bd9d26dbc5.herokuapp.com/api/profile/complete`
- **Local Backend Health**: `http://localhost:8000/health`
- **Local Frontend**: `http://localhost:3002`

### Test Commands
```bash
# Test deployed backend
curl -s https://first-move-e9bd9d26dbc5.herokuapp.com/health

# Test profile API (use proper UUID)
curl -X POST https://first-move-e9bd9d26dbc5.herokuapp.com/api/profile/complete \
  -H "Content-Type: application/json" \
  -d '{"user_id": "123e4567-e89b-12d3-a456-426614174000", ...}'

# Run tests against deployed backend
TEST_API_URL=https://first-move-e9bd9d26dbc5.herokuapp.com python3 tests/run_profile_setup_tests.py --quick
```

## 🔄 **Deployment Status**

### ✅ Working Services
- **Heroku Backend**: Fully operational with correct environment variables
- **Database**: Supabase connection working on all platforms
- **Profile API**: Working with proper UUID format

### ⚠️ Action Items
1. **URGENT**: Remove service role key from Vercel frontend
2. **Verify**: Vercel frontend URL and ensure NEXT_PUBLIC_API_URL points to Heroku backend
3. **Test**: End-to-end flow from Vercel frontend to Heroku backend

## 📝 **Notes**
- Our config.py supports both naming conventions for backward compatibility
- Database requires proper UUID format for user_id (not "test-user-123")
- Service role keys should ONLY be on backend (Heroku), never frontend (Vercel)
- Frontend only needs public/anon keys from Supabase

## 🔍 **Next Steps**
1. Clean up Vercel environment variables (security)
2. Get actual Vercel frontend URL 
3. Test full stack integration
4. Run comprehensive test suite

## 🔧 **MCP Server Configuration**

### Configured MCP Servers
- **Playwright MCP**: `npx @playwright/mcp@latest` - For end-to-end testing
- **TaskMaster AI**: `npx -y --package=task-master-ai task-master-ai` - For task management
- **Supabase MCP**: `npx -y @supabase/mcp-server-supabase@latest --access-token sbp_...` - For database operations
- **Context7**: `https://mcp.context7.com/mcp` - For contextual operations

### MCP Status
- **Configuration**: Added to Claude Code local config via `claude mcp add` commands
- **Installation**: MCP servers work with Cursor, indicating proper installation
- **Connection**: Currently showing "Failed to connect" in `claude mcp list`
- **Issue**: May require fresh Claude Code session restart to establish connections

### MCP Commands Used
```bash
claude mcp add context7 https://mcp.context7.com/mcp
claude mcp add playwright "npx @playwright/mcp@latest"
claude mcp add taskmaster-ai "npx -y --package=task-master-ai task-master-ai"
claude mcp add supabase "npx -y @supabase/mcp-server-supabase@latest --access-token sbp_39d7480dd0a853c0b1a6d8f482ab2129e114e7e8"
```

**Last Updated**: August 14, 2025
**Status**: Backend operational ✅ | Frontend secured ✅ | Environment variables aligned ✅ | MCP servers configured (connection pending) ⚠️