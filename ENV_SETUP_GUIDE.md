# Environment Setup Guide - Gold Tier AI Employee

This guide walks you through configuring the `.env` file for your AI Employee system.

---

## Quick Start

### Step 1: Copy the Template

```bash
# Windows (Command Prompt)
copy .env.example .env

# Windows (PowerShell)
Copy-Item .env.example .env

# Linux/Mac
cp .env.example .env
```

### Step 2: Configure Required Settings

**Minimum required for Gold Tier:**

1. **Odoo ERP** (if using Docker)
   - `ODOO_ADMIN_PASSWORD` - Secure password for Odoo admin
   - `ODOO_DB_PASSWORD` - Secure password for PostgreSQL

2. **Gmail** (for email integration)
   - Follow `generate_gmail_credentials.py` to get credentials

3. **Social Media** (for posting)
   - LinkedIn: `LINKEDIN_EMAIL` and `LINKEDIN_PASSWORD`
   - Facebook: `FACEBOOK_PAGES` (your page names)
   - Twitter: `TWITTER_USERNAME` and `TWITTER_PASSWORD`

4. **Claude Code**
   - Ensure Claude Code is installed and authenticated locally

---

## Configuration Sections

### 1. Odoo ERP (Docker)

**Required if using Odoo integration:**

```env
ODOO_ADMIN_PASSWORD=YourSecureAdminPassword123!
ODOO_DB_PASSWORD=YourSecureDBPassword123!
ODOO_DB_USER=odoo
ODOO_DB_NAME=odoo_db
ODOO_URL=http://localhost:8069
ODOO_DB=odoo_db
ODOO_USERNAME=admin
ODOO_PASSWORD=YourSecureAdminPassword123!
```

**Setup Steps:**
1. Set strong passwords
2. Run: `cd docker && docker-compose up -d`
3. Access Odoo at: http://localhost:8069
4. Create database `odoo_db`
5. Install Accounting module

---

### 2. Gmail API

**Required for email watching/sending:**

```env
GMAIL_CLIENT_ID=your-client-id.apps.googleusercontent.com
GMAIL_CLIENT_SECRET=your-client-secret
GMAIL_SENDER_EMAIL=your-email@gmail.com
```

**Setup Steps:**
1. Run: `python generate_gmail_credentials.py`
2. Follow OAuth flow in browser
3. `gmail_credentials.json` will be created automatically

---

### 3. LinkedIn

**Required for LinkedIn auto-posting:**

```env
LINKEDIN_EMAIL=your-linkedin-email@example.com
LINKEDIN_PASSWORD=YourLinkedInPassword123!
LINKEDIN_USERNAME=your-linkedin-username
```

**Note:** LinkedIn automation uses browser automation (Playwright). Ensure you can log in manually first.

---

### 4. Facebook/Instagram

**Required for Facebook/Instagram integration:**

```env
FACEBOOK_PAGES=YourBusinessPage,YourOtherPage
INSTAGRAM_ACCOUNTS=yourbusiness,yourbrand
```

**Optional - Graph API (advanced):**
```env
FACEBOOK_ACCESS_TOKEN=your-access-token
FACEBOOK_PAGE_ID=your-page-id
INSTAGRAM_BUSINESS_ACCOUNT_ID=your-ig-account-id
```

**Setup Steps:**
1. Add your Facebook Page names to `FACEBOOK_PAGES`
2. Add Instagram usernames to `INSTAGRAM_ACCOUNTS`
3. For Graph API: Create Facebook App at developers.facebook.com

---

### 5. Twitter/X

**Required for Twitter monitoring/posting:**

```env
TWITTER_USERNAME=YourUsername
TWITTER_EMAIL=your-email@example.com
TWITTER_PASSWORD=YourTwitterPassword123!
TWITTER_HASHTAGS=AI,Automation,Tech
```

**Optional - Twitter API v2:**
```env
TWITTER_API_KEY=your-api-key
TWITTER_API_SECRET=your-api-secret
TWITTER_ACCESS_TOKEN=your-access-token
```

---

### 6. WhatsApp

**Required for WhatsApp monitoring:**

```env
WHATSAPP_SESSION_PATH=./whatsapp_session
WHATSAPP_KEYWORDS=urgent,asap,invoice,payment,help
```

**Setup Steps:**
1. First run will open WhatsApp Web in browser
2. Scan QR code with your phone
3. Session saved to `whatsapp_session/` folder

---

### 7. Claude Code Configuration

**For Ralph Wiggum loop and AI processing:**

```env
CLAUDE_MODEL=claude-sonnet-4-20250514
CLAUDE_MAX_TOKENS=4096
RALPH_MAX_ITERATIONS=10
RALPH_MAX_DURATION_MINUTES=60
```

**Note:** Claude Code must be installed and authenticated locally.

---

### 8. System Configuration

**Recommended defaults:**

```env
VAULT_PATH=AI_Employee_Vault
LOG_LEVEL=INFO
APPROVAL_TIMEOUT_SECONDS=3600
MAX_RETRY_ATTEMPTS=3
```

---

