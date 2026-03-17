"""
LinkedIn Poster - Playwright Automation

This script automates posting to LinkedIn using Playwright.
It follows the correct workflow:
1. Login to LinkedIn
2. Navigate to feed
3. Click "Start a post"
4. Fill content in the editor
5. Click "Post"

Environment Variables Required:
    LINKEDIN_EMAIL: Your LinkedIn email
    LINKEDIN_PASSWORD: Your LinkedIn password
"""

import os
from pathlib import Path
from datetime import datetime
import time
from playwright.sync_api import sync_playwright, Page, Browser, BrowserContext


VAULT_PATH = "AI_Employee_Vault"
PENDING_APPROVAL_PATH = Path(VAULT_PATH) / "Pending_Approval"
APPROVED_PATH = Path(VAULT_PATH) / "Approved"
DONE_PATH = Path(VAULT_PATH) / "Done"


def get_linkedin_credentials() -> tuple[str, str]:
    """Get LinkedIn credentials from environment variables."""
    email = os.getenv("LINKEDIN_EMAIL")
    password = os.getenv("LINKEDIN_PASSWORD")
    
    if not email or not password:
        raise ValueError(
            "LinkedIn credentials not found. Please set LINKEDIN_EMAIL and LINKEDIN_PASSWORD "
            "environment variables or add them to your .env file."
        )
    
    return email, password


def wait_for_element(page: Page, selector: str, timeout: int = 30000, description: str = "") -> None:
    """Wait for an element to be visible with helpful error messages."""
    desc = f" ({description})" if description else ""
    print(f"[DEBUG] Waiting for element: {selector}{desc}")
    try:
        page.wait_for_selector(selector, state="visible", timeout=timeout)
        print(f"[DEBUG] Element found: {selector}")
    except Exception as e:
        print(f"[ERROR] Timeout waiting for element: {selector}{desc}")
        raise e


def click_element(page: Page, selector: str, timeout: int = 10000, description: str = "") -> bool:
    """Click an element with fallback handling."""
    desc = f" ({description})" if description else ""
    print(f"[DEBUG] Clicking element: {selector}{desc}")
    try:
        page.click(selector, timeout=timeout)
        print(f"[DEBUG] Successfully clicked: {selector}")
        return True
    except Exception as e:
        print(f"[WARN] Failed to click {selector}: {e}")
        return False


def login_to_linkedin(page: Page, email: str, password: str) -> bool:
    """
    Login to LinkedIn.
    Returns True if login successful, False otherwise.
    """
    print("[INFO] Navigating to LinkedIn login page...")
    page.goto("https://www.linkedin.com/login", wait_until="networkidle", timeout=60000)
    
    # Check if already logged in by checking for feed navigation
    if "feed" in page.url:
        print("[INFO] Already logged in to LinkedIn")
        return True
    
    # Try to fill login form
    try:
        # Wait for login form
        wait_for_element(page, 'input[id="username"]', description="email field")
        
        print("[INFO] Entering credentials...")
        page.fill('input[id="username"]', email)
        page.fill('input[id="password"]', password)
        
        # Click sign in button
        # LinkedIn uses different selectors, try multiple
        signin_selectors = [
            'button[type="submit"]',
            'input[type="submit"]',
            'button:has-text("Sign in")',
            'button:has-text("Sign in")',
        ]
        
        signed_in = False
        for selector in signin_selectors:
            if click_element(page, selector, timeout=5000, description="sign in button"):
                signed_in = True
                break
        
        if not signed_in:
            print("[ERROR] Could not find sign in button")
            return False
        
        # Wait for navigation after login
        print("[INFO] Waiting for login to complete...")
        page.wait_for_url("https://www.linkedin.com/feed/*", timeout=30000)
        print("[INFO] Login successful!")
        return True
        
    except Exception as e:
        print(f"[ERROR] Login failed: {e}")
        # Take screenshot for debugging
        try:
            page.screenshot(path="linkedin_login_error.png")
            print("[DEBUG] Screenshot saved to linkedin_login_error.png")
        except:
            pass
        return False


