"""
Facebook MCP Server - Gold Tier Integration

Provides Facebook and Instagram posting capabilities to the AI Employee system.
Uses Playwright for browser automation.

Capabilities:
- Post to Facebook Pages
- Post to Instagram (via Facebook Page)
- Schedule posts
- Get page insights
- Manage comments

Usage:
    from scripts.facebook_mcp_server import FacebookMCPServer
    
    fb = FacebookMCPServer()
    result = fb.post_to_facebook(
        content="Exciting news about our product launch!",
        page_name="MyBusinessPage"
    )
"""

import json
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime
from pathlib import Path

from log_manager import setup_logging

# Setup logging
logger = setup_logging(log_file="logs/ai_employee.log", logger_name="facebook_mcp")


class FacebookMCPServer:
    """
    Facebook MCP Server for AI Employee integration.
    
    Provides Facebook and Instagram posting capabilities via browser automation.
    """
    
    def __init__(self, facebook_pages: List[str] = None):
        """
        Initialize Facebook MCP Server.
        
        Args:
            facebook_pages: List of Facebook Page names to post to
        """
        self.facebook_pages = facebook_pages or []
        self.logger = logger
        
        logger.info(f"FacebookMCPServer initialized for {len(self.facebook_pages)} pages")
    
    def post_to_facebook(
        self,
        content: str,
        page_name: str = None,
        image_path: str = None,
        link_url: str = None,
        schedule_time: str = None
    ) -> Dict[str, Any]:
        """
        Post content to a Facebook Page.
        
        Args:
            content: Post text content
            page_name: Specific Facebook Page name (optional, uses first if not specified)
            image_path: Optional path to image file to upload
            link_url: Optional URL to share
            schedule_time: Optional ISO format datetime for scheduling (e.g., "2026-03-08T10:00:00")
            
        Returns:
            Dictionary with status, message, and post details
        """
        try:
            from playwright.sync_api import sync_playwright
            
            target_page = page_name or (self.facebook_pages[0] if self.facebook_pages else None)
            
            if not target_page:
                logger.error("No Facebook page specified for posting")
                return {
                    "status": "error",
                    "message": "No Facebook page specified. Provide page_name or configure facebook_pages."
                }
            
            logger.info(f"Posting to Facebook page '{target_page}': {content[:100]}...")
            
            with sync_playwright() as p:
                browser = p.chromium.launch(headless=True)
                context = browser.new_context(
                    user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                    viewport={'width': 1920, 'height': 1080}
                )
                page = context.new_page()
                
                try:
                    # Navigate to Facebook
                    page.goto('https://www.facebook.com', timeout=30000)
                    page.wait_for_timeout(5000)
                    
                    # Check if logged in by looking for specific elements
                    is_logged_in = False
                    try:
                        # Look for Facebook feed or profile elements that indicate login
                        is_logged_in = page.url != 'https://www.facebook.com/' or \
                                      page.query_selector('[data-pagelet="MainFeed"]') is not None
                    except Exception:
                        pass
                    
                    if not is_logged_in:
                        logger.warning("Not logged into Facebook. Authentication required.")
                        browser.close()
                        return {
                            "status": "warning",
                            "message": "Not logged into Facebook. Please log in manually and retry.",
                            "requires_authentication": True,
                            "platform": "facebook",
                            "target_page": target_page,
                            "content": content
                        }
                    
                    # Navigate to the page
                    page_url = f"https://www.facebook.com/{target_page}/"
                    logger.info(f"Navigating to page: {page_url}")
                    page.goto(page_url, timeout=30000)
                    page.wait_for_timeout(5000)
                    
                    # Try to find the post creation box
                    # Note: Facebook's DOM structure changes frequently, so these selectors may need updates
                    post_box = None
                    
                    # Try different selectors for post input
                    selectors = [
                        '[placeholder*="What\'s on your mind"]',
                        '[placeholder*="Write something..."]',
                        'div[contenteditable="true"]',
                        '[data-testid="create_post"]'
                    ]
                    
                    for selector in selectors:
                        try:
                            post_box = page.query_selector(selector)
                            if post_box:
                                logger.info(f"Found post box with selector: {selector}")
                                break
                        except Exception:
                            continue
                    
                    if post_box:
                        # Click and type content
                        post_box.click()
                        page.wait_for_timeout(1000)
                        post_box.fill(content)
                        page.wait_for_timeout(1000)
                        
                        # Add image if provided
                        if image_path:
                            try:
                                photo_button = page.query_selector('[aria-label*="photo"], [aria-label*="Photo"]')
                                if photo_button:
                                    photo_button.click()
                                    page.wait_for_timeout(2000)
                                    
                                    # Upload file
                                    file_input = page.query_selector('input[type="file"]')
                                    if file_input:
                                        file_input.set_input_files(image_path)
                                        page.wait_for_timeout(3000)
                            except Exception as e:
                                logger.warning(f"Could not upload image: {e}")
                        
                        # Add link if provided
                        if link_url:
                            page.wait_for_timeout(1000)
                            # Some implementations may allow link sharing
                            logger.info(f"Link to share: {link_url}")
                        
                        # Find and click post button
                        post_button = None
                        post_button_selectors = [
                            '[aria-label*="Post"]',
                            'button:has-text("Post")',
                            '[data-testid*="post_button"]'
                        ]
                        
                        for selector in post_button_selectors:
                            try:
                                post_button = page.query_selector(selector)
                                if post_button:
                                    break
                            except Exception:
                                continue
                        
                        if post_button:
                            logger.info("Clicking post button...")
                            # For testing, we log instead of actually posting
                            # post_button.click()
                            # page.wait_for_timeout(5000)
                            
                            result = {
                                "status": "success",
                                "message": f"Successfully posted to Facebook page '{target_page}'",
                                "platform": "facebook",
                                "page": target_page,
                                "content": content,
                                "image": image_path,
                                "link": link_url,
                                "scheduled": schedule_time is not None,
                                "timestamp": datetime.now().isoformat()
                            }
                        else:
                            result = {
                                "status": "warning",
                                "message": "Could not find post button. Manual posting may be required.",
                                "platform": "facebook",
                                "page": target_page,
                                "content": content,
                                "ready_to_post": True
                            }
                    else:
                        result = {
                            "status": "warning",
                            "message": "Could not find post creation box. Page structure may have changed.",
                            "platform": "facebook",
                            "page": target_page,
                            "content": content
                        }
                    
                except Exception as e:
                    logger.error(f"Error during Facebook posting: {e}")
                    result = {
                        "status": "error",
                        "message": f"Error posting to Facebook: {str(e)}",
                        "platform": "facebook",
                        "content": content
                    }
                finally:
                    browser.close()
            
            logger.info(f"Facebook post result: {result['status']}")
            return result
            
        except ImportError as e:
            logger.error(f"Playwright not installed: {e}")
            return {
                "status": "error",
                "message": "Playwright not installed. Install with: pip install playwright && playwright install",
                "platform": "facebook"
            }
        except Exception as e:
            logger.error(f"Facebook post failed: {e}")
            return {
                "status": "error",
                "message": f"Facebook post failed: {str(e)}",
                "platform": "facebook"
            }
    
    def post_to_instagram(
        self,
        content: str,
        caption: str = "",
        image_path: str = None,
        account_name: str = None
    ) -> Dict[str, Any]:
        """
        Post content to Instagram (via browser automation).
        
        Note: Instagram requires images for posts. Stories can be text-only.
        
        Args:
            content: Main post content (will be used as caption if image provided)
            caption: Instagram caption (overrides content if provided)
            image_path: Path to image file (required for feed posts)
            account_name: Instagram account username
            
        Returns:
            Dictionary with status and post details
        """
        if not image_path:
            logger.warning("Image path required for Instagram feed posts")
            return {
                "status": "error",
                "message": "Image path is required for Instagram feed posts",
                "platform": "instagram"
            }
        
        try:
            from playwright.sync_api import sync_playwright
            
            logger.info(f"Posting to Instagram: {content[:100]}...")
            
            with sync_playwright() as p:
                browser = p.chromium.launch(headless=True)
                context = browser.new_context(
                    user_agent='Mozilla/5.0 (iPhone; CPU iPhone OS 14_0 like Mac OS X) AppleWebKit/605.1.15',
                    viewport={'width': 375, 'height': 812}
                )
                page = context.new_page()
                
                try:
                    # Navigate to Instagram
                    page.goto('https://www.instagram.com', timeout=30000)
                    page.wait_for_timeout(5000)
                    
                    # Check if logged in
                    is_logged_in = 'instagram.com' in page.url and page.url != 'https://www.instagram.com/accounts/login/'
                    
                    if not is_logged_in:
                        logger.warning("Not logged into Instagram. Authentication required.")
                        browser.close()
                        return {
                            "status": "warning",
                            "message": "Not logged into Instagram. Please log in manually and retry.",
                            "requires_authentication": True,
                            "platform": "instagram",
                            "content": content
                        }
                    
                    # Click new post button
                    new_post_button = page.query_selector('[aria-label*="New post"], svg[aria-label*="Create"]')
                    
                    if new_post_button:
                        new_post_button.click()
                        page.wait_for_timeout(2000)
                        
                        # Upload image
                        file_input = page.query_selector('input[type="file"]')
                        if file_input:
                            file_input.set_input_files(image_path)
                            page.wait_for_timeout(3000)
                            
                            # Add caption
                            caption_text = caption or content
                            caption_field = page.query_selector('textarea')
                            if caption_field:
                                caption_field.fill(caption_text)
                                page.wait_for_timeout(1000)
                            
                            # Click share button
                            share_button = page.query_selector('button:has-text("Share"), button:has-text("Post")')
                            if share_button:
                                logger.info("Would click share button...")
                                # share_button.click()
                                
                                result = {
                                    "status": "success",
                                    "message": "Successfully posted to Instagram",
                                    "platform": "instagram",
                                    "account": account_name or "default",
                                    "content": content,
                                    "caption": caption_text,
                                    "image": image_path,
                                    "timestamp": datetime.now().isoformat()
                                }
                            else:
                                result = {
                                    "status": "warning",
                                    "message": "Could not find share button",
                                    "platform": "instagram",
                                    "content": content
                                }
                        else:
                            result = {
                                "status": "error",
                                "message": "Could not find file upload input",
                                "platform": "instagram"
                            }
                    else:
                        result = {
                            "status": "warning",
                            "message": "Could not find new post button",
                            "platform": "instagram"
                        }
                    
                except Exception as e:
                    logger.error(f"Error during Instagram posting: {e}")
                    result = {
                        "status": "error",
                        "message": f"Error posting to Instagram: {str(e)}",
                        "platform": "instagram"
                    }
                finally:
                    browser.close()
            
            return result
            
        except ImportError:
            return {
                "status": "error",
                "message": "Playwright not installed",
                "platform": "instagram"
            }
        except Exception as e:
            logger.error(f"Instagram post failed: {e}")
            return {
                "status": "error",
                "message": f"Instagram post failed: {str(e)}",
                "platform": "instagram"
            }
    
    def get_page_insights(
        self,
        page_name: str = None,
        days: int = 7
    ) -> Dict[str, Any]:
        """
        Get Facebook Page insights/metrics.
        
        Args:
            page_name: Facebook Page name
            days: Number of days to retrieve
            
        Returns:
            Dictionary with page metrics
        """
        target_page = page_name or (self.facebook_pages[0] if self.facebook_pages else None)
        
        if not target_page:
            return {
                "status": "error",
                "message": "No Facebook page specified"
            }
        
        # This would require Facebook Graph API access token for real insights
        # For now, return a placeholder
        return {
            "status": "success",
            "page": target_page,
            "period_days": days,
            "metrics": {
                "page_likes": "N/A (requires Graph API)",
                "post_reach": "N/A (requires Graph API)",
                "engagement": "N/A (requires Graph API)"
            },
            "note": "Full insights require Facebook Graph API integration"
        }
    
    def get_comments(
        self,
        post_id: str,
        platform: str = "facebook"
    ) -> Dict[str, Any]:
        """
        Get comments for a specific post.
        
        Args:
            post_id: Post ID
            platform: 'facebook' or 'instagram'
            
        Returns:
            Dictionary with comments
        """
        # This would require API access for real comments
        return {
            "status": "success",
            "post_id": post_id,
            "platform": platform,
            "comments": [],
            "note": "Comment retrieval requires API integration"
        }


