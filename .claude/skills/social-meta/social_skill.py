#!/usr/bin/env python3
"""
Social Media Agent Skill - Gold Tier Integration

Provides Facebook and Instagram posting capabilities to the AI Employee system.
Logs all actions to logs/social.log

Capabilities:
- Post to Facebook pages
- Post to Instagram business accounts
- Cross-post to both platforms
- Log all actions with timestamps
- Support for images and text

Usage:
    from .claude.skills.social_meta.social_skill import SocialMediaSkill

    social = SocialMediaSkill()
    
    # Post to Facebook
    result = social.post_facebook(
        content="Exciting update from our company!",
        image_path="path/to/image.jpg"  # Optional
    )
    
    # Post to Instagram
    result = social.post_instagram(
        content="Beautiful product photo! #instagram #business",
        image_path="path/to/image.jpg"
    )

Environment Variables:
    FACEBOOK_PAGE_ID: Facebook Page ID
    FACEBOOK_ACCESS_TOKEN: Facebook Page Access Token
    INSTAGRAM_BUSINESS_ACCOUNT_ID: Instagram Business Account ID
    INSTAGRAM_ACCESS_TOKEN: Instagram Access Token (can be same as Facebook)
    LOG_LEVEL: Logging level (default: INFO)
"""

import json
import logging
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional

# Configure logging
log_level = os.getenv('LOG_LEVEL', 'INFO')
log_file = os.getenv('SOCIAL_LOG_FILE', 'logs/social.log')

# Ensure log directory exists
log_path = Path(log_file)
log_path.parent.mkdir(parents=True, exist_ok=True)

# File handler for social media logs
file_handler = logging.FileHandler(log_path)
file_handler.setLevel(logging.INFO)
file_handler.setFormatter(logging.Formatter(
    '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
))

# Console handler
console_handler = logging.StreamHandler(sys.stderr)
console_handler.setLevel(logging.INFO)
console_handler.setFormatter(logging.Formatter(
    '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
))

# Logger setup
logger = logging.getLogger('social_media_skill')
logger.setLevel(logging.INFO)
logger.addHandler(file_handler)
logger.addHandler(console_handler)

# Configuration
FACEBOOK_PAGE_ID = os.getenv('FACEBOOK_PAGE_ID', '')
FACEBOOK_ACCESS_TOKEN = os.getenv('FACEBOOK_ACCESS_TOKEN', '')
INSTAGRAM_BUSINESS_ACCOUNT_ID = os.getenv('INSTAGRAM_BUSINESS_ACCOUNT_ID', '')
INSTAGRAM_ACCESS_TOKEN = os.getenv('INSTAGRAM_ACCESS_TOKEN', '')


