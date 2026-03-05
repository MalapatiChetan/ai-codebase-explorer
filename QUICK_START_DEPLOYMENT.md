# Quick Start: Cloud Deployment (5 Minutes)

Deploy the AI Codebase Explainer to production in ~5 minutes.

## TL;DR

1. **Get Gemini API Key**: https://aistudio.google.com/app/apikey
2. **Deploy Backend to Render**:
   - Push code to GitHub
   - Create Web Service on render.com
   - Set `GOOGLE_API_KEY` environment variable
3. **Deploy Frontend to Vercel**:
   - Push code to GitHub
   - Create Project on vercel.com
   - Set `NEXT_PUBLIC_API_URL` to your Render URL
4. **Done!** ✓

## Step-by-Step

### Backend (Render) - 3 minutes

```bash
# 1. Commit and push code
git add .
git commit -m "Ready for deployment"
git push origin main

# 2. Go to https://render.com
# 3. Click "New +" → "Web Service"
# 4. Connect GitHub repo and select branch "main"
# 5. Fill form:
#    - Name: ai-codebase-explainer
#    - Runtime: Python 3
#    - Build: pip install -r requirements.txt
#    - Start: python -m uvicorn src.main:app --host 0.0.0.0 --port $PORT
# 6. Click "Create Web Service"
# 7. Wait for deployment (3-5 min)
# 8. Copy your URL (e.g., https://ai-codebase-explainer.onrender.com)
```

**Add Environment Variables in Render Dashboard:**
```
GOOGLE_API_KEY=your_actual_key_from_step_1
GOOGLE_MODEL=gemini-2.5-flash
ENABLE_AI_CHAT=true
```

### Frontend (Vercel) - 2 minutes

```bash
# 1. Go to https://vercel.com
# 2. Click "Add New Project"
# 3. Import your GitHub repository
# 4. Select "Root Directory" → "frontend"
# 5. Click "Deploy"
# 6. In Environment Variables, set:
#    NEXT_PUBLIC_API_URL=https://your-render-url.onrender.com
# 7. Click "Redeploy" or push to main branch
```

## Verify Deployment

```bash
# Backend health check
curl https://your-render-url.onrender.com/api/health
# Response: {"status":"healthy",...}

# Frontend access
# Visit: https://your-vercel-url.vercel.app
# Should load the UI
```

## Make a Test Query

1. Visit your Vercel frontend URL
2. Click "Analyze Repository"
3. Enter: `https://github.com/fastapi/fastapi`
4. Click "Analyze"
5. Wait for analysis to complete
6. Try asking questions about the repository

## If Something Goes Wrong

### Frontend shows "Could not retrieve metadata"
- **Fix**: Check `NEXT_PUBLIC_API_URL` in Vercel is correct
- **Test**: Visit `https://your-render-url.onrender.com/api/health` directly

### Backend won't start
- **Check Render logs**: Dashboard → Logs tab
- **Common issue**: `GOOGLE_API_KEY` not set or invalid
- **Fix**: Set valid Gemini API key in Render environment variables

### AI returns rule-based answers (not using Gemini)
- **Fix**: Verify `GOOGLE_API_KEY` is correct
- **Check**: Visit `https://your-render-url.onrender.com/api/docs` → Try query endpoint

## Environment Variables Summary

### Render (Backend) - Required
```
GOOGLE_API_KEY                    # Get from aistudio.google.com
```

### Render (Backend) - Optional (Smart Defaults)
```
GOOGLE_MODEL=gemini-2.5-flash     # Latest Gemini model
ENABLE_AI_CHAT=true               # Keep AI enabled
DEBUG=false                       # Production mode
```

### Vercel (Frontend) - Required
```
NEXT_PUBLIC_API_URL               # Your Render backend URL
```

## Cost

- **Render Free**: 750 hours/month ✓ (enough for hobby projects)
- **Vercel Free**: Unlimited ✓

## Next Steps

- See [DEPLOYMENT.md](./DEPLOYMENT.md) for detailed guide
- Monitor Render logs: https://dashboard.render.com
- Monitor Vercel logs: https://vercel.com/dashboard

## Architecture

```
┌─────────────────────────────────┐
│    Browser (Vercel Frontend)    │
│  https://your-vercel-url        │
└──────────────┬──────────────────┘
               │ HTTP Requests
               │ NEXT_PUBLIC_API_URL
               ↓
┌─────────────────────────────────┐
│   API Server (Render Backend)   │
│  https://your-render-url        │
│  - Analyzes GitHub repos        │
│  - Uses Gemini AI               │
│  - Generates diagrams           │
└─────────────────────────────────┘
```

---

**Happy Deploying!** 🚀

