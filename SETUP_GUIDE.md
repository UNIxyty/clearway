# 🚀 Complete Setup Guide for Railway & Vercel

This guide will walk you through setting up your Airport AIP Lookup system with Railway (backend) and Vercel (frontend).

## 📋 Prerequisites

- GitHub account
- Railway account (https://railway.app)
- Vercel account (https://vercel.com)
- Supabase account (optional, https://supabase.com)

---

## 🔧 Part 1: Railway Backend Setup

### Step 1: Add Supabase Credentials to Railway

**Option A: If you have the credentials already:**

Your credentials are in `others/env.example`. Add them to Railway:

1. Go to your Railway dashboard
2. Click on your project → **Variables** tab
3. Add these environment variables:

```
SUPABASE_URL=https://dejdohsfjnvuimfofcmi.supabase.co
SUPABASE_ANON_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImRlamRvaHNmam52dWltZm9mY21pIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NjExNDk5MjEsImV4cCI6MjA3NjcyNTkyMX0.TMIbSTlZrwikOABAk8Lx3NEya0R5NcwaU_MMqob0uxg
```

4. **Don't forget to click "Deploy" after adding!**

**Option B: Set up new Supabase project:**

1. Go to https://supabase.com
2. Create a new project
3. Go to Settings → API
4. Copy your:
   - Project URL → `SUPABASE_URL`
   - anon/public key → `SUPABASE_ANON_KEY`
5. Add these to Railway Variables tab
6. Create the database table:

Run this SQL in Supabase SQL Editor:
```sql
CREATE TABLE IF NOT EXISTS airport_cache (
    id BIGSERIAL PRIMARY KEY,
    airport_code TEXT NOT NULL,
    airport_name TEXT NOT NULL,
    date DATE NOT NULL,
    data JSONB NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(airport_code, date)
);

CREATE INDEX IF NOT EXISTS idx_airport_code_date ON airport_cache(airport_code, date);
```

### Step 2: Get Your Railway Backend URL

1. In Railway dashboard, go to your service
2. Click on the **Settings** tab
3. Find your **"Public Domain"** or **"Deployment URL"**
4. Copy it! Example: `https://web-production-e7af.up.railway.app`

**✅ Backend is ready!**

---

## 🌐 Part 2: Vercel Frontend Setup

### Step 1: Create Vercel Project

1. Go to https://vercel.com
2. Sign in with your GitHub account
3. Click **"Add New..." → "Project"**
4. Import your repository: **`UNIxyty/clearway`**

### Step 2: Configure Vercel Settings

When importing, you'll see configuration options:

- **Framework Preset:** `Next.js` (auto-detected ✅)
- **Root Directory:** `frontend` ⚠️ **IMPORTANT!**
- **Build Command:** `npm run build` (auto-detected ✅)
- **Output Directory:** `.next` (auto-detected ✅)

### Step 3: Add Environment Variables

Before clicking "Deploy", click **"Environment Variables"**

Add this variable:
```
Name: NEXT_PUBLIC_API_URL
Value: https://web-production-e7af.up.railway.app
```
(Replace with YOUR Railway backend URL from Part 1 Step 2!)

### Step 4: Deploy!

1. Click **"Deploy"**
2. Wait for build to complete (2-3 minutes)
3. Get your Vercel URL! Example: `https://clearway.vercel.app`

**✅ Frontend is ready!**

---

## 🧪 Part 3: Testing

### Test Your Deployment

1. Visit your Vercel URL
2. Try searching for airports:
   - `EVRA` (Latvia)
   - `EYVI` (Lithuania)
   - `EFHK` (Finland)
   - `EETN` (Estonia)
   - `KJFK` (USA)
   - `LFPG` (France)

### Troubleshooting

**Problem: Frontend can't connect to backend**

- Check Vercel environment variable `NEXT_PUBLIC_API_URL` matches your Railway URL
- Make sure there's no trailing slash in the URL
- Test backend directly: `https://your-railway-url.up.railway.app/api/health`

**Problem: No Supabase caching**

- Check Railway Variables tab has `SUPABASE_URL` and `SUPABASE_ANON_KEY`
- Check Railway deploy logs for "Supabase client initialized"
- Redeploy Railway after adding variables

**Problem: Search returns errors**

- Check Railway logs: Dashboard → Deployments → View logs
- Look for Python errors
- Check that Playwright browsers are installed

---

## 🎉 Success!

Your Airport AIP Lookup system is now live!

- **Frontend:** https://your-project.vercel.app
- **Backend:** https://your-app.up.railway.app

---

## 📚 Quick Reference

### Railway Environment Variables
```
SUPABASE_URL=your_supabase_url
SUPABASE_ANON_KEY=your_supabase_key
```

### Vercel Environment Variables
```
NEXT_PUBLIC_API_URL=your_railway_backend_url
```

### Database Schema (Supabase)
```sql
CREATE TABLE airport_cache (
    id BIGSERIAL PRIMARY KEY,
    airport_code TEXT NOT NULL,
    airport_name TEXT NOT NULL,
    date DATE NOT NULL,
    data JSONB NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(airport_code, date)
);
```

---

## 🔄 Updating Your App

Both platforms auto-deploy on git push to main branch!

1. Make changes locally
2. Commit and push:
   ```bash
   git add .
   git commit -m "Your changes"
   git push origin main
   ```
3. Both Railway and Vercel will automatically deploy

---

**🎊 Congratulations! Your app is production-ready!**

