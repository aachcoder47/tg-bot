# 🚀 DEPLOYMENT GUIDE - Martyn Steady Corp LLC

## Option 1: Railway.app (RECOMMENDED - Easiest)

### Step 1: Prepare Your Code
1. Create a GitHub account if you don't have one
2. Create a new repository on GitHub
3. Upload your code:
```bash
cd c:\Users\ASUS\Downloads\tg-bot
git init
git add .
git commit -m "Initial commit"
git branch -M main
git remote add origin YOUR_GITHUB_REPO_URL
git push -u origin main
```

### Step 2: Deploy on Railway
1. Go to https://railway.app
2. Sign up with GitHub
3. Click "New Project"
4. Select "Deploy from GitHub repo"
5. Choose your repository
6. Railway will auto-detect Python and deploy

### Step 3: Set Environment Variables
In Railway dashboard:
1. Go to your project
2. Click "Variables" tab
3. Add:
   - `TELEGRAM_BOT_TOKEN` = 8306417982:AAG_iTJsRV3aMviAqrV1gOk5ecICNPh4fg0
   - `ADMIN_CHAT_ID` = 8203104058

### Step 4: Get Your URL
Railway will give you a URL like: `https://your-app.railway.app`

---

## Option 2: Render.com (Free Tier)

### Step 1: Push to GitHub (same as above)

### Step 2: Deploy on Render
1. Go to https://render.com
2. Sign up with GitHub
3. Click "New +" → "Web Service"
4. Connect your GitHub repo
5. Configure:
   - **Name:** martyn-steady-corp
   - **Environment:** Python 3
   - **Build Command:** `pip install -r requirements.txt`
   - **Start Command:** `uvicorn main:app --host 0.0.0.0 --port $PORT`

### Step 3: Environment Variables
Add in Render dashboard:
- `TELEGRAM_BOT_TOKEN` = 8306417982:AAG_iTJsRV3aMviAqrV1gOk5ecICNPh4fg0
- `ADMIN_CHAT_ID` = 8203104058

---

## Option 3: DigitalOcean ($5/month)

### Step 1: Create Droplet
1. Go to https://digitalocean.com
2. Create account
3. Create a Droplet (Ubuntu 22.04)
4. Choose $5/month plan

### Step 2: SSH into Server
```bash
ssh root@YOUR_DROPLET_IP
```

### Step 3: Install Dependencies
```bash
apt update
apt install python3-pip nginx -y
```

### Step 4: Upload Your Code
Use FileZilla or SCP to upload your files to `/var/www/tg-bot`

### Step 5: Install Python Packages
```bash
cd /var/www/tg-bot
pip3 install -r requirements.txt
```

### Step 6: Run with PM2 or Systemd
```bash
# Install PM2
npm install -g pm2

# Start app
pm2 start "uvicorn main:app --host 0.0.0.0 --port 8000" --name martyn-steady
pm2 save
pm2 startup
```

### Step 7: Configure Nginx
Create `/etc/nginx/sites-available/martyn-steady`:
```nginx
server {
    listen 80;
    server_name YOUR_DOMAIN_OR_IP;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
    }
}
```

Enable site:
```bash
ln -s /etc/nginx/sites-available/martyn-steady /etc/nginx/sites-enabled/
nginx -t
systemctl restart nginx
```

---

## Option 4: Quick Test with Ngrok (Temporary)

For quick testing/demo:

1. Download ngrok: https://ngrok.com/download
2. Run your app locally:
```bash
python main.py
```
3. In another terminal:
```bash
ngrok http 8000
```
4. Ngrok will give you a public URL like: `https://abc123.ngrok.io`

**Note:** This URL changes every time you restart ngrok (free tier)

---

## 🔒 IMPORTANT SECURITY NOTES

### Before Deploying:
1. **Never commit sensitive data to GitHub**
2. **Use environment variables** for:
   - TELEGRAM_BOT_TOKEN
   - ADMIN_CHAT_ID

### Update main.py:
Replace hardcoded values with environment variables:
```python
import os
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
ADMIN_CHAT_ID = os.getenv("ADMIN_CHAT_ID")
```

---

## 📊 Cost Comparison

| Platform | Free Tier | Paid | Best For |
|----------|-----------|------|----------|
| Railway | ✅ $5 credit/month | $5+/month | Easy deployment |
| Render | ✅ Yes (sleeps) | $7/month | Free start |
| DigitalOcean | ❌ | $5/month | Full control |
| PythonAnywhere | ✅ Limited | $5/month | Python apps |
| Ngrok | ✅ Temporary | $8/month | Testing only |

---

## 🎯 MY RECOMMENDATION

**Start with Railway.app:**
1. Easiest to deploy
2. Free $5 credit monthly
3. No sleep/downtime
4. WebSocket support
5. Automatic HTTPS
6. Takes 5 minutes to deploy

**Later, move to DigitalOcean if:**
- You need more control
- You want to add custom features
- You're getting high traffic

---

## 📞 Need Help?

If you run into issues:
1. Check Railway/Render logs
2. Verify environment variables are set
3. Make sure requirements.txt has all dependencies
4. Test locally first with `python main.py`

---

## ✅ Deployment Checklist

- [ ] Code pushed to GitHub
- [ ] Environment variables configured
- [ ] Telegram bot token set
- [ ] Admin chat ID set
- [ ] Test the deployed URL
- [ ] Update Telegram link in footer
- [ ] Test chat bot functionality
- [ ] Verify all pages load correctly

---

**Your website is ready to deploy! Choose Railway.app for the easiest experience.**
