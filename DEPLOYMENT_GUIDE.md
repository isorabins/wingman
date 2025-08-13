# WingmanMatch Deployment Guide
## Heroku Backend + Vercel Frontend Setup

### 🏗️ **Architecture Overview**
- **Backend**: FastAPI on Heroku (handles profile API, photo uploads, AI features)
- **Frontend**: Next.js on Vercel (handles UI, forms, user experience)
- **Database**: Supabase (shared by both backend and frontend)
- **Storage**: Supabase Storage (photos and files)

---

## 📋 **Prerequisites**
1. **Supabase Account** - Database and storage
2. **Heroku Account** - Backend hosting
3. **Vercel Account** - Frontend hosting  
4. **Anthropic API Key** - AI features
5. **Git Repository** - Code deployment

---

## 🚀 **Step 1: Supabase Setup**

### Create Supabase Project
```bash
# 1. Go to https://supabase.com and create new project
# 2. Note down your project details:
#    - Project URL: https://your-project.supabase.co
#    - Anon Key: eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
#    - Service Role Key: eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...

# 3. Link to your project
supabase link --project-ref your-project-ref

# 4. Apply all migrations
supabase db reset
```

### Verify Database Setup
- Go to Supabase Dashboard → Table Editor
- Confirm tables exist: `user_profiles`, `user_locations`, `confidence_test_results`
- Go to Storage → Create bucket named `profile-photos`
- Verify RLS policies are active

---

## 🔧 **Step 2: Backend Deployment (Heroku)**

### Setup Heroku App
```bash
# 1. Install Heroku CLI
# 2. Login and create app
heroku login
heroku create wingman-backend

# 3. Set environment variables
heroku config:set ANTHROPIC_API_KEY=sk-ant-your-key-here
heroku config:set SUPABASE_URL=https://your-project.supabase.co
heroku config:set SUPABASE_ANON_KEY=your-anon-key
heroku config:set SUPABASE_SERVICE_ROLE_KEY=your-service-key

# 4. Optional: Set debug mode for initial testing
heroku config:set DEBUG=true
heroku config:set LOG_LEVEL=INFO
```

### Deploy Backend
```bash
# 1. Commit your changes
git add .
git commit -m "Deploy backend to Heroku"

# 2. Deploy to Heroku
git push heroku main

# 3. Check deployment
heroku logs --tail
heroku open  # Should show FastAPI docs at /docs
```

### Test Backend API
```bash
# Check if backend is working
curl https://wingman-backend.herokuapp.com/health

# Test profile completion endpoint
curl -X POST https://wingman-backend.herokuapp.com/api/profile/complete \
  -H "Content-Type: application/json" \
  -d '{"user_id": "test", "bio": "Test bio", "location": {"city": "Test City", "privacy_mode": "city_only"}, "travel_radius": 20}'
```

---

## 🌐 **Step 3: Frontend Deployment (Vercel)**

### Setup Vercel Project
```bash
# 1. Install Vercel CLI (if not already installed)
npm i -g vercel

# 2. Login and link project
vercel login
vercel link

# 3. Set environment variables
vercel env add NEXT_PUBLIC_SUPABASE_URL
# Enter: https://your-project.supabase.co

vercel env add NEXT_PUBLIC_SUPABASE_ANON_KEY  
# Enter: your-anon-key

vercel env add NEXT_PUBLIC_API_URL
# Enter: https://wingman-backend.herokuapp.com
```

### Deploy Frontend
```bash
# 1. Deploy to production
vercel --prod

# 2. Your app will be available at:
# https://wingman-app.vercel.app (or your custom domain)
```

### Alternative: GitHub Integration
1. Go to Vercel Dashboard → Import Project
2. Connect your GitHub repository
3. Set environment variables in Vercel dashboard:
   - `NEXT_PUBLIC_SUPABASE_URL`
   - `NEXT_PUBLIC_SUPABASE_ANON_KEY`
   - `NEXT_PUBLIC_API_URL`

---

## 🧪 **Step 4: Testing Full Stack**

### Test Complete User Flow
1. **Visit Frontend**: `https://your-app.vercel.app`
2. **Profile Setup**: Go to `/profile-setup`
3. **Test Features**:
   - Photo upload (drag & drop)
   - Bio entry (400 char limit)
   - Location capture (geolocation + manual)
   - Privacy toggle (precise vs city-only)
   - Form submission

### Verify Data Flow
1. **Frontend → Backend**: Form submission calls Heroku API
2. **Backend → Database**: Profile data saved to Supabase
3. **Backend → Storage**: Photos saved to Supabase Storage
4. **Success Redirect**: User redirected to `/find-buddy`

### Debug Common Issues
```bash
# Check Heroku backend logs
heroku logs --tail --app wingman-backend

# Check Vercel frontend logs
vercel logs

# Check Supabase logs
# Go to Supabase Dashboard → Logs
```

---

## 🔒 **Step 5: Security & Environment**

### Production Environment Variables

**Heroku Backend:**
```bash
heroku config:set NODE_ENV=production
heroku config:set DEBUG=false
heroku config:set CORS_ORIGINS=https://your-app.vercel.app
```

**Vercel Frontend:**
```bash
vercel env add NODE_ENV production
vercel env add NEXT_PUBLIC_API_URL https://wingman-backend.herokuapp.com
```

### CORS Configuration
Update `src/main.py` CORS settings:
```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",  # Development
        "https://your-app.vercel.app",  # Production frontend
        "https://*.vercel.app"  # All Vercel preview deployments
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

---

## 🚨 **Troubleshooting**

### Backend Issues
```bash
# Common fixes
heroku restart --app wingman-backend
heroku ps:scale web=1 --app wingman-backend

# Check if all env vars are set
heroku config --app wingman-backend
```

### Frontend Issues
```bash
# Redeploy frontend
vercel --prod

# Check environment variables
vercel env list
```

### Database Issues
- Check Supabase dashboard for connection issues
- Verify RLS policies allow operations
- Check if migrations applied correctly

---

## 📊 **Monitoring & Maintenance**

### Health Checks
- **Backend Health**: `https://wingman-backend.herokuapp.com/health`
- **Frontend Health**: Check Vercel dashboard
- **Database Health**: Supabase dashboard metrics

### Cost Management
- **Heroku**: Free tier for development, paid for production
- **Vercel**: Generous free tier, paid for high traffic
- **Supabase**: Free tier with good limits

---

## 🎯 **Quick Deployment Commands**

### Initial Setup
```bash
# Backend
heroku create wingman-backend
heroku config:set ANTHROPIC_API_KEY=your-key SUPABASE_URL=your-url
git push heroku main

# Frontend  
vercel link
vercel env add NEXT_PUBLIC_API_URL https://wingman-backend.herokuapp.com
vercel --prod
```

### Updates
```bash
# Backend updates
git push heroku main

# Frontend updates
vercel --prod
# Or automatic via GitHub integration
```

---

**🎉 That's it! Your WingmanMatch app should now be running with:**
- Backend API on Heroku
- Frontend UI on Vercel  
- Database & Storage on Supabase
- Full profile setup functionality working end-to-end