def click_start_post(page: Page) -> bool:
    """
    Click the 'Start a post' button on the LinkedIn feed.
    Returns True if successful, False otherwise.
    """
    print("[INFO] Looking for 'Start a post' button...")
    
    # LinkedIn's "Start a post" button selectors (multiple fallbacks)
    start_post_selectors = [
        # Primary selector - the share box trigger
        'button:has-text("Start a post")',
        'button:has-text("start a post")',
        # Alternative - share box with avatar
        'div.share-box-feed-entry__trigger button',
        # Button with specific aria-label
        'button[aria-label="Start a post"]',
        # Generic share button
        'div[id="feed-share-box"] button',
        # Text-based selectors
        'button:has-text("Start")',
        'span:has-text("Start a post")',
    ]
    
    for selector in start_post_selectors:
        print(f"[DEBUG] Trying selector: {selector}")
        try:
            # Wait briefly for this selector
            page.wait_for_selector(selector, state="visible", timeout=5000)
            page.click(selector)
            print(f"[INFO] Clicked 'Start a post' using selector: {selector}")
            
            # Wait for post modal to appear
            try:
                wait_for_element(page, 'div[role="dialog"]', timeout=10000, description="post modal")
                print("[INFO] Post editor modal opened")
                return True
            except:
                # Modal might use different selector
                wait_for_element(page, 'div.editor-content', timeout=10000, description="editor content")
                print("[INFO] Post editor opened")
                return True
                
        except Exception as e:
            print(f"[DEBUG] Selector failed: {selector} - {e}")
            continue
    
    print("[ERROR] Could not find 'Start a post' button")
    return False


def fill_post_content(page: Page, content: str) -> bool:
    """
    Fill the post content in the LinkedIn editor.
    Uses div[role="textbox"] as the primary selector.
    Returns True if successful, False otherwise.
    """
    print("[INFO] Filling post content...")
    
    # LinkedIn post editor textbox selectors
    textbox_selectors = [
        # Primary selector - role="textbox"
        'div[role="textbox"]',
        # Alternative editor selectors
        'div.editor-content div[contenteditable="true"]',
        'div[contenteditable="true"]',
        # Specific LinkedIn editor
        'div.ql-editor[contenteditable="true"]',
        'div.artdeco-text-input__input[contenteditable="true"]',
    ]
    
    for selector in textbox_selectors:
        print(f"[DEBUG] Trying textbox selector: {selector}")
        try:
            # Wait for textbox
            page.wait_for_selector(selector, state="visible", timeout=5000)
            
            # Clear any existing content and fill new content
            textbox = page.locator(selector).first
            textbox.click()
            
            # Use keyboard to input text (more reliable than fill for contenteditable)
            textbox.press("Control+A")  # Select all (Windows)
            textbox.press("Delete")
            
            # Type the content
            textbox.type(content, delay=50)
            
            print(f"[INFO] Content filled using selector: {selector}")
            
            # Wait a moment for LinkedIn to process the input
            time.sleep(1)
            
            return True
            
        except Exception as e:
            print(f"[DEBUG] TextBox selector failed: {selector} - {e}")
            continue
    
    print("[ERROR] Could not find post editor textbox")
    return False


