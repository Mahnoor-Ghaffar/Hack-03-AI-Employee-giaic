# Business MCP Server

Production-ready Model Context Protocol (MCP) server for external business actions.

## Overview

This MCP server provides Claude Code with tools to perform common business actions:

| Tool | Description | Use Case |
|------|-------------|----------|
| `send_email` | Send emails via Gmail API | Client communication, responses, notifications |
| `post_linkedin` | Create LinkedIn posts | Professional updates, announcements |
| `log_activity` | Log business activities | Audit trail, tracking, compliance |

## Features

✅ **Production-Ready**
- Comprehensive error handling
- Detailed logging
- Input validation
- Type hints

✅ **Integration**
- Gmail API for email sending
- Playwright for LinkedIn automation
- Vault logging for audit trail

✅ **Security**
- Environment-based configuration
- Credential management
- Activity logging

## Installation

### 1. Install Dependencies

```bash
# Navigate to project root
cd E:\New folder\GIAIC-Q4\sub-hack03\Hack-03-AI-Employee-giaic

# Install MCP SDK
pip install mcp

# Install additional dependencies
pip install google-auth google-auth-oauthlib google-auth-httplib2 google-api-python-client
pip install playwright
playwright install
```

### 2. Configure Environment

Create or update your `.env` file:

```env
# Business MCP Server Configuration
VAULT_PATH=AI_Employee_Vault
GMAIL_CREDENTIALS_FILE=gmail_credentials.json
LINKEDIN_EMAIL=your-linkedin-email@example.com
LINKEDIN_PASSWORD=YourLinkedInPassword
LOG_LEVEL=INFO
```

### 3. Setup Gmail Credentials

```bash
python generate_gmail_credentials.py
```

Follow the OAuth flow to authenticate Gmail.

## Configuration

### Environment Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `VAULT_PATH` | No | `AI_Employee_Vault` | Path to Obsidian vault |
| `GMAIL_CREDENTIALS_FILE` | No | `gmail_credentials.json` | Gmail OAuth credentials |
| `LINKEDIN_EMAIL` | Yes* | - | LinkedIn email for automation |
| `LINKEDIN_PASSWORD` | Yes* | - | LinkedIn password for automation |
| `LOG_LEVEL` | No | `INFO` | Logging level (DEBUG, INFO, WARNING, ERROR) |

*Required for LinkedIn posting

## Usage

### Standalone Mode

```bash
# Run the MCP server
python mcp/business_mcp/server.py
```

### Claude Code Integration

Add to your MCP configuration:

**Option 1: Project-level (`.claude/mcp.json`)**
```json
{
  "mcpServers": {
    "business": {
      "command": "python",
      "args": ["mcp/business_mcp/server.py"],
      "cwd": "E:\\New folder\\GIAIC-Q4\\sub-hack03\\Hack-03-AI-Employee-giaic",
      "env": {
        "VAULT_PATH": "AI_Employee_Vault",
        "GMAIL_CREDENTIALS_FILE": "gmail_credentials.json",
        "LINKEDIN_EMAIL": "your-email@example.com",
        "LINKEDIN_PASSWORD": "your-password"
      }
    }
  }
}
```

**Option 2: Global (`~/.config/claude-code/mcp.json`)**
```json
{
  "mcpServers": {
    "business": {
      "command": "python",
      "args": ["mcp/business_mcp/server.py"],
      "cwd": "E:\\New folder\\GIAIC-Q4\\sub-hack03\\Hack-03-AI-Employee-giaic",
      "env": {
        "VAULT_PATH": "AI_Employee_Vault",
        "GMAIL_CREDENTIALS_FILE": "gmail_credentials.json"
      }
    }
  }
}
```

### Using Tools in Claude Code

Once configured, use the tools in Claude Code conversations:

**Send Email:**
```
Use the send_email tool to notify the client about the project update.
To: client@example.com
Subject: Project Update - Week 12
Body: Dear Client, I'm pleased to inform you...
```

**Post to LinkedIn:**
```
Create a LinkedIn post announcing our new AI Employee feature.
Content: Excited to announce our new Gold Tier AI Employee...
```

**Log Activity:**
```
Log this business activity: Completed quarterly review meeting with stakeholders.
Category: meeting
Metadata: {"attendees": ["John", "Sarah"], "duration": "60min"}
```

## Tool Specifications

### send_email

Send an email via Gmail API.

**Parameters:**
- `to` (required): Recipient email address
- `subject` (required): Email subject line
- `body` (required): Email body content
- `cc` (optional): CC recipients (comma-separated)
- `bcc` (optional): BCC recipients (comma-separated)

**Example Response:**
```json
{
  "status": "success",
  "message": "Email sent successfully to client@example.com",
  "subject": "Project Update",
  "timestamp": "2026-03-14T10:30:00",
  "details": {
    "message_id": "<abc123@mail.gmail.com>"
  }
}
```

### post_linkedin

Create a post on LinkedIn.

**Parameters:**
- `content` (required): Post content (max 3000 characters)
- `visibility` (optional): Post visibility (`anyone`, `connections`, `group`)

**Example Response:**
```json
{
  "status": "success",
  "message": "LinkedIn post published successfully",
  "content_preview": "Excited to announce our new AI Employee...",
  "character_count": 250,
  "visibility": "anyone",
  "timestamp": "2026-03-14T10:30:00"
}
```

