# 🚀 Deployment Guide

This guide explains how to deploy the Airport AIP Lookup system to **Railway** (backend) and **Vercel** (frontend).

## 📋 Prerequisites

- GitHub account
- Railway account ([railway.app](https://railway.app))
- Vercel account ([vercel.com](https://vercel.com))
- Supabase account (optional, for caching)

## 🎯 Deployment Architecture

```
┌─────────────────┐         ┌─────────────────┐
│   Vercel        │         │   Railway       │
│  (Frontend)     │────────▶│  (Backend API)  │
│  Next.js App    │  HTTPS  │  Flask + Python │
│                 │         │                 │
└─────────────────┘         └─────────────────┘
                                   │
                                   ▼
                            ┌─────────────────┐
                            │   Supabase      │
                            │  (Cache/DB)     │
                            └─────────────────┘
```

## 🔧 Step 1: Deploy Backend to Railway

### 1.1 Push your code to GitHub
```bash
git add .
git commit -m "Add deployment configuration"
git push origin main
```

### 1.2 Create Railway Project

1. Go to [railway.app](https://railway.app) and sign up/login
2. Click **"New Project"**
3. Select **"Deploy from GitHub repo"**
4. Choose your `UNIxyty/clearway` repository
5. Railway will auto-detect Python

### 1.3 Configure Railway Settings

**Environment Variables:**
Go to **Variables** tab and add:
```
PORT=8080
FLASK_ENV=production
```

**If using Supabase:**
Add your Supabase credentials from `.env`:
```
SUPABASE_URL=your_supabase_url
SUPABASE_KEY=your_supabase_key
```

### 1.4 Deploy

Railway will automatically:
- Install Python dependencies from `requirements.txt`
- Run `python app.py`
- Expose your backend at a public URL

**🎉 Note down your Railway URL!** (e.g., `https://your-app.up.railway.app`)

---

## 🌐 Step 2: Deploy Frontend to Vercel

### 2.1 Prepare Frontend

The frontend is already configured for Vercel with:
- `frontend/vercel.json`
- Environment variable support

### 2.2 Create Vercel Project

1. Go to [vercel.com](https://vercel.com) and sign up/login
2. Click **"Add New..." → "Project"**
3. Import your GitHub repository `UNIxyty/clearway`

### 2.3 Configure Vercel

**Framework Preset:** Next.js (auto-detected)

**Root Directory:** `frontend`

**Build Command:** `npm run build` (auto-detected)

**Output Directory:** `.next` (auto-detected)

**Environment Variables:**
Add:
```
NEXT_PUBLIC_API_URL=https://your-railway-url.up.railway.app
```
(Replace with your actual Railway URL from Step 1)

### 2.4 Deploy

Click **"Deploy"** and Vercel will:
- Build your Next.js app
- Deploy to their CDN
- Give you a public URL

**🎉 Your frontend is now live!**

---

## ✅ Step 3: Verify Deployment

### Test Backend:
```bash
curl https://your-railway-url.up.railway.app/api/health
```

Expected response:
```json
{"status": "healthy", "service": "Airport AIP Lookup"}
```

### Test Frontend:
Visit your Vercel URL and try searching for an airport:
- EVRA (Latvia)
- EYVI (Lithuania)
- EFHK (Finland)

---

## 🔄 Updating Deployments

Both Railway and Vercel auto-deploy on every push to `main` branch!

**To update:**
1. Make changes to your code
2. Commit and push:
   ```bash
   git add .
   git commit -m "Your changes"
   git push origin main
   ```
3. Both platforms will auto-redeploy

---

## 🐛 Troubleshooting

### Backend Issues (Railway)

**Build fails:**
- Check logs in Railway dashboard
- Verify `requirements.txt` has all dependencies
- Ensure Playwright browsers are installed:
  ```bash
  playwright install chromium
  ```

**App crashes:**
- Check environment variables
- Verify PORT is set correctly
- Check logs for Python errors

**Playwright timeouts:**
- Increase timeout in scraper code
- Consider using Railway's larger plan for more resources

### Frontend Issues (Vercel)

**Build fails:**
- Check that root directory is `frontend`
- Verify all dependencies in `package.json`
- Check build logs

**API connection errors:**
- Verify `NEXT_PUBLIC_API_URL` environment variable
- Check CORS settings on backend
- Ensure Railway backend is accessible

**Environment variables not working:**
- Restart deployment after adding env vars
- Use `NEXT_PUBLIC_` prefix for client-side vars

### CORS Issues

If you see CORS errors, ensure `app.py` has:
```python
from flask_cors import CORS
CORS(app)
```

---

## 💰 Pricing

**Railway:**
- **Hobby:** $5/month (500 hours)
- **Pro:** $20/month (unlimited)

**Vercel:**
- **Free:** 100GB bandwidth/month
- **Pro:** $20/month (1TB bandwidth)

Both have generous free tiers for testing!

---

## 📊 Monitoring

### Railway
- **Logs:** Dashboard → Deployments → View logs
- **Metrics:** CPU, memory usage
- **Restart:** One-click restart

### Vercel
- **Analytics:** Built-in analytics
- **Logs:** Real-time function logs
- **Deployments:** Build history

---

## 🔐 Security Best Practices

1. **Never commit `.env` files** (already in `.gitignore`)
2. **Use environment variables** for all secrets
3. **Enable HTTPS** (automatic on both platforms)
4. **Set proper CORS** origins
5. **Rate limiting** (consider adding)

---

## 📚 Additional Resources

- [Railway Docs](https://docs.railway.app)
- [Vercel Docs](https://vercel.com/docs)
- [Next.js Deployment](https://nextjs.org/docs/deployment)
- [Flask Deployment](https://flask.palletsprojects.com/en/stable/deploying/)

---

## 🎉 Success!

Your Airport AIP Lookup system is now live on the internet!

- **Frontend:** `https://your-project.vercel.app`
- **Backend:** `https://your-app.up.railway.app`

Share the link and start using it! 🚀✈️