class SocialMediaSkill:
    """
    Social Media Skill for AI Employee integration.

    Supports posting to Facebook Pages and Instagram Business accounts
    via the Meta Graph API.
    """

    def __init__(
        self,
        facebook_page_id: str = None,
        facebook_access_token: str = None,
        instagram_business_account_id: str = None,
        instagram_access_token: str = None
    ):
        """
        Initialize Social Media skill.

        Args:
            facebook_page_id: Facebook Page ID
            facebook_access_token: Facebook Page Access Token
            instagram_business_account_id: Instagram Business Account ID
            instagram_access_token: Instagram Access Token
        """
        self.facebook_page_id = facebook_page_id or FACEBOOK_PAGE_ID
        self.facebook_access_token = facebook_access_token or FACEBOOK_ACCESS_TOKEN
        self.instagram_business_account_id = instagram_business_account_id or INSTAGRAM_BUSINESS_ACCOUNT_ID
        self.instagram_access_token = instagram_access_token or INSTAGRAM_ACCESS_TOKEN

        self._session = None
        logger.info('SocialMediaSkill initialized')

    def _get_session(self):
        """Get requests session for API calls."""
        try:
            import requests
            if self._session is None:
                self._session = requests.Session()
            return self._session
        except ImportError:
            raise ImportError(
                "requests not installed. Install with: pip install requests"
            )

    def _make_graph_request(
        self,
        endpoint: str,
        method: str = 'GET',
        data: Dict[str, Any] = None,
        files: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """Make a request to Meta Graph API."""
        session = self._get_session()
        base_url = "https://graph.facebook.com/v18.0"

        url = f"{base_url}/{endpoint}"

        try:
            if method == 'GET':
                response = session.get(url, params=data, timeout=30)
            elif method == 'POST':
                if files:
                    response = session.post(url, data=data, files=files, timeout=30)
                else:
                    response = session.post(url, data=data, timeout=30)
            else:
                raise ValueError(f"Unsupported HTTP method: {method}")

            response.raise_for_status()
            return response.json()

        except requests.exceptions.RequestException as e:
            logger.error(f"Graph API request failed: {e}")
            if hasattr(e, 'response') and e.response is not None:
                try:
                    error_data = e.response.json()
                    logger.error(f"API Error: {error_data}")
                except:
                    pass
            raise

    def post_facebook(
        self,
        content: str,
        image_path: str = None,
        link: str = None,
        scheduled_time: str = None
    ) -> Dict[str, Any]:
        """
        Post to Facebook Page.

        Args:
            content: Post content/text
            image_path: Path to image file (optional)
            link: URL to share (optional)
            scheduled_time: ISO 8601 datetime for scheduled posting (optional)

        Returns:
            Dictionary with post details and status
        """
        if not content and not image_path and not link:
            raise ValueError("At least one of content, image_path, or link is required")

        if not self.facebook_page_id:
            raise ValueError(
                "Facebook Page ID not configured. Set FACEBOOK_PAGE_ID environment variable."
            )

        if not self.facebook_access_token:
            raise ValueError(
                "Facebook Access Token not configured. Set FACEBOOK_ACCESS_TOKEN environment variable."
            )

        logger.info(f"Posting to Facebook: {content[:50]}..." if content else "Posting image/link to Facebook")

        try:
            endpoint = f"{self.facebook_page_id}/feed"

            data = {
                'access_token': self.facebook_access_token,
            }

            if content:
                data['message'] = content

            if link:
                data['link'] = link

            if scheduled_time:
                data['scheduled_publish_time'] = scheduled_time
                data['published'] = False

            files = {}
            if image_path:
                if not os.path.exists(image_path):
                    raise FileNotFoundError(f"Image not found: {image_path}")
                files['source'] = open(image_path, 'rb')
                # For photo upload, use photos endpoint instead
                endpoint = f"{self.facebook_page_id}/photos"

            result = self._make_graph_request(
                endpoint=endpoint,
                method='POST',
                data=data,
                files=files if files else None
            )

            if image_path and files:
                files['source'].close()

            post_url = f"https://facebook.com/{self.facebook_page_id}/posts/{result.get('id', 'unknown')}"

            response_data = {
                "status": "success",
                "platform": "facebook",
                "post_id": result.get('id', ''),
                "post_url": post_url,
                "content": content[:100] + "..." if content and len(content) > 100 else content,
                "has_image": image_path is not None,
                "has_link": link is not None,
                "scheduled": scheduled_time is not None,
                "timestamp": datetime.now().isoformat()
            }

            logger.info(f"Facebook post successful: {result.get('id', '')}")
            self._log_action("facebook_post", response_data)

            return response_data

        except Exception as e:
            logger.error(f"Failed to post to Facebook: {e}", exc_info=True)
            error_data = {
                "status": "error",
                "platform": "facebook",
                "message": str(e),
                "content": content[:100] if content else "",
                "timestamp": datetime.now().isoformat()
            }
            self._log_action("facebook_post_error", error_data)
            return error_data

    def post_instagram(
        self,
        content: str,
        image_path: str,
        location_id: str = None,
        share_to_facebook: bool = False
    ) -> Dict[str, Any]:
        """
        Post to Instagram Business Account.

        Note: Instagram API requires images for all posts.
        For carousel posts, use post_instagram_carousel().

        Args:
            content: Caption text (max 2200 characters)
            image_path: Path to image file (required)
            location_id: Facebook Location ID (optional)
            share_to_facebook: Share to connected Facebook page (optional)

        Returns:
            Dictionary with post details and status
        """
        if not content:
            raise ValueError("Instagram caption is required")

        if not image_path:
            raise ValueError("Instagram requires an image for posts")

        if not self.instagram_business_account_id:
            raise ValueError(
                "Instagram Business Account ID not configured. "
                "Set INSTAGRAM_BUSINESS_ACCOUNT_ID environment variable."
            )

        if not self.instagram_access_token:
            raise ValueError(
                "Instagram Access Token not configured. "
                "Set INSTAGRAM_ACCESS_TOKEN environment variable."
            )

        if not os.path.exists(image_path):
            raise FileNotFoundError(f"Image not found: {image_path}")

        logger.info(f"Posting to Instagram: {content[:50]}...")

        try:
            # Step 1: Create media container
            create_endpoint = f"{self.instagram_business_account_id}/media"

            create_data = {
                'image_url': self._get_public_image_url(image_path),
                'caption': content,
                'access_token': self.instagram_access_token,
            }

            if location_id:
                create_data['location_id'] = location_id

            create_result = self._make_graph_request(
                endpoint=create_endpoint,
                method='POST',
                data=create_data
            )

            creation_id = create_result.get('id')
            if not creation_id:
                raise ValueError("Failed to create media container")

            logger.info(f"Instagram media container created: {creation_id}")

            # Step 2: Publish the media
            publish_endpoint = f"{self.instagram_business_account_id}/media_publish"

            publish_data = {
                'creation_id': creation_id,
                'access_token': self.instagram_access_token,
            }

            if share_to_facebook and self.facebook_page_id:
                publish_data['share_to_facebook'] = True

            publish_result = self._make_graph_request(
                endpoint=publish_endpoint,
                method='POST',
                data=publish_data
            )

            media_id = publish_result.get('id', '')
            post_url = f"https://instagram.com/p/{media_id}"

            response_data = {
                "status": "success",
                "platform": "instagram",
                "media_id": media_id,
                "post_url": post_url,
                "content": content[:100] + "..." if len(content) > 100 else content,
                "image_path": image_path,
                "share_to_facebook": share_to_facebook,
                "timestamp": datetime.now().isoformat()
            }

            logger.info(f"Instagram post successful: {media_id}")
            self._log_action("instagram_post", response_data)

            return response_data

        except Exception as e:
            logger.error(f"Failed to post to Instagram: {e}", exc_info=True)
            error_data = {
                "status": "error",
                "platform": "instagram",
                "message": str(e),
                "content": content[:100] if len(content) > 100 else content,
                "timestamp": datetime.now().isoformat()
            }
            self._log_action("instagram_post_error", error_data)
            return error_data

    def post_instagram_carousel(
        self,
        content: str,
        image_paths: list,
        share_to_facebook: bool = False
    ) -> Dict[str, Any]:
        """
        Post a carousel (multiple images) to Instagram.

        Args:
            content: Caption text
            image_paths: List of image paths (2-10 images)
            share_to_facebook: Share to connected Facebook page

        Returns:
            Dictionary with post details and status
        """
        if not image_paths or len(image_paths) < 2:
            raise ValueError("Carousel requires at least 2 images")

        if len(image_paths) > 10:
            raise ValueError("Carousel limited to 10 images")

        logger.info(f"Posting Instagram carousel with {len(image_paths)} images")

        try:
            # Create children array
            children = []

            for image_path in image_paths:
                if not os.path.exists(image_path):
                    raise FileNotFoundError(f"Image not found: {image_path}")

                # Create media container for each image
                create_endpoint = f"{self.instagram_business_account_id}/media"

                create_data = {
                    'image_url': self._get_public_image_url(image_path),
                    'media_type': 'IMAGE',
                    'access_token': self.instagram_access_token,
                }

                create_result = self._make_graph_request(
                    endpoint=create_endpoint,
                    method='POST',
                    data=create_data
                )

                children.append(create_result.get('id'))

            # Create carousel container
            carousel_endpoint = f"{self.instagram_business_account_id}/media"

            carousel_data = {
                'media_type': 'CAROUSEL',
                'children': ','.join(children),
                'caption': content,
                'access_token': self.instagram_access_token,
            }

            carousel_result = self._make_graph_request(
                endpoint=carousel_endpoint,
                method='POST',
                data=carousel_data
            )

            creation_id = carousel_result.get('id')

            # Publish
            publish_endpoint = f"{self.instagram_business_account_id}/media_publish"

            publish_data = {
                'creation_id': creation_id,
                'access_token': self.instagram_access_token,
            }

            if share_to_facebook:
                publish_data['share_to_facebook'] = True

            publish_result = self._make_graph_request(
                endpoint=publish_endpoint,
                method='POST',
                data=publish_data
            )

            media_id = publish_result.get('id', '')

            response_data = {
                "status": "success",
                "platform": "instagram",
                "post_type": "carousel",
                "media_id": media_id,
                "image_count": len(image_paths),
                "content": content[:100] + "..." if len(content) > 100 else content,
                "timestamp": datetime.now().isoformat()
            }

            logger.info(f"Instagram carousel post successful: {media_id}")
            self._log_action("instagram_carousel_post", response_data)

            return response_data

        except Exception as e:
            logger.error(f"Failed to post Instagram carousel: {e}", exc_info=True)
            error_data = {
                "status": "error",
                "platform": "instagram",
                "post_type": "carousel",
                "message": str(e),
                "timestamp": datetime.now().isoformat()
            }
            self._log_action("instagram_carousel_post_error", error_data)
            return error_data

    def post_to_both(
        self,
        content: str,
        image_path: str = None,
        facebook_link: str = None
    ) -> Dict[str, Any]:
        """
        Post to both Facebook and Instagram.

        Args:
            content: Post content
            image_path: Path to image file
            facebook_link: URL to share on Facebook (optional)

        Returns:
            Dictionary with results from both platforms
        """
        logger.info("Posting to both Facebook and Instagram")

        results = {
            "facebook": None,
            "instagram": None,
            "timestamp": datetime.now().isoformat()
        }

        # Post to Facebook
        if self.facebook_page_id and self.facebook_access_token:
            results["facebook"] = self.post_facebook(
                content=content,
                image_path=image_path,
                link=facebook_link
            )

        # Post to Instagram (requires image)
        if self.instagram_business_account_id and self.instagram_access_token and image_path:
            results["instagram"] = self.post_instagram(
                content=content,
                image_path=image_path,
                share_to_facebook=False
            )

        self._log_action("cross_post", results)
        return results

    def _get_public_image_url(self, image_path: str) -> str:
        """
        Get a publicly accessible URL for an image.

        For production, upload to a CDN or public storage.
        For development, this is a placeholder.

        Args:
            image_path: Local path to image

        Returns:
            Public URL string
        """
        # In production, upload to cloud storage and return URL
        # For now, return a placeholder that assumes image is publicly accessible
        # You should implement proper image hosting (e.g., AWS S3, Cloudinary)

        image_path = Path(image_path).resolve()

        # If you have a CDN URL configured
        cdn_base = os.getenv('IMAGE_CDN_BASE', '')
        if cdn_base:
            return f"{cdn_base}/{image_path.name}"

        # For local development, the image needs to be publicly accessible
        # This is a limitation - in production, use proper image hosting
        raise ValueError(
            "Image must be hosted on a public URL for Instagram API. "
            "Set IMAGE_CDN_BASE environment variable or upload image to cloud storage."
        )

    def _log_action(self, action_type: str, data: Dict[str, Any]):
        """Log action to social.log file."""
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "action": action_type,
            "data": data
        }

        logger.info(f"{action_type}: {json.dumps(data, indent=2)}")

    def get_account_info(self) -> Dict[str, Any]:
        """Get connected account information."""
        info = {
            "facebook": {
                "configured": bool(self.facebook_page_id and self.facebook_access_token),
                "page_id": self.facebook_page_id[:10] + "..." if self.facebook_page_id else None
            },
            "instagram": {
                "configured": bool(self.instagram_business_account_id and self.instagram_access_token),
                "account_id": self.instagram_business_account_id[:10] + "..." if self.instagram_business_account_id else None
            },
            "timestamp": datetime.now().isoformat()
        }

        if info["facebook"]["configured"]:
            try:
                result = self._make_graph_request(
                    endpoint=self.facebook_page_id,
                    method='GET',
                    data={'fields': 'name', 'access_token': self.facebook_access_token}
                )
                info["facebook"]["name"] = result.get('name', 'Unknown')
            except Exception as e:
                info["facebook"]["error"] = str(e)

        if info["instagram"]["configured"]:
            try:
                result = self._make_graph_request(
                    endpoint=self.instagram_business_account_id,
                    method='GET',
                    data={'fields': 'username,name', 'access_token': self.instagram_access_token}
                )
                info["instagram"]["username"] = result.get('username', 'Unknown')
                info["instagram"]["name"] = result.get('name', 'Unknown')
            except Exception as e:
                info["instagram"]["error"] = str(e)

        return info


# Convenience function
def get_social_media_client() -> SocialMediaSkill:
    """Get a Social Media skill client."""
    return SocialMediaSkill()


if __name__ == '__main__':
    # Test the skill
    print("=" * 60)
    print("Social Media Skill - Test Mode")
    print("=" * 60)

    social = SocialMediaSkill()

    # Get account info
    info = social.get_account_info()
    print(f"\nAccount Info: {json.dumps(info, indent=2)}")

    print("\nNote: To post to social media, configure credentials in environment variables.")
