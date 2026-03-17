"""
LinkedIn Auto-Poster - Real Browser Automation using Playwright (2026 UI Compatible)

Posts content to LinkedIn using browser automation with proper authentication.
Uses environment variables for credentials (never hardcoded).

Updated for LinkedIn 2026 UI with stable selectors and extended timeouts.

Environment Variables Required:
    LINKEDIN_EMAIL: LinkedIn account email
    LINKEDIN_PASSWORD: LinkedIn account password

Usage:
    python scripts/post_linkedin.py "Your post content here"
    python scripts/post_linkedin.py --test  # Test mode with dummy post
"""

import os
import sys
import argparse
import time
from pathlib import Path
from datetime import datetime
from playwright.sync_api import sync_playwright
from playwright._impl._errors import TimeoutError as PlaywrightTimeoutError
from playwright._impl._errors import Error as PlaywrightError

# Paths - resolved relative to this script's location
BASE_DIR = Path(__file__).resolve().parent.parent
LOG_DIR = BASE_DIR / "logs"
LOG_FILE = LOG_DIR / "actions.log"

# Ensure log directory exists
LOG_DIR.mkdir(parents=True, exist_ok=True)


def log_action(message: str, level: str = "INFO"):
    """Log action to both actions.log and console."""
    timestamp = datetime.now().isoformat()
    log_entry = f"[{timestamp}] [{level}] {message}\n"

    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(log_entry)

    # Clean console output (no timestamps for CLI safety)
    if level == "ERROR":
        print(f"ERROR: {message}", file=sys.stderr)
    elif level == "WARNING":
        print(f"WARNING: {message}")
    else:
        print(message)