### log_activity

Log a business activity to the vault.

**Parameters:**
- `message` (required): Activity message
- `category` (optional): Category (`email`, `social`, `meeting`, `task`, `call`, `other`)
- `metadata` (optional): Additional metadata as JSON object

**Example Response:**
```json
{
  "status": "success",
  "message": "Activity logged successfully",
  "log_file": "AI_Employee_Vault/Logs/business.log",
  "entry": {
    "timestamp": "2026-03-14T10:30:00",
    "category": "meeting",
    "message": "Completed quarterly review",
    "metadata": {}
  }
}
```

## Log File Format

Business activities are logged to `AI_Employee_Vault/Logs/business.log`:

```
[2026-03-14T10:30:00] [EMAIL] Email sent to client@example.com: Project Update
[2026-03-14T10:35:00] [SOCIAL] LinkedIn post published: Excited to announce...
[2026-03-14T10:40:00] [MEETING] Completed quarterly review meeting with stakeholders
```

## Error Handling

The server handles various error conditions:

| Error | Cause | Resolution |
|-------|-------|------------|
| `Gmail credentials not found` | Missing `gmail_credentials.json` | Run `python generate_gmail_credentials.py` |
| `LinkedIn credentials not configured` | Missing LINKEDIN_EMAIL/PASSWORD | Add to `.env` file |
| `Content exceeds LinkedIn limit` | Content > 3000 characters | Shorten content |
| `Missing required fields` | Incomplete tool arguments | Provide all required parameters |

## Testing

### Test Email Sending

```bash
python -c "
from mcp.business_mcp.server import BusinessMCPServer
import asyncio

async def test():
    server = BusinessMCPServer()
    result = await server._send_email({
        'to': 'test@example.com',
        'subject': 'Test Email',
        'body': 'This is a test'
    })
    print(result)

asyncio.run(test())
"
```

### Test LinkedIn Posting

```bash
python -c "
from mcp.business_mcp.server import BusinessMCPServer
import asyncio

async def test():
    server = BusinessMCPServer()
    result = await server._post_linkedin({
        'content': 'Test post from MCP server',
        'visibility': 'anyone'
    })
    print(result)

asyncio.run(test())
"
```

### Test Activity Logging

```bash
python -c "
from mcp.business_mcp.server import BusinessMCPServer
import asyncio

async def test():
    server = BusinessMCPServer()
    result = await server._log_activity({
        'message': 'Test activity log',
        'category': 'task'
    })
    print(result)

asyncio.run(test())
"
```

## Troubleshooting

### Issue: MCP server not starting

**Check logs:**
```bash
python mcp/business_mcp/server.py 2>&1 | head -50
```

**Verify Python path:**
```bash
which python  # Linux/Mac
where python  # Windows
```

### Issue: Gmail authentication fails

**Solution:**
1. Delete existing credentials: `rm gmail_credentials.json`
2. Regenerate: `python generate_gmail_credentials.py`
3. Ensure Gmail API is enabled in Google Cloud Console

### Issue: LinkedIn posting fails

**Solution:**
1. Verify credentials in `.env`
2. Try manual login at linkedin.com
3. Run with `PLAYWRIGHT_HEADLESS=false` for debugging
4. Ensure Playwright browsers installed: `playwright install`

### Issue: Activities not logging

**Solution:**
1. Check vault path exists
2. Verify write permissions: `ls -la AI_Employee_Vault/Logs/`
3. Check disk space

## Security Best Practices

✅ **DO:**
- Store credentials in `.env` file (already in `.gitignore`)
- Use strong, unique passwords
- Rotate credentials regularly
- Review business.log for audit trail
- Use environment-specific configurations

❌ **DON'T:**
- Never commit `.env` to version control
- Never hardcode credentials in code
- Don't share credential files
- Don't disable logging in production

## Architecture

```
┌─────────────────┐
│   Claude Code   │
│   (AI Agent)    │
└────────┬────────┘
         │ MCP Protocol
         │ (stdio)
         ▼
┌─────────────────────────────────────┐
│     Business MCP Server             │
│  ┌───────────────────────────────┐  │
│  │  send_email Tool              │  │
│  │  - Gmail API                  │  │
│  │  - OAuth 2.0                  │  │
│  └───────────────────────────────┘  │
│  ┌───────────────────────────────┐  │
│  │  post_linkedin Tool           │  │
│  │  - Playwright                 │  │
│  │  - Browser Automation         │  │
│  └───────────────────────────────┘  │
│  ┌───────────────────────────────┐  │
│  │  log_activity Tool            │  │
│  │  - File I/O                   │  │
│  │  - JSON Logging               │  │
│  └───────────────────────────────┘  │
└─────────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────┐
│  External Services                  │
│  - Gmail API                        │
│  - LinkedIn (Browser)               │
│  - Vault/Logs/business.log          │
└─────────────────────────────────────┘
```

## Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.0.0 | 2026-03-14 | Initial release |

## License

MIT License - See project LICENSE file for details.

## Support

For issues:
1. Check server logs: `logs/ai_employee.log`
2. Review business log: `AI_Employee_Vault/Logs/business.log`
3. Verify environment configuration
4. Test individual tools

---

**Business MCP Server** - Part of the Gold Tier AI Employee Project
