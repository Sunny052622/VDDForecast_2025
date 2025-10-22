# 📊 Google Sheets Setup Guide

This guide will help you connect your VDD Sales Analysis Dashboard to Google Sheets for real-time data access.

## 🎯 Overview

By connecting to Google Sheets, you can:
- Update data daily without redeploying
- Access the dashboard from anywhere online
- Collaborate with your team on data entry
- Automatic data refresh every 5 minutes

---

## 📋 Step-by-Step Setup

### Step 1: Upload Your Excel Data to Google Sheets

1. **Go to Google Sheets**: https://sheets.google.com
2. **Create a new spreadsheet** or click **File → Import**
3. **Upload your `data.xlsx` file**
4. **IMPORTANT**: Make sure you have these three sheets:
   - `SalesData` - Your main sales transactions
   - `nameRef` - Product name reference table
   - `comboRef` - Combo items reference table
5. **Keep the exact same sheet names and column headers** as your Excel file
6. **Copy the spreadsheet URL** from your browser (you'll need this later)

### Step 2: Create a Google Cloud Project

1. **Go to Google Cloud Console**: https://console.cloud.google.com/
2. **Create a new project**:
   - Click on the project dropdown at the top
   - Click "New Project"
   - Name it: `VDD-Sales-Dashboard`
   - Click "Create"

### Step 3: Enable Google Sheets API

1. In your Google Cloud Console, go to **APIs & Services → Library**
2. Search for "**Google Sheets API**"
3. Click on it and click **"Enable"**
4. Also search for "**Google Drive API**" and enable it

### Step 4: Create a Service Account

1. Go to **APIs & Services → Credentials**
2. Click **"Create Credentials"** → **"Service Account"**
3. Fill in the details:
   - **Service account name**: `vdd-dashboard-reader`
   - **Service account ID**: Will auto-fill
   - Click **"Create and Continue"**
4. **Grant access** (optional):
   - Role: Select **"Viewer"** (read-only access)
   - Click **"Continue"** → **"Done"**

### Step 5: Create Service Account Key

1. Click on the service account you just created
2. Go to the **"Keys"** tab
3. Click **"Add Key"** → **"Create new key"**
4. Choose **JSON** format
5. Click **"Create"**
6. A JSON file will download - **KEEP THIS FILE SAFE!** 🔐
   - This file contains your credentials
   - Never share it publicly or commit it to Git

### Step 6: Share Google Sheet with Service Account

1. **Open your JSON key file** and find the `client_email` field
   - It looks like: `vdd-dashboard-reader@your-project.iam.gserviceaccount.com`
2. **Go back to your Google Sheet**
3. Click **"Share"** button (top right)
4. **Paste the service account email**
5. Give it **"Viewer"** permissions (read-only)
6. **Uncheck "Notify people"** (it's a service account, not a person)
7. Click **"Share"**

---

## 🚀 Deployment Configuration

### For Local Testing:

1. **Create `.streamlit/secrets.toml`** in your project folder:

```toml
# Google Sheets Configuration
[gsheet]
spreadsheet_url = "YOUR_GOOGLE_SHEET_URL_HERE"

# Paste the contents of your JSON key file here
[gcp_service_account]
type = "service_account"
project_id = "your-project-id"
private_key_id = "your-private-key-id"
private_key = "-----BEGIN PRIVATE KEY-----\nYOUR-PRIVATE-KEY-HERE\n-----END PRIVATE KEY-----\n"
client_email = "vdd-dashboard-reader@your-project.iam.gserviceaccount.com"
client_id = "123456789"
auth_uri = "https://accounts.google.com/o/oauth2/auth"
token_uri = "https://oauth2.googleapis.com/token"
auth_provider_x509_cert_url = "https://www.googleapis.com/oauth2/v1/certs"
client_x509_cert_url = "https://www.googleapis.com/robot/v1/metadata/x509/your-service-account%40your-project.iam.gserviceaccount.com"
```

2. **DO NOT commit `secrets.toml` to Git!** Add it to `.gitignore`

### For Streamlit Cloud Deployment:

When deploying to Streamlit Cloud (covered in DEPLOYMENT_GUIDE.md):

1. Go to your app settings in Streamlit Cloud
2. Click on **"Secrets"**
3. Paste the same content from your `secrets.toml` file
4. Click **"Save"**

---

## 🔄 Daily Data Updates

Once set up, you can update your data daily:

1. **Open your Google Sheet**
2. **Update the data** in any of the three sheets:
   - Add new sales transactions to `SalesData`
   - Update product names in `nameRef`
   - Modify combo items in `comboRef`
3. **Save** (Google Sheets auto-saves)
4. **Wait 5 minutes** or click the **"🔄 Refresh Data"** button in the dashboard sidebar

The dashboard will automatically pull the latest data from Google Sheets!

---

## ✅ Testing Your Setup

1. Run the dashboard locally:
   ```bash
   python -m streamlit run dashboard.py
   ```

2. Check the sidebar:
   - You should see "✅ Google Sheets: Enabled"
   - It should say "📊 Data loaded from Google Sheets"

3. Try the refresh button:
   - Make a small change in your Google Sheet
   - Click "🔄 Refresh Data" in the dashboard
   - Verify the change appears

---

## 🔧 Troubleshooting

### "Failed to load data from Google Sheets"

- **Check**: Is the service account email added to your sheet with Viewer permissions?
- **Check**: Are all three sheets present with correct names? (`SalesData`, `nameRef`, `comboRef`)
- **Check**: Is the spreadsheet URL correct in secrets.toml?

### "Authentication failed"

- **Check**: Is the JSON key file correct?
- **Check**: Did you enable both Google Sheets API and Google Drive API?
- **Check**: Are the credentials properly formatted in secrets.toml? (Watch for line breaks in private_key)

### Dashboard loads but shows old data

- Click the "🔄 Refresh Data" button
- Data cache refreshes automatically every 5 minutes

---

## 🎉 You're Done!

Your dashboard is now connected to Google Sheets and ready for deployment! 

Next: See [DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md) for deploying to the web.

---

## 📧 Support

If you encounter issues:
1. Check that all API keys are enabled
2. Verify service account has access to the sheet
3. Ensure sheet names match exactly
4. Check the Streamlit terminal for error messages

