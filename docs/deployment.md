# Deployment Guide: Netlify Frontend & Cloud Backend

**Project**: *Maximizing Section Throughput Using AI-Powered Precise Train Traffic Control*

This guide explains how to connect and deploy the project to **Netlify** for the frontend, and how to connect the FastAPI backend to a cloud host.

---

## 1. Quick Deploy to Netlify (Frontend)

The frontend is a modern React 18 + Vite SPA located in rontend/. All necessary Netlify configuration files have been prepared:
- 
etlify.toml in the project root
- rontend/public/_redirects (ensures SPA routing works without 404s on page refresh)
- rontend/dist/ production bundle compiled and ready

### Option A: 1-Click Git Connect (Recommended)

Because your project is linked to GitHub:
https://github.com/nithinkumarreddy1634/AI-Based-Train-Traffic-Management-System

1. Open [app.netlify.com](https://app.netlify.com/) and log in (or sign up with GitHub).
2. Click **Add new site** > **Import an existing project**.
3. Select **GitHub** and authorize Netlify.
4. Choose the repository: 
ithinkumarreddy1634/AI-Based-Train-Traffic-Management-System.
5. Netlify will automatically detect the settings from 
etlify.toml:
   - **Base directory**: rontend
   - **Build command**: 
pm run build
   - **Publish directory**: rontend/dist
6. (Optional) Set Environment Variable:
   - Key: VITE_API_URL
   - Value: https://your-backend-api-url.onrender.com (or leave blank to default to localhost)
7. Click **Deploy site**.
8. Netlify will build and provide a live URL like https://train-traffic-control.netlify.app.

---

### Option B: Instant Netlify Drop (No Git or CLI required)

If you want an instant live URL in under 30 seconds:

1. Open [app.netlify.com/drop](https://app.netlify.com/drop) in your browser.
2. Drag and drop the folder:
   c:\Users\nithi\Maximizing Section Throughput Using Al- Powered Precise Train Traffic Control\frontend\dist
3. Netlify will upload and instantly publish the site with a live URL.

---

### Option C: Netlify CLI (Command Line)

To deploy directly from PowerShell:

`ash
# 1. Install Netlify CLI globally
npm install -g netlify-cli

# 2. Login to your Netlify account (opens browser)
netlify login

# 3. Deploy the pre-built dist directory to production
cd frontend
netlify deploy --prod --dir=dist
`

---

## 2. Backend Cloud Deployment (FastAPI + ML Engine)

Since Netlify hosts static frontends and serverless functions, the Python FastAPI backend (which includes SQLite, the kinematic simulation loop, and ML inference) is best hosted on free cloud container platforms:

### Deploying Backend to Render.com (Recommended Free Tier)
1. Go to [render.com](https://render.com) and click **New** > **Web Service**.
2. Connect your GitHub repository.
3. Configure settings:
   - **Root Directory**: . (or blank)
   - **Environment**: Python 3
   - **Build Command**: pip install -r requirements.txt && python seed_database.py
   - **Start Command**: uvicorn backend.app.main:app --host 0.0.0.0 --port 
4. Copy the resulting URL (e.g., https://train-control-api.onrender.com).
5. In Netlify Site Settings > **Environment variables**, set:
   - VITE_API_URL = https://train-control-api.onrender.com
6. Trigger a redeploy in Netlify!
