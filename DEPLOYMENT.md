# Deployment Guide: Render + Vercel

This guide explains how to deploy the AI Codebase Explainer application to the cloud:
- **Backend (FastAPI)** → [Render.com](https://render.com)
- **Frontend (Next.js)** → [Vercel](https://vercel.com)

---

## Prerequisites

- GitHub account (for connecting repositories)
- Render account (free tier available)
- Vercel account (free tier available)
- Google Gemini API key: https://aistudio.google.com/app/apikey

---

## Part 1: Deploy Backend to Render

### Step 1: Push to GitHub

```bash
git add .
git commit -m "Prepare for cloud deployment"
git push origin main
```

### Step 2: Create Render Service

1. Go to https://render.com and sign up/log in
2. Click **"New +"** → **"Web Service"**
3. Select **"Build and deploy from a Git repository"**
4. Connect your GitHub account and select this repository
5. Fill in the form:
   - **Name**: `ai-codebase-explainer` (or your choice)
   - **Environment**: `Python 3`
   - **Region**: Choose closest to you
   - **Branch**: `main`
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: 
     ```
     python -m uvicorn src.main:app --host 0.0.0.0 --port $PORT
     ```

### Step 3: Set Environment Variables

In Render dashboard, go to **Environment** tab and add:

```
GOOGLE_API_KEY              your_actual_gemini_api_key
GOOGLE_MODEL                gemini-2.5-flash
ENABLE_AI_CHAT              true
DEBUG                       false
REPO_CLONE_PATH             /tmp/ai-explainer/repos
DIAGRAM_OUTPUT_PATH         /tmp/ai-explainer/diagrams
RAG_INDEX_PATH              /tmp/ai-explainer/rag_indices
GENERATE_MERMAID            true
GENERATE_GRAPHVIZ           true
ENABLE_RAG                  true
RAG_EMBEDDING_MODEL         all-MiniLM-L6-v2
```

### Step 4: Deploy

1. Click **"Create Web Service"**
2. Wait for deployment to complete (3-5 minutes)
3. Note your service URL: `https://ai-codebase-explainer.onrender.com`
4. Test the health endpoint:
   ```
   curl https://ai-codebase-explainer.onrender.com/api/health
   ```

---

## Part 2: Deploy Frontend to Vercel

### Step 1: Initialize Vercel Project (if needed)

The frontend folder should be treated as a separate project. You can either:

**Option A: Deploy from Vercel Dashboard (Recommended)**

1. Go to https://vercel.com and sign up/log in
2. Click **"Add New Project"**
3. Select your GitHub repository
4. Select **"Root Directory"** → `frontend`
5. Click **"Deploy"**

**Option B: Deploy using Vercel CLI**

```bash
npm i -g vercel
cd frontend
vercel
```

### Step 2: Configure Environment Variables

In Vercel dashboard for the frontend project:

1. Go to **Settings** → **Environment Variables**
2. Add:
   ```
   NEXT_PUBLIC_API_URL = https://ai-codebase-explainer.onrender.com
   ```
   (Replace with your actual Render backend URL)

3. Make sure it's set for all environments (Production, Preview, Development)

### Step 3: Redeploy

After adding environment variables, trigger a redeploy:
1. Go to **Deployments** tab
2. Click on the latest deployment
3. Click **"Redeploy"**

Or simply push to GitHub:
```bash
git push origin main
```

The deployment will automatically trigger.

---

## Verification

### Test Backend API

```bash
# Get health status
curl https://your-render-url.onrender.com/api/health

# View API documentation
# Visit: https://your-render-url.onrender.com/api/docs
```

### Test Frontend

1. Visit `https://your-vercel-url.vercel.app`
2. The frontend should load successfully
3. Try analyzing a GitHub repository
4. Check browser console for any API errors (F12 → Console)

### Common Issues

**Frontend shows "Could not retrieve metadata"**
- Check that `NEXT_PUBLIC_API_URL` environment variable is set correctly in Vercel
- Verify the backend URL is publicly accessible
- Check CORS is enabled on backend (it is by default)

**Backend returns 404 errors for Gemini**
- Verify `GOOGLE_API_KEY` is set correctly
- Verify `GOOGLE_MODEL` is set to `gemini-2.5-flash` or another valid model
- Check that the API key has access to the Gemini API

**Repository cloning fails**
- Render's free tier may have limited resources
- For large repositories, consider upgrading to a paid plan
- Maximum repo size is set to 500MB by default

---

## Production Tips

### 1. Enable Persistent Storage (Optional)

Render's free tier uses ephemeral storage (data is deleted on restart). For persistent data:

1. Upgrade to a paid Render plan
2. Add a Disk volume:
   - Size: 1GB (minimum)
   - Mount path: `/mnt/data`
3. Update environment variables:
   ```
   REPO_CLONE_PATH=/mnt/data/repos
   DIAGRAM_OUTPUT_PATH=/mnt/data/diagrams
   RAG_INDEX_PATH=/mnt/data/rag_indices
   ```

### 2. Monitor Logs

- **Render**: Dashboard → "Logs" tab
- **Vercel**: Dashboard → "Deployments" → Click deployment → "Logs"

### 3. Update Frontend API URL

If you need to change the backend URL later:
1. Update `NEXT_PUBLIC_API_URL` in Vercel environment variables
2. Trigger a redeploy
3. The frontend will use the new URL on next build

### 4. Security

- **Never commit `.env` files** to GitHub (they're in `.gitignore`)
- Use Render/Vercel's environment variable management for secrets
- Regularly rotate your GOOGLE_API_KEY
- Use GitHub personal access tokens (GITHUB_TOKEN) if analyzing private repos

---

## Troubleshooting

### Render Deployment Fails

Check the logs:
1. Go to Render dashboard
2. Select your service
3. Click "Logs" tab
4. Look for error messages

Common issues:
- **Python version mismatch**: Render uses Python 3.11 by default ✓ (should work)
- **Missing dependencies**: Ensure `requirements.txt` includes all packages
- **Port binding failed**: Check `PORT` environment variable is set

### Frontend Builds Successfully but Shows Blank Page

1. Open browser DevTools (F12)
2. Check Console for errors
3. Check Network tab for failed API requests
4. Verify `NEXT_PUBLIC_API_URL` includes protocol (https://)

### API Requests Timeout

- Render free tier has 30-second timeout for HTTP responses
- Large repository analysis may exceed this
- Consider upgrading or splitting large repos

---

## Environment Variables Reference

### Backend (Render)

| Variable | Required | Default | Notes |
|----------|----------|---------|-------|
| `GOOGLE_API_KEY` | ✅ | - | Get from aistudio.google.com |
| `GOOGLE_MODEL` | ❌ | `gemini-2.5-flash` | Latest model available |
| `ENABLE_AI_CHAT` | ❌ | `true` | Set to `false` to disable AI |
| `DEBUG` | ❌ | `false` | Enable verbose logging |
| `REPO_CLONE_PATH` | ❌ | `/tmp/ai-explainer/repos` | Where repos are stored |
| `DIAGRAM_OUTPUT_PATH` | ❌ | `/tmp/ai-explainer/diagrams` | Where diagrams are saved |
| `RAG_INDEX_PATH` | ❌ | `/tmp/ai-explainer/rag_indices` | Where RAG indices are stored |

### Frontend (Vercel)

| Variable | Required | Notes |
|----------|----------|-------|
| `NEXT_PUBLIC_API_URL` | ✅ | Backend URL (e.g., https://ai-codebase-explainer.onrender.com) |

---

## Cost Summary

### Render
- **Free Tier**: 750 hours/month, shared CPU, 256MB RAM
- **Pro**: $7/month per service, dedicated CPU
- **Paid** if you add persistent storage/databases

### Vercel
- **Free Tier**: Unlimited deployments, serverless functions
- **Pro**: $20/month for advanced features

For a personal project, free tiers should suffice!

---

## Need Help?

- **Render Docs**: https://render.com/docs
- **Vercel Docs**: https://vercel.com/docs
- **FastAPI Deployment**: https://fastapi.tiangolo.com/deployment/
- **Next.js Deployment**: https://nextjs.org/docs/deployment

