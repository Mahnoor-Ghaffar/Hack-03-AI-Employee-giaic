# gmail-send Skill

**Purpose:** Send real emails using SMTP.

**Usage:**
This skill sends emails to specified recipients.

**Arguments:**
*   `to`: The recipient's email address.
*   `subject`: The subject of the email.
*   `body`: The content of the email.

**Environment Variables:**
*   `EMAIL_ADDRESS`: The sender's email address.
*   `EMAIL_PASSWORD`: The sender's email password or app-specific password.

**Example Invocation:**
```bash
python scripts/send_email.py "recipient@example.com" "Hello" "This is the email body."
```
