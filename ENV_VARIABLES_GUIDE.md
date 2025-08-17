# Environment Variables Configuration Guide

## Source of Truth: `.env` file
The local `.env` file uses these variable names:
- `SUPABASE_ANON`
- `SUPABASE_SERVICE_ROLE` 
- `SUPBASE_PROJECT_URL` (note: typo in "SUPBASE")
- `SUPABASE_DB_PASSWORD`
- `SUPABASE_PROJECT_ID`
- `SUPABASE_JWT_TOKEN`
- `ANTHROPIC_API_KEY`
- `HEROKU_URL`
- `VERCEL_PROJECT`

## Heroku Backend Configuration
Set these in Heroku Dashboard → Settings → Config Vars:

```bash
# Required for Backend
SUPABASE_ANON=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
SUPABASE_SERVICE_ROLE=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
SUPBASE_PROJECT_URL=https://hwrtgcuzgrajyzpxmjtz.supabase.co
ANTHROPIC_API_KEY=sk-ant-api03-...

# Optional (if using these features)
SUPABASE_DB_PASSWORD=Fforage323!!
SUPABASE_PROJECT_ID=hwrtgcuzgrajyzpxmjtz
SUPABASE_JWT_TOKEN=8ktJnx6/NC2i4bDfgLaifT9E0QYm6DBHLZLBm6iqsw5UHEAIbftuhvsp7lDn5v2b4xTx4l7uqnsacRgt1FAS6g==
REDIS_URL=<if-using-redis>
RESEND_API_KEY=<if-using-email>
```

## Vercel Frontend Configuration  
Set these in Vercel Dashboard → Settings → Environment Variables:

```bash
# Required for Frontend
NEXT_PUBLIC_SUPABASE_URL=https://hwrtgcuzgrajyzpxmjtz.supabase.co
NEXT_PUBLIC_SUPABASE_ANON_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
NEXT_PUBLIC_API_URL=https://first-move-e9bd9d26dbc5.herokuapp.com

# Note: Frontend only needs public keys, not service role keys
```

## Local Development
For local development, the `.env` file in the root directory should contain all variables.

## Code Configuration (src/config.py)
The config.py file now supports both naming conventions:
- Checks for `SUPBASE_PROJECT_URL` first (our convention), falls back to `SUPABASE_URL`
- Checks for `SUPABASE_ANON` first (our convention), falls back to `SUPABASE_ANON_KEY`
- Checks for `SUPABASE_SERVICE_ROLE` first (our convention), falls back to `SUPABASE_SERVICE_ROLE_KEY`

## Important Notes
1. **Never commit `.env` files to git** - they contain secrets
2. **Heroku**: Set variables through Dashboard or CLI: `heroku config:set VAR_NAME=value`
3. **Vercel**: Set through Dashboard or CLI: `vercel env add`
4. **The typo in SUPBASE_PROJECT_URL**: We're keeping it for backward compatibility but the code checks both versions

## To Update Platform Variables

### Heroku CLI
```bash
heroku config:set SUPABASE_ANON="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..." --app first-move-e9bd9d26dbc5
heroku config:set SUPABASE_SERVICE_ROLE="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..." --app first-move-e9bd9d26dbc5
heroku config:set SUPBASE_PROJECT_URL="https://hwrtgcuzgrajyzpxmjtz.supabase.co" --app first-move-e9bd9d26dbc5
heroku config:set ANTHROPIC_API_KEY="sk-ant-api03-..." --app first-move-e9bd9d26dbc5
```

### Vercel CLI
```bash
vercel env add NEXT_PUBLIC_SUPABASE_URL
vercel env add NEXT_PUBLIC_SUPABASE_ANON_KEY  
vercel env add NEXT_PUBLIC_API_URL
```

## Verification Commands

### Check Heroku Config
```bash
heroku config --app first-move-e9bd9d26dbc5
```

### Check Vercel Config
```bash
vercel env ls
```