def click_post_button(page: Page) -> bool:
    """
    Click the 'Post' button to publish the content.
    Returns True if successful, False otherwise.
    """
    print("[INFO] Looking for 'Post' button...")
    
    # LinkedIn Post button selectors
    post_button_selectors = [
        # Primary - Post button in modal
        'button:has-text("Post")',
        'button:has-text("post")',
        # Button with specific aria-label
        'button[aria-label="Post"]',
        # Submit button in dialog
        'div[role="dialog"] button[type="submit"]',
        # LinkedIn specific classes
        'button.ember-view:has-text("Post")',
        # Disabled state check (LinkedIn enables when content is added)
        'button:not([disabled]):has-text("Post")',
    ]
    
    for selector in post_button_selectors:
        print(f"[DEBUG] Trying post button selector: {selector}")
        try:
            # Wait for post button to be enabled
            page.wait_for_selector(selector, state="visible", timeout=10000)
            
            # Additional wait for button to be enabled
            time.sleep(1)
            
            page.click(selector)
            print(f"[INFO] Clicked 'Post' button using selector: {selector}")
            
            # Wait for post to be published (URL change or modal close)
            try:
                page.wait_for_load_state("networkidle", timeout=15000)
                print("[INFO] Post published successfully!")
                return True
            except:
                print("[WARN] Post may have been published (timeout waiting for confirmation)")
                return True
                
        except Exception as e:
            print(f"[DEBUG] Post button selector failed: {selector} - {e}")
            continue
    
    print("[ERROR] Could not find 'Post' button")
    return False


def post_to_linkedin(post_content: str, headless: bool = False) -> bool:
    """
    Main function to post content to LinkedIn using Playwright.
    
    Args:
        post_content: The content to post
        headless: Run browser in headless mode (default: False for better LinkedIn compatibility)
    
    Returns:
        True if post successful, False otherwise
    """
    print("=" * 60)
    print("LINKEDIN POST AUTOMATION")
    print("=" * 60)
    print(f"[INFO] Post content length: {len(post_content)} characters")
    
    # Get credentials
    try:
        email, password = get_linkedin_credentials()
    except ValueError as e:
        print(f"[ERROR] {e}")
        return False
    
    print(f"[INFO] Logging in as: {email}")
    
    # Launch browser
    print("[INFO] Launching browser...")
    
    with sync_playwright() as p:
        # Use Chromium (most compatible with LinkedIn)
        browser: Browser = p.chromium.launch(
            headless=headless,
            args=[
                "--disable-blink-features=AutomationControlled",
                "--no-sandbox",
                "--disable-dev-shm-usage",
            ]
        )
        
        # Create context with realistic user agent
        context: BrowserContext = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            viewport={"width": 1920, "height": 1080},
        )
        
        page: Page = context.new_page()
        
        try:
            # Step 1: Login
            print("\n" + "=" * 40)
            print("STEP 1: LOGIN")
            print("=" * 40)
            if not login_to_linkedin(page, email, password):
                print("[ERROR] Login failed")
                return False
            
            # Small delay to ensure page is fully loaded
            time.sleep(2)
            
            # Step 2: Navigate to feed (if not already there)
            print("\n" + "=" * 40)
            print("STEP 2: NAVIGATE TO FEED")
            print("=" * 40)
            if "feed" not in page.url:
                page.goto("https://www.linkedin.com/feed/", wait_until="networkidle", timeout=60000)
                print("[INFO] Navigated to feed")
            else:
                print("[INFO] Already on feed page")
            
            # Wait for feed to fully load
            time.sleep(3)
            
            # Step 3: Click "Start a post"
            print("\n" + "=" * 40)
            print("STEP 3: CLICK 'START A POST'")
            print("=" * 40)
            if not click_start_post(page):
                print("[ERROR] Could not open post editor")
                return False
            
            # Wait for modal animation
            time.sleep(2)
            
            # Step 4: Fill post content
            print("\n" + "=" * 40)
            print("STEP 4: FILL POST CONTENT")
            print("=" * 40)
            if not fill_post_content(page, post_content):
                print("[ERROR] Could not fill post content")
                return False
            
            # Wait for content to register
            time.sleep(2)
            
            # Step 5: Click Post button
            print("\n" + "=" * 40)
            print("STEP 5: PUBLISH POST")
            print("=" * 40)
            if not click_post_button(page):
                print("[ERROR] Could not publish post")
                return False
            
            print("\n" + "=" * 60)
            print("SUCCESS: LinkedIn post published!")
            print("=" * 60)
            return True
            
        except Exception as e:
            print(f"\n[ERROR] Unexpected error: {e}")
            # Save screenshot for debugging
            try:
                page.screenshot(path="linkedin_error.png")
                print("[DEBUG] Screenshot saved to linkedin_error.png")
            except:
                pass
            return False
            
        finally:
            browser.close()
            print("[INFO] Browser closed")


