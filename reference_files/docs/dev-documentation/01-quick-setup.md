# Quick Setup

## Prerequisites
Python 3.11+, Node.js 18+, Git, API keys (Anthropic, Supabase)

## Backend Setup

```bash
git clone https://github.com/fridays-at-four/fridays-at-four.git
cd fridays-at-four
source activate-env.sh  # Creates/activates conda env 'faf'

# .env file
cat > .env << 'EOF'
ANTHROPIC_API_KEY=sk-ant-...
SUPABASE_URL=https://mxlmadjuauugvlukgrla.supabase.co
SUPABASE_SERVICE_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Im14bG1hZGp1YXV1Z3ZsdWtncmxhIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTczMzk2NDc0NSwiZXhwIjoyMDQ5NTQwNzQ1fQ.Hw5zuWjRx8XSGrOQPxIUGf4zzlvfQrK5gR4RdKdh_0w
EOF

faf-dev                              # Start dev server (:8000)
curl http://localhost:8000/health    # {"status": "healthy"}
```

## Test Conversation

```bash
curl -X POST http://localhost:8000/query \
  -H "Content-Type: application/json" \
  -d '{
    "user_input": "Hello",
    "user_id": "'$(uuidgen)'",
    "thread_id": "'$(uuidgen)'"
  }'
```

## Common Issues

- `ImportError: create_client` → Run `source activate-env.sh`
- `ModuleNotFoundError: src` → Run from project root with conda env
- `UUID validation errors` → Use proper UUIDs, not strings

## Database Test

```python
from src.config import Config
from supabase import create_client
client = create_client(Config.SUPABASE_URL, Config.SUPABASE_SERVICE_KEY)
result = client.table('creator_profiles').select('*').limit(1).execute()
```

**Database URLs:**
- Dev: `mxlmadjuauugvlukgrla.supabase.co` (full access)
- Prod: `ipvxxsthulsysbkwbitu.supabase.co` (READ ONLY) 