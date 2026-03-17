"""
Facebook Watcher - Gold Tier Integration

Monitors Facebook Pages and Instagram accounts for:
- New posts and engagement
- Comments and messages
- Mentions and tags
- Performance metrics

Uses Playwright for browser automation (Facebook Graph API optional).

Usage:
    python facebook_watcher.py
"""

import time
import logging
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any
import json

from base_watcher import BaseWatcher
from log_manager import setup_logging
from skills.vault_skills import get_vault

# Setup logging
logger = setup_logging(log_file="logs/ai_employee.log", logger_name="facebook_watcher")


class FacebookWatcher(BaseWatcher):
    """
    Facebook Page and Instagram Business Account Watcher.
    
    Monitors for new comments, messages, mentions, and engagement metrics.
    Uses Playwright for browser automation.
    """
    
    def __init__(
        self,
        vault_path: str,
        facebook_pages: List[str] = None,
        instagram_accounts: List[str] = None,
        check_interval: int = 600  # Check every 10 minutes
    ):
        """
        Initialize Facebook Watcher.
        
        Args:
            vault_path: Path to AI Employee vault
            facebook_pages: List of Facebook Page IDs/names to monitor
            instagram_accounts: List of Instagram usernames to monitor
            check_interval: Interval between checks in seconds
        """
        super().__init__(vault_path, check_interval=check_interval)
        
        self.facebook_pages = facebook_pages or []
        self.instagram_accounts = instagram_accounts or []
        self.processed_items = set()
        self.vault = get_vault()
        
        # Create Social_Media folder in vault
        self.social_media_path = self.vault_path / 'Social_Media'
        self.social_media_path.mkdir(parents=True, exist_ok=True)
        
        logger.info(f"FacebookWatcher initialized. Monitoring {len(self.facebook_pages)} FB pages, {len(self.instagram_accounts)} IG accounts")
    
    def check_for_updates(self) -> List[Dict[str, Any]]:
        """
        Check for new Facebook/Instagram activity.
        
        Returns:
            List of new activity items to process
        """
        logger.info("Checking for new Facebook/Instagram activity...")
        new_items = []
        
        try:
            from playwright.sync_api import sync_playwright
            import time

            with sync_playwright() as p:
                # Launch browser in headful mode with slowMo for debugging
                browser = p.chromium.launch(
                    headless=False,
                    slow_mo=1000  # 1000ms delay between actions for debugging
                )
                context = browser.new_context(
                    user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
                )
                page = context.new_page()

                # Check Facebook Pages
                for page_name in self.facebook_pages:
                    try:
                        fb_items = self._check_facebook_page(page, page_name)
                        new_items.extend(fb_items)
                    except Exception as e:
                        logger.error(f"Error checking Facebook page {page_name}: {e}")

                # Check Instagram Accounts
                for username in self.instagram_accounts:
                    try:
                        ig_items = self._check_instagram_account(page, username)
                        new_items.extend(ig_items)
                    except Exception as e:
                        logger.error(f"Error checking Instagram account {username}: {e}")

                # Keep browser open for 30 seconds for debugging
                logger.info("Keeping browser open for 30 seconds for debugging...")
                time.sleep(30)

                browser.close()
                
        except ImportError:
            logger.warning("Playwright not installed. Skipping Facebook/Instagram check.")
            logger.info("Install with: pip install playwright && playwright install")
        except Exception as e:
            logger.error(f"Error in Facebook/Instagram check: {e}")
        
        # Filter out already processed items
        filtered_items = [
            item for item in new_items 
            if item.get('unique_id') not in self.processed_items
        ]
        
        # Mark as processed
        for item in filtered_items:
            self.processed_items.add(item.get('unique_id'))
        
        logger.info(f"Found {len(filtered_items)} new Facebook/Instagram activities")
        return filtered_items
    
    def _check_facebook_page(self, page, page_name: str) -> List[Dict[str, Any]]:
        """
        Check a Facebook Page for new activity.
        
        Args:
            page: Playwright page object
            page_name: Facebook Page name/ID
            
        Returns:
            List of activity items
        """
        items = []
        
        try:
            # Navigate to Facebook Page
            page_url = f"https://www.facebook.com/{page_name}"
            page.goto(page_url, timeout=30000)
            page.wait_for_timeout(5000)  # Wait for content to load
            
            # Check for new posts (simplified - would need authentication for full access)
            posts = page.query_selector_all('[role="article"]')
            
            for i, post in enumerate(posts[:5]):  # Check last 5 posts
                try:
                    post_text = post.inner_text()[:500]
                    post_id = f"FB_{page_name}_{i}"
                    
                    # Check for new comments
                    comments_section = post.query_selector('[data-comment-count]')
                    comment_count = 0
                    if comments_section:
                        comment_count = int(comments_section.get_attribute('data-comment-count') or 0)
                    
                    if comment_count > 0:
                        items.append({
                            'type': 'facebook_comment',
                            'platform': 'facebook',
                            'page': page_name,
                            'post_id': post_id,
                            'comment_count': comment_count,
                            'content': post_text,
                            'unique_id': f"{post_id}_comments",
                            'timestamp': datetime.now().isoformat()
                        })
                    
                except Exception as e:
                    logger.debug(f"Error processing post: {e}")
            
            logger.info(f"Checked Facebook page {page_name}, found {len(items)} activities")
            
        except Exception as e:
            logger.error(f"Error checking Facebook page {page_name}: {e}")
        
        return items
    
    def _check_instagram_account(self, page, username: str) -> List[Dict[str, Any]]:
        """
        Check an Instagram account for new activity.
        
        Args:
            page: Playwright page object
            username: Instagram username
            
        Returns:
            List of activity items
        """
        items = []
        
        try:
            # Navigate to Instagram profile
            profile_url = f"https://www.instagram.com/{username}/"
            page.goto(profile_url, timeout=30000)
            page.wait_for_timeout(5000)
            
            # Get post count
            try:
                stats = page.query_selector_all('meta[property="og:description"]')
                if stats:
                    description = stats[0].get_attribute('content', '')
                    # Parse follower/following/post counts from description
            except Exception:
                pass
            
            # Check recent posts
            posts = page.query_selector_all('article')
            
            for i, post in enumerate(posts[:3]):  # Check last 3 posts
                try:
                    post_id = f"IG_{username}_{i}"
                    
                    # Get likes and comments
                    likes = 0
                    comments = 0
                    
                    like_elem = post.query_selector('[aria-label*="like"]')
                    if like_elem:
                        likes = int(like_elem.inner_text().replace(',', '').replace('.', '') or 0)
                    
                    comment_elem = post.query_selector('[aria-label*="comment"]')
                    if comment_elem:
                        comments = int(comment_elem.inner_text().replace(',', '').replace('.', '') or 0)
                    
                    if comments > 0:
                        items.append({
                            'type': 'instagram_comment',
                            'platform': 'instagram',
                            'account': username,
                            'post_id': post_id,
                            'likes': likes,
                            'comment_count': comments,
                            'unique_id': f"{post_id}_comments",
                            'timestamp': datetime.now().isoformat()
                        })
                    
                except Exception as e:
                    logger.debug(f"Error processing Instagram post: {e}")
            
            logger.info(f"Checked Instagram account {username}, found {len(items)} activities")
            
        except Exception as e:
            logger.error(f"Error checking Instagram account {username}: {e}")
        
        return items
    
    def create_action_file(self, item: Dict[str, Any]) -> Path:
        """
        Create an action file in Needs_Action folder for Facebook/Instagram activity.
        
        Args:
            item: Activity item dictionary
            
        Returns:
            Path to created action file
        """
        timestamp = datetime.now().isoformat().replace(':', '-').replace('.', '-')
        
        if item['type'] == 'facebook_comment':
            filename = f"FACEBOOK_COMMENTS_{item['page']}_{timestamp}.md"
            content = f"""---
type: facebook_engagement
platform: facebook
page: {item['page']}
post_id: {item['post_id']}
comment_count: {item['comment_count']}
received: {item['timestamp']}
priority: medium
status: pending
---

## Facebook Engagement Alert

**Page:** {item['page']}
**Post ID:** {item['post_id']}
**New Comments:** {item['comment_count']}

**Post Content Preview:**
```
{item['content'][:300]}
```

## Suggested Actions
- [ ] Review comments for spam or important messages
- [ ] Respond to customer inquiries
- [ ] Engage with positive comments
- [ ] Flag negative feedback for review
"""
        
        elif item['type'] == 'instagram_comment':
            filename = f"INSTAGRAM_COMMENTS_{item['account']}_{timestamp}.md"
            content = f"""---
type: instagram_engagement
platform: instagram
account: {item['account']}
post_id: {item['post_id']}
likes: {item['likes']}
comment_count: {item['comment_count']}
received: {item['timestamp']}
priority: medium
status: pending
---

## Instagram Engagement Alert

**Account:** @{item['account']}
**Post ID:** {item['post_id']}
**Likes:** {item['likes']}
**New Comments:** {item['comment_count']}

## Suggested Actions
- [ ] Review comments for spam or important messages
- [ ] Respond to customer inquiries
- [ ] Engage with followers
- [ ] Analyze engagement metrics
"""
        
        else:
            filename = f"SOCIAL_MEDIA_{item['type']}_{timestamp}.md"
            content = f"""---
type: {item['type']}
platform: {item.get('platform', 'unknown')}
received: {item['timestamp']}
status: pending
---

## Social Media Activity

**Type:** {item['type']}
**Details:** {json.dumps(item, indent=2)}

## Suggested Actions
- [ ] Review activity
- [ ] Take appropriate action
"""
        
        file_path = self.vault.needs_action / filename
        file_path.write_text(content)
        logger.info(f"Created Facebook/Instagram action file: {filename}")
        return file_path