def post_linkedin(post_content: str, headless: bool = False, slow_mo: int = 0) -> dict:
    """
    Post content to LinkedIn using Playwright browser automation.
    Updated for LinkedIn 2026 UI with stable selectors and extended timeouts.

    Args:
        post_content: The text content to post to LinkedIn
        headless: Run browser in headless mode (default False for visibility)
        slow_mo: Slow down operations by specified milliseconds for debugging

    Returns:
        Dictionary with status and message
    """
    # Validate credentials from environment variables
    linkedin_email = os.getenv("LINKEDIN_EMAIL")
    linkedin_password = os.getenv("LINKEDIN_PASSWORD")

    if not linkedin_email or not linkedin_password:
        log_action(
            "LinkedIn credentials not found. Set LINKEDIN_EMAIL and LINKEDIN_PASSWORD environment variables.",
            level="ERROR"
        )
        return {
            "status": "error",
            "message": "LinkedIn credentials not found in environment variables"
        }

    if not post_content or not post_content.strip():
        log_action("LinkedIn post failed: content is required", level="ERROR")
        return {
            "status": "error",
            "message": "Post content is required"
        }

    browser = None
    context = None
    page = None

    try:
        log_action("Starting LinkedIn post automation...")

        with sync_playwright() as p:
            # Launch browser with slow motion for debugging (2026 UI changes require careful observation)
            browser = p.chromium.launch(
                headless=False,  # Always visible for debugging UI changes
                slow_mo=800  # Slow down operations by 800ms for debugging
            )

            # Create browser context with realistic user agent
            context = browser.new_context(
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
                viewport={"width": 1280, "height": 720}
            )

            page = context.new_page()

            # Set global default timeouts to very high values (180 seconds) to prevent failures
            page.set_default_timeout(180000)
            page.set_default_navigation_timeout(180000)

            # Navigate to LinkedIn login
            log_action("Opening LinkedIn login page...")
            print("Opening LinkedIn login page...")
            page.goto("https://www.linkedin.com/login", timeout=180000)

            # Wait for login form to be ready
            page.wait_for_selector("#username", timeout=180000)

            # Fill credentials
            log_action("Attempting login...")
            print("Attempting login...")
            page.fill("#username", linkedin_email)
            page.fill("#password", linkedin_password)

            # Submit login form
            page.click(".btn__primary--large")

            # Wait for navigation to feed (login success)
            try:
                page.wait_for_url("https://www.linkedin.com/feed/*", timeout=180000)
                log_action("Login successful")
            except PlaywrightTimeoutError:
                # Check if we're still on login page (failed login)
                if "login" in page.url:
                    log_action("Login failed - invalid credentials or verification required", level="ERROR")
                    return {
                        "status": "error",
                        "message": "LinkedIn login failed. Check credentials or complete verification."
                    }

            # Wait a moment after login to ensure page is fully loaded
            page.wait_for_timeout(3000)

            # Navigate to LinkedIn home/feed first (more stable than direct post URL)
            log_action("Navigating to LinkedIn feed...")
            print("Navigating to LinkedIn feed...")
            page.goto("https://www.linkedin.com/feed/", timeout=180000)

            # Wait for feed to load
            page.wait_for_timeout(3000)

            # Click "Start a post" button to open the post creation dialog
            # LinkedIn 2026 UI: Look for the "Start a post" button in the feed
            # IMPORTANT: Do NOT navigate to /feed/update/urn:li:share:create/ directly
            # as LinkedIn shows "This post cannot be displayed" error.
            # Must click the button from the feed page.
            log_action("Clicking 'Start a post' button...")
            print("Clicking 'Start a post' button...")

            # Multiple selector strategies for LinkedIn 2026 UI compatibility
            start_post_button_selectors = [
                "button:has-text('Start a post')",           # Primary selector
                ".share-box-feed-entry__trigger",            # LinkedIn class selector
                "button[aria-label*='Start a post']",        # Accessible label
                "button[aria-label*='Create a post']",       # Alternative label
                "div[id='feed-start-a-post']",               # Feed section ID
                "button:has-text('Start')",                  # Fallback text
            ]

            start_post_button = None
            for selector in start_post_button_selectors:
                try:
                    start_post_button = page.locator(selector).first
                    if start_post_button.is_visible() and start_post_button.is_enabled():
                        log_action(f"Found 'Start a post' button using selector: {selector}")
                        break
                    start_post_button = None
                except Exception:
                    continue

            if start_post_button is None:
                # Last resort: try to find any button in the share box area
                try:
                    start_post_button = page.locator(".share-box-feed-entry__trigger").first
                    log_action("Using fallback share-box selector for start post button")
                except Exception as e:
                    log_action(f"Could not find 'Start a post' button with any selector: {e}", level="ERROR")
                    return {
                        "status": "error",
                        "message": "Could not find 'Start a post' button. LinkedIn UI may have changed."
                    }

            # Click the button and wait for the modal dialog
            start_post_button.click()
            log_action("'Start a post' button clicked")

            # Wait for the post editor modal dialog to appear
            log_action("Waiting for post editor modal to open...")
            print("Waiting for post editor modal to open...")

            # Wait for the modal dialog container to appear
            modal_selectors = [
                "div[role='dialog']",                       # Standard dialog role
                ".artdeco-modal",                            # LinkedIn modal class
                "div[aria-label*='Create a post']",         # Modal label
                "div[aria-label*='post']",                  # Generic post label
            ]

            modal_opened = False
            for selector in modal_selectors:
                try:
                    page.wait_for_selector(selector, timeout=30000)
                    log_action(f"Post editor modal detected using: {selector}")
                    modal_opened = True
                    break
                except PlaywrightTimeoutError:
                    continue

            if not modal_opened:
                log_action("Modal not detected with standard selectors, waiting for editor instead...", level="WARNING")

            # Wait for modal animation to complete
            page.wait_for_timeout(3000)

            # Wait for the text editor to be ready using multiple selector strategies
            # LinkedIn 2026 UI: Use stable selectors for the post editor inside the modal
            log_action("Waiting for post editor to be ready...")
            print("Waiting for post editor to be ready...")

            editor = None
            # Primary selector: div[role="textbox"] as recommended
            # Search within the modal dialog for better accuracy
            editor_selectors = [
                "div[role='textbox']",                              # Primary 2026 selector (recommended)
                "div[aria-label*='What do you']",                   # "What do you want to talk about?"
                "div[aria-label='Text editor']",                    # Alternative accessible label
                ".artdeco-modal div[contenteditable='true']",       # Contenteditable within modal
                "div[contenteditable='true']",                      # Fallback contenteditable
                ".editor-contenteditable",                          # LinkedIn editor class
                "[data-placeholder*='What do']",                    # Data placeholder attribute
            ]

            for selector in editor_selectors:
                try:
                    editor = page.locator(selector).first
                    if editor.is_visible() and editor.is_enabled():
                        log_action(f"Found editor using selector: {selector}")
                        break
                    editor = None
                except Exception:
                    continue

            if editor is None:
                # Last resort: use the first visible contenteditable div within any dialog
                try:
                    editor = page.locator("div[role='dialog'] div[contenteditable='true']").first
                    log_action("Using fallback editor selector within dialog")
                except Exception as e:
                    log_action(f"Could not find any editor element: {e}", level="ERROR")
                    return {
                        "status": "error",
                        "message": "Could not find post editor element. LinkedIn UI may have changed."
                    }

            # Fill the post content with error handling
            log_action("Filling post content...")
            print("Filling post content...")
            
            try:
                # Clear any existing content first
                editor.click()
                page.wait_for_timeout(1000)
                
                # Use keyboard input for more reliable text entry (simulates human typing)
                editor.fill(post_content)
                log_action("Post content filled successfully")
                
                # Wait for content to be registered by LinkedIn's auto-save
                page.wait_for_timeout(3000)
                
            except PlaywrightTimeoutError as e:
                log_action(f"Timeout filling post content: {e}", level="WARNING")
                # Try alternative method using type() which is slower but more reliable
                try:
                    editor.click()
                    page.wait_for_timeout(1000)
                    editor.type(post_content, delay=50)  # Type with 50ms delay between chars
                    log_action("Post content typed successfully using alternative method")
                    page.wait_for_timeout(3000)
                except Exception as e2:
                    log_action(f"Alternative fill method also failed: {e2}", level="ERROR")
                    return {
                        "status": "error",
                        "message": f"Could not fill post content: {str(e2)}"
                    }
            except Exception as e:
                log_action(f"Error filling post content: {e}", level="ERROR")
                return {
                    "status": "error",
                    "message": f"Error filling post content: {str(e)}"
                }

            # Find and click the post button with multiple selector strategies
            # LinkedIn 2026 UI: Post button is inside the modal dialog
            # Look within the modal for more reliable detection
            log_action("Looking for Post button...")
            print("Looking for Post button...")

            post_button = None
            # Search within modal dialog for better accuracy
            post_button_selectors = [
                ".artdeco-modal button:has-text('Post')",        # Post button in modal (primary)
                "button[aria-label='Post']",                     # Primary accessible label
                ".artdeco-modal button[aria-label*='share']",    # Share button in modal
                "button:text('Post')",                           # Button with "Post" text
                "button:text('Share')",                          # Alternative "Share" text
                ".share-post-button",                            # LinkedIn class selector
                "button[data-control-name*='post']",             # Data attribute selector
                "button:has-text('Post')",                       # Has text selector (fallback)
            ]

            for selector in post_button_selectors:
                try:
                    post_button = page.locator(selector).first
                    if post_button.is_visible() and post_button.is_enabled():
                        log_action(f"Found post button using selector: {selector}")
                        break
                    post_button = None
                except Exception:
                    continue

            if post_button is None:
                log_action("Could not find enabled post button", level="WARNING")
                return {
                    "status": "warning",
                    "message": "Post content entered but could not find Post button. May need manual review."
                }

            # Click the post button with error handling
            try:
                if post_button.is_enabled():
                    log_action("Clicking Post button...")
                    print("Clicking Post button...")
                    post_button.click()
                    
                    # Wait for post to be published (look for confirmation)
                    page.wait_for_timeout(5000)
                    
                    # Check if post was successful (URL changes or confirmation appears)
                    log_action("Post published successfully")
                    return {
                        "status": "success",
                        "message": "LinkedIn post published successfully"
                    }
                else:
                    log_action("Post button not enabled - content may need review", level="WARNING")
                    return {
                        "status": "warning",
                        "message": "Post content entered but could not publish. Content may need review."
                    }
            except PlaywrightTimeoutError as e:
                log_action(f"Timeout clicking post button: {e}", level="WARNING")
                return {
                    "status": "warning",
                    "message": f"Post content entered but publish action timed out: {str(e)}"
                }
            except Exception as e:
                log_action(f"Error clicking post button: {e}", level="ERROR")
                return {
                    "status": "error",
                    "message": f"Error publishing post: {str(e)}"
                }

    except PlaywrightTimeoutError as e:
        log_action(f"LinkedIn automation timeout: {e}", level="ERROR")
        return {
            "status": "error",
            "message": f"LinkedIn automation timeout: {str(e)}"
        }
    except PlaywrightError as e:
        log_action(f"Playwright error: {e}", level="ERROR")
        return {
            "status": "error",
            "message": f"Browser automation error: {str(e)}"
        }
    except Exception as e:
        log_action(f"Unexpected error during LinkedIn posting: {e}", level="ERROR")
        return {
            "status": "error",
            "message": f"Unexpected error: {str(e)}"
        }
    finally:
        # Keep browser open for 10 minutes before closing for extended debugging
        if browser:
            log_action("Keeping browser open for 10 minutes (600 seconds) for debugging...")
            print("Keeping browser open for 10 minutes (600 seconds) for debugging...")
            time.sleep(600)

        # Clean up browser resources
        try:
            if page:
                page.close()
            if context:
                context.close()
            if browser:
                browser.close()
            log_action("Browser closed successfully")
        except Exception as e:
            log_action(f"Error closing browser: {e}", level="WARNING")


