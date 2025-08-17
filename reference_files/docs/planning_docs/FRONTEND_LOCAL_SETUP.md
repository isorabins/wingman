# 🚀 Frontend Local Development Setup Guide

**Context**: Our backend is running locally at `http://localhost:8000` with real Supabase database and API connections. We need to configure the frontend to connect to this local backend for testing.

## Step 1: Install and Run Frontend

```bash
# Install dependencies
npm install

# Start development server (usually runs on http://localhost:3000)
npm run dev
# OR
npm start
# OR  
yarn dev
```

## Step 2: Configure API Base URL

**Find and update your API configuration** to point to local backend:

### Look for files like:
- `config.js` / `config.ts`
- `.env` / `.env.local` / `.env.development`
- `constants.js` / `api.js`
- `services/api.js`

### Update the API URL:

```javascript
// CHANGE FROM (production):
const API_BASE_URL = "https://fridays-at-four-c9c6b7a513be.herokuapp.com"

// TO (local development):
const API_BASE_URL = "http://localhost:8000"
```

### Or in environment file:

```bash
# .env.local or .env.development
REACT_APP_API_URL=http://localhost:8000
# OR
NEXT_PUBLIC_API_URL=http://localhost:8000
# OR
VUE_APP_API_URL=http://localhost:8000
```

## Step 3: Key API Endpoints Available

Our local backend provides these endpoints:

- **Chat**: `POST /query` and `POST /query_stream`
- **Project Overview**: `GET /project-overview/{user_id}`
- **Chat History**: `GET /chat-history/{user_id}`
- **Health Check**: `GET /health`
- **API Docs**: `GET /docs` (visit http://localhost:8000/docs)

## Step 4: Test the Connection

1. **Start frontend**: Should run on `http://localhost:3000`
2. **Test API connection**: Open browser dev tools → Network tab
3. **Try the onboarding flow**: Sign up as new user or clear existing project
4. **Verify requests**: Should see API calls going to `localhost:8000` not Heroku

## Step 5: CORS Note

✅ **CORS is already configured** in our backend for `http://localhost:3000`, so cross-origin requests should work automatically.

## 🎯 What We're Testing

We've improved the **project onboarding flow** with:

- ✅ Progress tracking ("Topic 1 of 8...")
- ✅ 10-minute time expectation  
- ✅ Clear completion signals
- ✅ Better database saving
- ✅ No infinite loops

**Test this flow** by going through project setup as a new user!

## 🐛 Troubleshooting

### If API calls fail:
1. Check that backend is running at `http://localhost:8000`
2. Visit `http://localhost:8000/docs` to confirm API is accessible
3. Check browser console for CORS or network errors
4. Verify API_BASE_URL is correctly updated in your config

### If frontend won't start:
1. Try `npm install` or `yarn install` 
2. Check for port conflicts (3000 might be in use)
3. Try `npm run build` to check for build errors

## 📝 Expected Flow

1. **Frontend runs**: `http://localhost:3000`
2. **Backend runs**: `http://localhost:8000` 
3. **Real database**: Connected via Supabase
4. **Real APIs**: Connected via production keys
5. **Complete local testing**: With real data, no deployment needed!

---

**That's it!** Once frontend runs on `http://localhost:3000`, you'll have a complete local development environment with real data connections. 