# ============================================================================
# Approval Workflow Functions (for integration with vault system)
# ============================================================================

def create_linkedin_post_request(post_content: str) -> Path:
    """Create a pending approval request file for a LinkedIn post."""
    timestamp = datetime.now().isoformat().replace(':', '-')
    filename = f"LINKEDIN_POST_{timestamp}.md"
    filepath = PENDING_APPROVAL_PATH / filename
    
    # Ensure directories exist
    PENDING_APPROVAL_PATH.mkdir(parents=True, exist_ok=True)
    APPROVED_PATH.mkdir(parents=True, exist_ok=True)
    DONE_PATH.mkdir(parents=True, exist_ok=True)
    
    content = f'''---
type: social_media_post
action: linkedin_post
status: pending
created: {datetime.now().isoformat()}Z
---

# LinkedIn Post Request

## Content to Post
```
{post_content}
```

## To Approve
Move this file to {APPROVED_PATH} to proceed with the LinkedIn post.

## To Reject
Move this file to {DONE_PATH} (or delete) to cancel the LinkedIn post.
'''
    filepath.write_text(content)
    print(f"Created LinkedIn post approval request: {filepath}")
    return filepath


def check_for_approval(request_file_name: str, timeout: int = 300) -> Path | None:
    """
    Wait for approval of a LinkedIn post request.
    
    Args:
        request_file_name: Name of the request file to monitor
        timeout: Maximum time to wait in seconds (default: 5 minutes)
    
    Returns:
        Path to approved file if approved, None if rejected or timeout
    """
    start_time = time.time()
    while (time.time() - start_time) < timeout:
        approved_file_path = APPROVED_PATH / request_file_name
        if approved_file_path.exists():
            print(f"Approval detected for {request_file_name}. Posting to LinkedIn...")
            return approved_file_path

        rejected_file_path = DONE_PATH / request_file_name
        if rejected_file_path.exists():
            print(f"Rejection detected for {request_file_name}. Cancelling post.")
            return None

        time.sleep(5)  # Check every 5 seconds
    
    print(f"Timeout: No approval or rejection for {request_file_name}. Cancelling post.")
    return None


# ============================================================================
# Main Entry Point
# ============================================================================

if __name__ == "__main__":
    import sys
    
    # Check if running in direct mode (for testing)
    if len(sys.argv) > 1 and sys.argv[1] == "--direct":
        # Direct posting mode (bypasses approval workflow)
        print("\n[MODE] Direct posting mode (no approval workflow)")
        
        sample_post = """Excited to share our latest project update! 

We've been working on automating business processes using AI and Playwright. The results have been incredible:

✅ 80% reduction in manual tasks
✅ 24/7 autonomous operations
✅ Seamless integration across platforms

#AI #Automation #Playwright #BusinessAutomation #Innovation"""
        
        success = post_to_linkedin(sample_post, headless=False)
        sys.exit(0 if success else 1)
    
    # Default: Approval workflow mode
    print("\n[MODE] Approval workflow mode")
    
    # Example usage: Claude Code would call this script with the content
    sample_post = "Excited to share our latest project update! #AI #Automation #ClaudeCode"
    request_file_path = create_linkedin_post_request(sample_post)

    approved_path = check_for_approval(request_file_path.name)
    if approved_path:
        if post_to_linkedin(sample_post, headless=False):
            print("LinkedIn post successful!")
            # Move the approved file to Done after successful posting
            approved_path.rename(DONE_PATH / approved_path.name)
        else:
            print("LinkedIn post failed.")
            sys.exit(1)
    else:
        print("LinkedIn post not approved or timed out.")
        sys.exit(1)