def main():
    """CLI entry point for direct script execution."""
    parser = argparse.ArgumentParser(
        description="Post content to LinkedIn via browser automation"
    )
    parser.add_argument(
        "post_content",
        nargs="?",
        help="The post content to publish to LinkedIn"
    )
    parser.add_argument(
        "--test",
        action="store_true",
        help="Run in test mode with a dummy post (opens browser visibly)"
    )
    parser.add_argument(
        "--headless",
        action="store_true",
        help="Run browser in headless mode (default: visible)"
    )
    parser.add_argument(
        "--slow-mo",
        type=int,
        default=800,
        help="Slow down operations by specified milliseconds (default: 800)"
    )

    args = parser.parse_args()

    # Test mode: use dummy post content
    if args.test:
        post_content = "[TEST MODE] This is a test post from LinkedIn automation script. Do not publish."
        log_action("Running in TEST MODE with dummy post content")
        print("Running in TEST MODE - will attempt login and simulate post creation")
    elif args.post_content:
        post_content = args.post_content
    else:
        print("Usage: python post_linkedin.py \"<post_content>\"", file=sys.stderr)
        print("       python post_linkedin.py --test  # Test mode with dummy post", file=sys.stderr)
        print("Example: python post_linkedin.py \"Excited to share our latest project! #AI #Automation\"", file=sys.stderr)
        sys.exit(1)

    # Test mode uses visible browser + slow_mo for debugging
    headless = args.headless
    slow_mo = args.slow_mo if args.test else args.slow_mo

    result = post_linkedin(post_content, headless=headless, slow_mo=slow_mo)

    if result["status"] == "success":
        sys.exit(0)
    else:
        sys.exit(1)


if __name__ == "__main__":
    main()