### 9. Security Settings

**Human-in-the-loop thresholds:**

```env
SOCIAL_AUTO_APPROVE_LIMIT=0        # 0 = always require approval
INVOICE_AUTO_APPROVE_LIMIT=0       # 0 = always require approval
PAYMENT_AUTO_APPROVE_LIMIT=0       # 0 = always require approval
EMAIL_NEW_CONTACT_APPROVAL=true    # Require approval for new contacts
```

**Adjust based on your trust level:**
- Set to `100` to auto-approve invoices under $100
- Set to `50` to auto-approve payments under $50

---

### 10. CEO Briefing

**Weekly briefing configuration:**

```env
CEO_BRIEFING_SCHEDULE=0 7 * * 1    # Monday 7:00 AM
BRIEFING_INCLUDE_FINANCIALS=true
BRIEFING_INCLUDE_SOCIAL=true
BRIEFING_INCLUDE_TASKS=true
```

---

## Security Best Practices

### ✅ DO:
- Use strong, unique passwords
- Rotate credentials monthly
- Keep `.env` file private (already in `.gitignore`)
- Use environment-specific values for production
- Enable approval workflows for sensitive actions

### ❌ DON'T:
- Never commit `.env` to version control
- Never share `.env` file
- Don't use default passwords in production
- Don't disable approval workflows completely

---

## Testing Configuration

### Test Odoo Connection:
```bash
python -c "from scripts.odoo_mcp_server import OdooMCPServer; odoo = OdooMCPServer(); print(odoo.test_connection())"
```

### Test Gmail:
```bash
python generate_gmail_credentials.py
```

### Test Facebook:
```bash
python -c "from scripts.facebook_mcp_server import FacebookMCPServer; fb = FacebookMCPServer(); print('Facebook MCP ready')"
```

### Test Twitter:
```bash
python -c "from twitter_watcher import TwitterPoster; poster = TwitterPoster(); print('Twitter ready')"
```

---

## Troubleshooting

### Issue: Odoo won't connect
**Solution:**
1. Check Docker is running: `docker-compose ps`
2. Verify credentials in `.env` match Odoo admin user
3. Check logs: `docker-compose logs odoo`

### Issue: Gmail authentication fails
**Solution:**
1. Delete `gmail_credentials.json` and regenerate
2. Ensure Gmail API is enabled in Google Cloud Console
3. Check redirect URI matches

### Issue: Social media automation fails
**Solution:**
1. Verify you can log in manually via browser
2. Check credentials in `.env` are correct
3. Try running with `PLAYWRIGHT_HEADLESS=false` for debugging

### Issue: Ralph loop not completing
**Solution:**
1. Increase `RALPH_MAX_ITERATIONS` (default: 10)
2. Increase `RALPH_MAX_DURATION_MINUTES` (default: 60)
3. Check task files are moving to `/Done` folder

---

## Environment Variables Reference

| Category | Variable | Required | Default | Description |
|----------|----------|----------|---------|-------------|
| **Odoo** | `ODOO_URL` | If using Odoo | `http://localhost:8069` | Odoo server URL |
| **Odoo** | `ODOO_DB` | If using Odoo | `odoo_db` | Database name |
| **Odoo** | `ODOO_USERNAME` | If using Odoo | `admin` | Odoo username |
| **Odoo** | `ODOO_PASSWORD` | If using Odoo | - | Odoo password |
| **Gmail** | `GMAIL_CLIENT_ID` | If using Gmail | - | OAuth client ID |
| **Gmail** | `GMAIL_CLIENT_SECRET` | If using Gmail | - | OAuth client secret |
| **LinkedIn** | `LINKEDIN_EMAIL` | If using LinkedIn | - | LinkedIn email |
| **LinkedIn** | `LINKEDIN_PASSWORD` | If using LinkedIn | - | LinkedIn password |
| **Facebook** | `FACEBOOK_PAGES` | If using Facebook | - | Comma-separated page names |
| **Twitter** | `TWITTER_USERNAME` | If using Twitter | - | Twitter username |
| **Twitter** | `TWITTER_PASSWORD` | If using Twitter | - | Twitter password |
| **System** | `VAULT_PATH` | Yes | `AI_Employee_Vault` | Obsidian vault path |
| **System** | `LOG_LEVEL` | No | `INFO` | Logging level |
| **Security** | `APPROVAL_TIMEOUT_SECONDS` | No | `3600` | Approval timeout |

---

## Next Steps

After configuring `.env`:

1. **Start Odoo (if using):**
   ```bash
   cd docker
   docker-compose up -d
   ```

2. **Generate Gmail credentials:**
   ```bash
   python generate_gmail_credentials.py
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   playwright install
   ```

4. **Run Gold Tier orchestrator:**
   ```bash
   python orchestrator_gold.py
   ```

---

## Support

For issues:
1. Check logs: `logs/ai_employee.log`
2. Review `GOLD_TIER_COMPLETE.md`
3. Test individual components
4. Verify `.env` configuration

---

**Remember:** Your `.env` file contains sensitive credentials. Keep it secure!
