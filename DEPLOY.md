# MarketingOS 2.0 Deployment Guide

## Architecture
- **Backend**: FastAPI (Python) → Deploy to Railway
- **Frontend**: React → Deploy to Vercel

---

## Step 1: Deploy Backend to Railway

### 1.1 Create Railway Account
1. Go to [railway.app](https://railway.app)
2. Sign up with GitHub

### 1.2 Create New Project
1. Click "New Project"
2. Select "Deploy from GitHub repo"
3. Connect your MarketingOS2.0 repository
4. Railway auto-detects the Dockerfile

### 1.3 Add Environment Variables
In Railway dashboard → Variables, add ALL these:

```
GEMINI_API_KEY=your_value
GROQ_API_KEY=your_value
BRAVE_API_KEY=your_value
GA4_PROPERTY_ID=your_value
SEARCH_CONSOLE_SITE_URL=https://your-site.com
GOOGLE_ADS_CUSTOMER_ID=your_value
GOOGLE_ADS_DEVELOPER_TOKEN=your_value
HUBSPOT_ACCESS_TOKEN=your_value
DATAFORSEO_LOGIN=your_value
DATAFORSEO_PASSWORD=your_value
WORDPRESS_URL=https://your-site.com
WORDPRESS_USERNAME=your_value
WORDPRESS_APP_PASSWORD=your_value
```

### 1.4 Add Google Service Account
For Google APIs (GA4, Search Console, Ads):
1. In Railway Variables, add:
   ```
   GOOGLE_SERVICE_ACCOUNT_JSON_CONTENT=<paste entire JSON content here>
   ```
2. Or mount the JSON file as a volume

### 1.5 Deploy
1. Railway auto-deploys on push
2. Get your backend URL: `https://your-app.railway.app`
3. Test: `https://your-app.railway.app/docs`

---

## Step 2: Deploy Frontend to Vercel

### 2.1 Update API URL
Edit `frontend/src/App.js` line 25:
```javascript
const API_BASE = 'https://your-app.railway.app';  // Your Railway URL
```

### 2.2 Create Vercel Account
1. Go to [vercel.com](https://vercel.com)
2. Sign up with GitHub

### 2.3 Deploy
1. Click "New Project"
2. Import your GitHub repo
3. Set root directory to `frontend`
4. Framework: Create React App (auto-detected)
5. Click Deploy

### 2.4 Get Frontend URL
Your frontend is live at: `https://your-app.vercel.app`

---

## Step 3: Connect Frontend to Backend

### Option A: Update Code (Recommended)
```javascript
// frontend/src/App.js
const API_BASE = process.env.REACT_APP_API_URL || 'http://localhost:8000';
```

Then in Vercel → Settings → Environment Variables:
```
REACT_APP_API_URL=https://your-app.railway.app
```

### Option B: Direct Edit
Just change the API_BASE constant before deploying.

---

## Quick Deploy Commands

### Local Development
```bash
# Terminal 1 - Backend
cd MarketingOS2.0
uvicorn backend.main:app --reload --port 8000

# Terminal 2 - Frontend
cd MarketingOS2.0/frontend
npm start
```

### Production Build Test
```bash
# Backend
docker build -t marketingos-backend .
docker run -p 8000:8000 --env-file .env marketingos-backend

# Frontend
cd frontend
npm run build
npx serve -s build
```

---

## Verify Deployment

### Backend Health Check
```bash
curl https://your-app.railway.app/health
# Should return: {"status":"healthy","agents":10}
```

### Integration Status
```bash
curl https://your-app.railway.app/api/integrations/status
# Shows which integrations are connected
```

### API Docs
Visit: `https://your-app.railway.app/docs`

---

## Troubleshooting

### Backend won't start
- Check Railway logs for errors
- Verify all environment variables are set
- Check if PORT is being used correctly

### Frontend can't connect to backend
- Verify CORS is enabled (it is by default)
- Check API_BASE URL is correct
- Check browser console for errors

### Integrations not working
- Verify credentials in environment variables
- For Google APIs: ensure service account has correct permissions
- For HubSpot: check if access token is valid

---

## Cost Estimates

| Service | Free Tier | Paid |
|---------|-----------|------|
| Railway | $5/month credit | ~$5-20/month |
| Vercel | 100GB bandwidth | Free for most use |
| Total | ~$5/month | ~$10-25/month |

---

## Security Notes

1. Never commit `.env` to git
2. Use Railway/Vercel secrets for sensitive data
3. Set specific CORS origins in production:
   ```python
   allow_origins=["https://your-frontend.vercel.app"]
   ```
