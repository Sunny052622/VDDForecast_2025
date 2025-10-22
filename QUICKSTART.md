# ⚡ Quick Start Guide

Get your VDD Sales Analysis Dashboard running in 5 minutes!

---

## 🎯 Choose Your Path

### Path A: Local Testing (Fastest)
**Time: 2 minutes** | Best for: Testing and development

### Path B: Online Deployment with Google Sheets  
**Time: 30 minutes** | Best for: Production use with daily updates

---

## 🚀 Path A: Local Testing

### Step 1: Install Dependencies
```bash
pip install -r requirements.txt
```

### Step 2: Place Your Data
Make sure `data.xlsx` is in the project folder with these sheets:
- `SalesData`
- `nameRef`
- `comboRef`

### Step 3: Run the Dashboard
```bash
python -m streamlit run dashboard.py
```

### Step 4: Open in Browser
Go to: **http://localhost:8501**

**Done!** 🎉 You now have a local analytics dashboard.

---

## 🌐 Path B: Online Deployment

### Overview
1. Upload data to Google Sheets (~5 min)
2. Set up Google Cloud credentials (~15 min)
3. Deploy to Streamlit Cloud (~10 min)

### Step 1: Google Sheets Setup
**Detailed guide**: [GOOGLE_SHEETS_SETUP.md](GOOGLE_SHEETS_SETUP.md)

Quick checklist:
- [ ] Upload `data.xlsx` to Google Sheets
- [ ] Create Google Cloud project
- [ ] Enable Google Sheets API & Drive API
- [ ] Create service account
- [ ] Download JSON key
- [ ] Share sheet with service account email

### Step 2: Configure Secrets

Create `.streamlit/secrets.toml` (for local testing):

```toml
[gsheet]
spreadsheet_url = "YOUR_GOOGLE_SHEETS_URL"

[gcp_service_account]
# Paste contents from downloaded JSON key file
type = "service_account"
project_id = "your-project-id"
private_key_id = "xxx"
private_key = "-----BEGIN PRIVATE KEY-----\nYOUR-KEY\n-----END PRIVATE KEY-----\n"
client_email = "xxx@xxx.iam.gserviceaccount.com"
client_id = "123456789"
auth_uri = "https://accounts.google.com/o/oauth2/auth"
token_uri = "https://oauth2.googleapis.com/token"
auth_provider_x509_cert_url = "https://www.googleapis.com/oauth2/v1/certs"
client_x509_cert_url = "https://www.googleapis.com/robot/v1/metadata/x509/xxx"
```

### Step 3: Test Locally
```bash
python -m streamlit run dashboard.py
```

Check sidebar for: "✅ Google Sheets: Enabled"

### Step 4: Deploy Online
**Detailed guide**: [DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md)

Quick steps:
```bash
# Initialize git
git init

# Add files
git add .
git commit -m "Initial commit"

# Push to GitHub
git remote add origin https://github.com/YOUR_USERNAME/VDDForecast_2025.git
git push -u origin main
```

Then:
1. Go to https://share.streamlit.io/
2. Sign in with GitHub
3. Click "New app"
4. Select your repository and `dashboard.py`
5. Add secrets (same as secrets.toml)
6. Deploy!

**Done!** 🎉 Your dashboard is now online at `https://your-app.streamlit.app`

---

## 📱 Daily Usage (After Setup)

### Update Data
1. Open your Google Sheet
2. Add new rows to `SalesData`
3. Save (auto-saves)
4. Dashboard updates within 5 minutes

### View Dashboard
- Open your Streamlit app URL
- Or click "🔄 Refresh Data" for immediate update

### Share Insights
- Tab 9: Generate WhatsApp-friendly targets
- Download CSVs from any tab
- Share your app URL with team

---

## 🔧 Troubleshooting

### "streamlit not found"
```bash
pip install streamlit
# or
python -m pip install -r requirements.txt
```

### "Failed to load data"
- Check `data.xlsx` exists
- Verify sheet names: `SalesData`, `nameRef`, `comboRef`
- Check Google Sheets credentials

### Google Sheets not connecting
- Verify service account has access to sheet
- Check secrets.toml format
- See [GOOGLE_SHEETS_SETUP.md](GOOGLE_SHEETS_SETUP.md)

---

## 📚 Next Steps

After getting it running:

- [ ] Explore all 9 tabs of the dashboard
- [ ] Set up filters to analyze specific outlets
- [ ] Generate your first weekly forecast (Tab 8)
- [ ] Create WhatsApp targets (Tab 9)
- [ ] Share the app URL with your team

---

## 🆘 Need Help?

- **Local issues**: Check terminal for error messages
- **Google Sheets**: See [GOOGLE_SHEETS_SETUP.md](GOOGLE_SHEETS_SETUP.md)
- **Deployment**: See [DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md)
- **Feature questions**: See [README.md](README.md)

---

## 📞 Quick Reference

| Task | Command |
|------|---------|
| Install packages | `pip install -r requirements.txt` |
| Run locally | `python -m streamlit run dashboard.py` |
| Local URL | http://localhost:8501 |
| Stop server | Press `Ctrl+C` |
| Clear cache | Click "🔄 Refresh Data" in sidebar |

---

**Happy Analyzing! 📊**

