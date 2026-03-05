# Frontend Quick Start Guide

## Get Running in 5 Minutes

### 1. Prerequisites Check

```bash
node --version    # Should be 18.0.0 or higher
npm --version     # Should be 8.0.0 or higher
```

If not installed, download from [nodejs.org](https://nodejs.org)

### 2. Install Dependencies

```bash
cd frontend
npm install
```

Expected output:
```
added 287 packages in 45s
```

### 3. Configure API Connection

Backend must be running first:

```bash
# In a separate terminal, from project root:
python -m uvicorn backend.main:app --reload --port 8000
```

You should see:
```
INFO:     Uvicorn running on http://127.0.0.1:8000
```

### 4. Start Frontend

```bash
cd frontend
npm run dev
```

Expected output:
```
> next dev

  ▲ Next.js 14.0.0
  ✓ Ready in 1.2s
```

### 5. Open Browser

Navigate to: **http://localhost:3000**

---

## Using the Application

### Analyze a Repository

1. Enter GitHub URL: `https://github.com/user/repo`
2. Click **"Analyze Repository"** button
3. Wait for analysis (2-5 seconds depending on repo size)
4. View results in the dashboard

### View Architecture Diagram

Scroll down to the **"Architecture Diagram"** section
- Displays Mermaid diagram from backend
- Shows system components and relationships
- Auto-generates from backend analysis

### Ask Questions

Scroll to **"Ask About the Architecture"** section:
- Click **"Popular Questions"** buttons (quick presets)
- Or type your own question
- Click **"Ask"** to submit
- View AI-powered response

---

## Common Issues & Solutions

### Issue: "API Unavailable" Message

**Solution 1**: Verify backend is running
```bash
curl http://localhost:8000/api/health
```

Should return:
```json
{"status": "ok"}
```

**Solution 2**: Check API URL in environment
```bash
# Verify .env.local exists
cat .env.local
```

Should show:
```env
NEXT_PUBLIC_API_URL=http://localhost:8000
```

### Issue: "Cannot find module" Error

**Solution**: Reinstall dependencies
```bash
rm -rf node_modules package-lock.json
npm install
```

### Issue: Blank Page or Console Errors

**Solution 1**: Hard refresh browser
```
Ctrl+Shift+R (Windows/Linux)
Cmd+Shift+R (Mac)
```

**Solution 2**: Restart development server
```bash
Ctrl+C  # Stop server
npm run dev  # Restart
```

### Issue: Repository Analysis Fails

**Possible causes**:
1. GitHub API rate limit reached (public repos: 60 req/hr)
2. Repository is private (need authentication)
3. Invalid GitHub URL format

**Solution**: Use different repository or wait 1 hour

---

## Environment Configuration

### .env.local File

Create `.env.local` in frontend directory:

```bash
cp .env.local.example .env.local
```

Edit if needed:
```env
# Backend API URL
NEXT_PUBLIC_API_URL=http://localhost:8000

# Optional: Enable debug logging
NEXT_PUBLIC_DEBUG=false
```

### Environment Variables Explained

| Variable | Purpose | Default |
|----------|---------|---------|
| `NEXT_PUBLIC_API_URL` | Backend API location | `http://localhost:8000` |
| `NEXT_PUBLIC_DEBUG` | Enable console logging | `false` |

---

## Development Commands

### Development Server
```bash
npm run dev
```
- Hot reload on file changes
- Source maps for debugging
- Runs on http://localhost:3000

### Production Build
```bash
npm run build
```

Creates optimized bundle in `.next/` directory

### Production Server
```bash
npm start
```

Runs optimized production build
- Use after `npm run build`
- Faster than development mode

### Linting (if configured)
```bash
npm run lint
```

Checks code quality

---

## Next.js Features Used

### Image Optimization
- Automatic lazy loading
- Format conversion
- Responsive sizing

### Code Splitting
- Automatic route-based splitting
- Faster page loads

### CSS Optimization
- Tailwind CSS purging
- Minification
- Autoprefixing

---

## Troubleshooting Checklist

- [ ] Node.js 18+ installed (`node --version`)
- [ ] Dependencies installed (`npm install`)
- [ ] Backend running at http://localhost:8000 (`curl http://localhost:8000/api/health`)
- [ ] Frontend running at http://localhost:3000
- [ ] Browser developer console has no errors (F12)
- [ ] Network tab shows successful API calls

---

## Getting Help

### Check Logs

**Browser Console** (F12):
```javascript
// Should see no red errors
// May see warnings (safe to ignore)
```

**Terminal Output**:
```bash
# Check for Next.js compilation errors
# Should say "Ready in X.Xs"
```

### Debug Mode

Enable console logging:

```javascript
// Add to .env.local
NEXT_PUBLIC_DEBUG=true
```

Then check browser console for detailed logs

### Performance Testing

```bash
# Start server with profiling
npm run dev -- --experimental-app-dir

# Check Network tab for slow requests
# Should be < 1s per request for most operations
```

---

## Build & Deploy

### Build for Production

```bash
npm run build
```

Creates:
- `.next/` directory with optimized code
- Static files ready for deployment

### Deploy to Vercel (Easiest)

1. Push code to GitHub
2. Go to [vercel.com](https://vercel.com)
3. Import repository
4. Set `NEXT_PUBLIC_API_URL` environment variable
5. Deploy (auto on push)

### Deploy to Docker

```bash
docker build -t ai-frontend .
docker run -p 3000:3000 \
  -e NEXT_PUBLIC_API_URL=http://backend:8000 \
  ai-frontend
```

### Deploy to Traditional Server

```bash
npm run build
# Copy to server
npm start
```

---

## Project Structure Quick Reference

```
frontend/
├── pages/
│   └── index.js           Main dashboard page
├── components/
│   ├── RepositoryInput    URL input form
│   ├── AnalysisSummary    Results display
│   ├── ArchitectureDiagram Mermaid renderer
│   └── QuestionInput      Q&A interface
├── lib/
│   └── api.js             HTTP client
├── styles/
│   └── globals.css        Tailwind styles
├── package.json           Dependencies
├── next.config.js         Next.js config
└── .env.local            Environment vars
```

---

## Quick Links

- **Frontend Code**: `frontend/` directory
- **Frontend Docs**: [FRONTEND_ARCHITECTURE_REPORT.md](FRONTEND_ARCHITECTURE_REPORT.md)
- **Backend**: Root directory with `backend/main.py`
- **Backend Docs**: Check backend README

---

## What's Next?

After getting running:

1. ✅ Analyze a real GitHub repository
2. ✅ View the Mermaid architecture diagram
3. ✅ Ask questions about the repo architecture
4. ✅ Check browser console for any errors
5. ✅ Read [FRONTEND_ARCHITECTURE_REPORT.md](FRONTEND_ARCHITECTURE_REPORT.md) for deeper understanding

---

**All set!** You should now have the AI Codebase Explainer frontend running locally. 🚀