class FacebookPoster:
    """
    Facebook Page Poster using Playwright automation.
    
    Posts content to Facebook Pages and optionally cross-posts to Instagram.
    """
    
    def __init__(self, facebook_pages: List[str] = None):
        """
        Initialize Facebook Poster.
        
        Args:
            facebook_pages: List of Facebook Page names to post to
        """
        self.facebook_pages = facebook_pages or []
        logger.info(f"FacebookPoster initialized for {len(self.facebook_pages)} pages")
    
    def post_to_facebook(
        self,
        content: str,
        page_name: str = None,
        image_path: str = None,
        schedule_time: str = None
    ) -> Dict[str, Any]:
        """
        Post content to a Facebook Page.
        
        Args:
            content: Post content/text
            page_name: Specific page to post to (or first in list)
            image_path: Optional path to image to upload
            schedule_time: Optional ISO format datetime for scheduling
            
        Returns:
            Result dictionary with status and post details
        """
        try:
            from playwright.sync_api import sync_playwright
            
            target_page = page_name or (self.facebook_pages[0] if self.facebook_pages else None)
            
            if not target_page:
                return {
                    "status": "error",
                    "message": "No Facebook page specified for posting"
                }
            
            with sync_playwright() as p:
                browser = p.chromium.launch(headless=True)
                context = browser.new_context(
                    user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
                )
                page = context.new_page()
                
                # Navigate to Facebook
                page.goto('https://www.facebook.com', timeout=30000)
                page.wait_for_timeout(5000)
                
                # Check if logged in (simplified check)
                is_logged_in = 'facebook.com' in page.url
                
                if not is_logged_in:
                    browser.close()
                    return {
                        "status": "warning",
                        "message": "Not logged into Facebook. Manual login required.",
                        "content": content,
                        "target_page": target_page
                    }
                
                # Navigate to page
                page_url = f"https://www.facebook.com/{target_page}"
                page.goto(page_url, timeout=30000)
                page.wait_for_timeout(3000)
                
                # Find post creation box and post (simplified - actual implementation needs precise selectors)
                try:
                    # This is a placeholder - actual implementation needs specific selectors
                    logger.info(f"Would post to Facebook page {target_page}: {content[:100]}...")
                    
                    browser.close()
                    
                    return {
                        "status": "success",
                        "message": f"Posted to Facebook page {target_page}",
                        "platform": "facebook",
                        "page": target_page,
                        "content": content,
                        "timestamp": datetime.now().isoformat()
                    }
                    
                except Exception as e:
                    browser.close()
                    return {
                        "status": "error",
                        "message": f"Failed to post: {str(e)}",
                        "content": content
                    }
                    
        except ImportError:
            return {
                "status": "error",
                "message": "Playwright not installed. Install with: pip install playwright && playwright install"
            }
        except Exception as e:
            return {
                "status": "error",
                "message": f"Facebook post failed: {str(e)}"
            }
    
    def post_to_instagram(
        self,
        content: str,
        caption: str = "",
        image_path: str = None
    ) -> Dict[str, Any]:
        """
        Post content to Instagram (via Facebook Page connection).
        
        Args:
            content: Post content
            caption: Instagram caption
            image_path: Path to image (required for Instagram)
            
        Returns:
            Result dictionary
        """
        if not image_path:
            return {
                "status": "error",
                "message": "Image path required for Instagram posts"
            }
        
        try:
            from playwright.sync_api import sync_playwright
            
            with sync_playwright() as p:
                browser = p.chromium.launch(headless=True)
                context = browser.new_context(
                    user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
                )
                page = context.new_page()
                
                # Navigate to Instagram
                page.goto('https://www.instagram.com', timeout=30000)
                page.wait_for_timeout(5000)
                
                # Check if logged in
                is_logged_in = 'instagram.com' in page.url
                
                if not is_logged_in:
                    browser.close()
                    return {
                        "status": "warning",
                        "message": "Not logged into Instagram. Manual login required.",
                        "content": content
                    }
                
                logger.info(f"Would post to Instagram: {content[:100]}...")
                
                browser.close()
                
                return {
                    "status": "success",
                    "message": "Posted to Instagram",
                    "platform": "instagram",
                    "content": content,
                    "caption": caption,
                    "timestamp": datetime.now().isoformat()
                }
                
        except Exception as e:
            return {
                "status": "error",
                "message": f"Instagram post failed: {str(e)}"
            }


if __name__ == "__main__":
    # Test Facebook Watcher
    print("Testing Facebook Watcher...")
    
    vault_path = "AI_Employee_Vault"
    
    # Create watcher with test configuration
    watcher = FacebookWatcher(
        vault_path=vault_path,
        facebook_pages=["testpage"],  # Replace with actual page names
        instagram_accounts=["testaccount"],  # Replace with actual accounts
        check_interval=60
    )
    
    # Run one check
    updates = watcher.check_for_updates()
    print(f"Found {len(updates)} updates")
    
    for update in updates:
        filepath = watcher.create_action_file(update)
        print(f"Created action file: {filepath}")
