# Render Deployment Checklist

## ✅ Pre-Deployment Checklist

### 1. Essential Files Included
- [x] `app.py` - Main application entry point
- [x] `requirements.txt` - All dependencies
- [x] `render.yaml` - Deployment configuration
- [x] `src/store/` - Vectorstore files (FAISS index)
- [x] `documents/` - All HR documents
- [x] `src/api/app_with_integrations.py` - Flask app

### 2. Environment Variables (Set in Render Dashboard)
- [ ] `GROQ_API_KEY` - Required for LLM functionality
- [ ] `SLACK_BOT_TOKEN` - Optional for Slack integration
- [ ] `SLACK_SIGNING_SECRET` - Optional for Slack integration
- [ ] `SLACK_APP_TOKEN` - Optional for Slack integration
- [ ] `EMAIL_USERNAME` - Optional for email integration
- [ ] `EMAIL_PASSWORD` - Optional for email integration

### 3. Build Configuration
- [x] Python 3.11.0 specified
- [x] Build command: `pip install -r requirements.txt`
- [x] Start command: `python app.py`
- [x] Health check path: `/api/status`
- [x] Health check timeout: 300 seconds

## 🚀 Deployment Steps

### 1. Push to GitHub
```bash
git add .
git commit -m "Prepare for Render deployment"
git push origin main
```

### 2. Connect to Render
1. Go to [Render Dashboard](https://dashboard.render.com)
2. Click "New +" → "Web Service"
3. Connect your GitHub repository
4. Select the repository

### 3. Configure Environment Variables
In Render dashboard, add these environment variables:
- `GROQ_API_KEY`: Your GROQ API key
- `SLACK_BOT_TOKEN`: Your Slack bot token (optional)
- `SLACK_SIGNING_SECRET`: Your Slack signing secret (optional)
- `SLACK_APP_TOKEN`: Your Slack app token (optional)

### 4. Deploy
1. Click "Create Web Service"
2. Wait for build to complete
3. Check health status at `/api/status`

## 🔍 Post-Deployment Verification

### 1. Health Check
- [ ] Visit `https://your-app-name.onrender.com/api/status`
- [ ] Should return: `{"bot":{"status":"ready","message":"Bot ready!"}}`

### 2. Web Interface
- [ ] Visit `https://your-app-name.onrender.com/`
- [ ] Should show the HR Policy Assistant interface
- [ ] Status should show "Ready" instead of "Initializing..."

### 3. Chat Functionality
- [ ] Type a question or click sidebar buttons
- [ ] Should receive proper responses
- [ ] No errors in browser console

### 4. API Testing
- [ ] Test `/api/ask` endpoint with POST request
- [ ] Should return JSON response with answer

## 🐛 Troubleshooting

### Common Issues:
1. **Build fails**: Check requirements.txt for missing dependencies
2. **Bot stuck on "Initializing"**: Check GROQ_API_KEY environment variable
3. **Health check fails**: Increase timeout in render.yaml
4. **Vectorstore not found**: Ensure src/store/ files are committed

### Logs:
- Check Render logs for detailed error messages
- Monitor application logs for initialization issues

## 📝 Notes
- The bot will take 1-2 minutes to initialize on first deployment
- Vectorstore files are ~5MB total
- Model cache will be downloaded on first run (~200MB)
- Free tier has limitations on build time and memory