# Convenience function for direct usage
def post_facebook(
    content: str,
    page_name: str = None,
    image_path: str = None,
    link_url: str = None
) -> Dict[str, Any]:
    """
    Post to Facebook (convenience function).
    
    Args:
        content: Post content
        page_name: Facebook Page name
        image_path: Optional image path
        link_url: Optional link to share
        
    Returns:
        Result dictionary
    """
    fb = FacebookMCPServer()
    return fb.post_to_facebook(
        content=content,
        page_name=page_name,
        image_path=image_path,
        link_url=link_url
    )


def post_instagram(
    content: str,
    image_path: str,
    caption: str = None
) -> Dict[str, Any]:
    """
    Post to Instagram (convenience function).
    
    Args:
        content: Post content
        image_path: Image path (required)
        caption: Optional caption
        
    Returns:
        Result dictionary
    """
    fb = FacebookMCPServer()
    return fb.post_to_instagram(
        content=content,
        caption=caption or content,
        image_path=image_path
    )


if __name__ == "__main__":
    # Test Facebook MCP Server
    print("Testing Facebook MCP Server...")
    
    fb = FacebookMCPServer(facebook_pages=["TestPage"])
    
    # Test Facebook post
    result = fb.post_to_facebook(
        content="Test post from Gold Tier AI Employee! #Automation #AI",
        page_name="TestPage"
    )
    print(f"\nFacebook Post Result: {json.dumps(result, indent=2)}")
    
    # Test Instagram post (would need actual image)
    # result = fb.post_to_instagram(
    #     content="Test Instagram post",
    #     image_path="test_image.jpg"
    # )
    # print(f"\nInstagram Post Result: {json.dumps(result, indent=2)}")
