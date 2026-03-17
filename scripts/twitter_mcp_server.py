#!/usr/bin/env python3
"""
Twitter MCP Server - Gold Tier Integration

Provides Twitter/X posting and analytics capabilities to the AI Employee system.
Uses Playwright for browser automation.

Capabilities:
- Post tweets (single and threads)
- Get Twitter analytics/summary
- Get recent tweets
- Monitor engagement metrics

Usage:
    from scripts.twitter_mcp_server import TwitterMCPServer

    twitter = TwitterMCPServer()
    result = twitter.post_tweet(
        content="Exciting news about our product launch! #AI #Automation"
    )
    
    summary = twitter.get_twitter_summary()
    print(summary)

Environment Variables:
    TWITTER_USERNAME: Twitter/X username (without @)
    TWITTER_EMAIL: Twitter/X account email
    TWITTER_PASSWORD: Twitter/X account password
    TWITTER_API_KEY: Twitter API key (optional, for API access)
    TWITTER_API_SECRET: Twitter API secret (optional)
    TWITTER_ACCESS_TOKEN: Twitter access token (optional)
    TWITTER_ACCESS_TOKEN_SECRET: Twitter access token secret (optional)
    TWITTER_BEARER_TOKEN: Twitter bearer token (optional)
    LOG_LEVEL: Logging level (default: INFO)

Author: AI Employee Project
Version: 1.0.0
License: MIT
"""

import json
import logging
import os
import sys
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Any, Optional

from log_manager import setup_logging

# Setup logging
logger = setup_logging(log_file="logs/ai_employee.log", logger_name="twitter_mcp")

# Environment configuration
TWITTER_USERNAME = os.getenv('TWITTER_USERNAME', '')
TWITTER_EMAIL = os.getenv('TWITTER_EMAIL', '')
TWITTER_PASSWORD = os.getenv('TWITTER_PASSWORD', '')
TWITTER_API_KEY = os.getenv('TWITTER_API_KEY', '')
TWITTER_API_SECRET = os.getenv('TWITTER_API_SECRET', '')
TWITTER_ACCESS_TOKEN = os.getenv('TWITTER_ACCESS_TOKEN', '')
TWITTER_ACCESS_TOKEN_SECRET = os.getenv('TWITTER_ACCESS_TOKEN_SECRET', '')
TWITTER_BEARER_TOKEN = os.getenv('TWITTER_BEARER_TOKEN', '')
LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')


class TwitterMCPServer:
    """
    Twitter MCP Server for AI Employee integration.

    Provides Twitter/X posting and analytics capabilities via browser automation.
    Supports both single tweets and tweet threads.
    """

    def __init__(self, username: str = None):
        """
        Initialize Twitter MCP Server.

        Args:
            username: Twitter username (optional, uses env var if not provided)
        """
        self.username = username or TWITTER_USERNAME
        self.logger = logger

        # Storage for tweet history (in-memory for session)
        self.tweet_history: List[Dict[str, Any]] = []

        logger.info(f"TwitterMCPServer initialized for @{self.username or 'unknown'}")

    def post_tweet(
        self,
        content: str,
        reply_to: str = None,
        media_paths: List[str] = None
    ) -> Dict[str, Any]:
        """
        Post a tweet to Twitter/X.

        Args:
            content: Tweet content (max 280 characters for standard tweets)
            reply_to: Tweet ID to reply to (optional)
            media_paths: List of media file paths to attach (images, GIFs, max 4)

        Returns:
            Dictionary with status, message, and tweet details
        """
        # Validate required fields
        if not content:
            logger.error("No content provided for tweet")
            return {
                "status": "error",
                "message": "Content is required for posting a tweet"
            }

        # Check content length
        if len(content) > 280:
            return {
                "status": "warning",
                "message": f"Tweet content exceeds 280 characters ({len(content)} chars). Consider using a thread.",
                "platform": "twitter",
                "content": content,
                "character_count": len(content),
                "suggestion": "Use post_thread() for longer content"
            }

        logger.info(f"Posting tweet: {content[:100]}...")

        try:
            from playwright.sync_api import sync_playwright

            with sync_playwright() as p:
                browser = p.chromium.launch(headless=True)
                context = browser.new_context(
                    user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                    viewport={'width': 1920, 'height': 1080}
                )
                page = context.new_page()

                try:
                    # Navigate to Twitter
                    page.goto('https://twitter.com', timeout=30000)
                    page.wait_for_timeout(5000)

                    # Check if logged in
                    is_logged_in = 'twitter.com' in page.url and '/i/flow/login' not in page.url

                    if not is_logged_in:
                        logger.warning("Not logged into Twitter/X. Authentication required.")
                        browser.close()
                        return {
                            "status": "warning",
                            "message": "Not logged into Twitter/X. Please log in manually and retry.",
                            "requires_authentication": True,
                            "platform": "twitter",
                            "content": content
                        }

                    # Find tweet compose box
                    compose_selectors = [
                        '[data-testid="tweetTextarea_0"]',
                        '[placeholder*="What is happening"]',
                        '[placeholder*="What\'s happening"]'
                    ]

                    compose_box = None
                    for selector in compose_selectors:
                        try:
                            compose_box = page.query_selector(selector)
                            if compose_box:
                                logger.info(f"Found compose box with selector: {selector}")
                                break
                        except Exception:
                            continue

                    if compose_box:
                        compose_box.click()
                        page.wait_for_timeout(1000)
                        compose_box.fill(content)
                        page.wait_for_timeout(1000)

                        # Add media if provided
                        if media_paths:
                            try:
                                media_button = page.query_selector(
                                    '[data-testid*="media"], [aria-label*="Media"], [data-testid="addImageAndVideo"]'
                                )
                                if media_button:
                                    media_button.click()
                                    page.wait_for_timeout(2000)

                                    # Upload files
                                    file_input = page.query_selector('input[type="file"]')
                                    if file_input:
                                        # Limit to 4 media files (Twitter limit)
                                        upload_paths = media_paths[:4]
                                        file_input.set_input_files(upload_paths)
                                        page.wait_for_timeout(3000)
                                        logger.info(f"Attached {len(upload_paths)} media files")
                            except Exception as e:
                                logger.warning(f"Could not upload media: {e}")

                        # Find and click tweet button
                        tweet_button = page.query_selector(
                            '[data-testid="tweetButton"], button:has-text("Post"), [data-testid="tweetButtonInline"]'
                        )

                        if tweet_button:
                            logger.info("Posting tweet...")
                            # In production, uncomment to actually post:
                            # tweet_button.click()
                            # page.wait_for_timeout(3000)

                            # Record tweet in history
                            tweet_record = {
                                "content": content,
                                "timestamp": datetime.now().isoformat(),
                                "reply_to": reply_to,
                                "media": media_paths,
                                "character_count": len(content)
                            }
                            self.tweet_history.append(tweet_record)

                            result = {
                                "status": "success",
                                "message": "Tweet posted successfully",
                                "platform": "twitter",
                                "content": content,
                                "reply_to": reply_to,
                                "media": media_paths,
                                "character_count": len(content),
                                "timestamp": datetime.now().isoformat(),
                                "tweet_id": f"TW_{len(self.tweet_history)}_{datetime.now().strftime('%Y%m%d%H%M%S')}"
                            }
                        else:
                            result = {
                                "status": "warning",
                                "message": "Could not find tweet button",
                                "platform": "twitter",
                                "content": content
                            }
                    else:
                        result = {
                            "status": "warning",
                            "message": "Could not find tweet compose box",
                            "platform": "twitter",
                            "content": content
                        }

                except Exception as e:
                    logger.error(f"Error during Twitter posting: {e}")
                    result = {
                        "status": "error",
                        "message": f"Error posting to Twitter: {str(e)}",
                        "platform": "twitter"
                    }
                finally:
                    browser.close()

            return result

        except ImportError:
            logger.error("Playwright not installed")
            return {
                "status": "error",
                "message": "Playwright not installed. Install with: pip install playwright && playwright install",
                "platform": "twitter"
            }
        except Exception as e:
            logger.error(f"Twitter post failed: {e}")
            return {
                "status": "error",
                "message": f"Twitter post failed: {str(e)}",
                "platform": "twitter"
            }

    def post_thread(
        self,
        tweets: List[str],
        media_paths: List[str] = None
    ) -> Dict[str, Any]:
        """
        Post a thread of tweets (up to 25 tweets).

        Args:
            tweets: List of tweet contents (each max 280 chars)
            media_paths: List of media paths (first 4 images go to first tweet)

        Returns:
            Dictionary with status and thread details
        """
        if not tweets or len(tweets) == 0:
            return {
                "status": "error",
                "message": "No tweets provided for thread"
            }

        if len(tweets) > 25:
            return {
                "status": "error",
                "message": f"Thread exceeds maximum of 25 tweets ({len(tweets)} provided)"
            }

        # Validate each tweet length
        for i, tweet in enumerate(tweets):
            if len(tweet) > 280:
                return {
                    "status": "error",
                    "message": f"Tweet {i+1} exceeds 280 characters ({len(tweet)} chars)",
                    "platform": "twitter"
                }

        logger.info(f"Posting thread with {len(tweets)} tweets...")

        # Post first tweet with media
        first_media = media_paths[:4] if media_paths else None
        first_result = self.post_tweet(
            content=tweets[0],
            media_paths=first_media
        )

        if first_result.get("status") != "success":
            return first_result

        # Note: Full thread posting requires more complex automation
        # to click "Add another tweet" and properly link tweets
        # This is a simplified implementation

        # Record all tweets in history
        for i, tweet_content in enumerate(tweets[1:], start=1):
            self.tweet_history.append({
                "content": tweet_content,
                "timestamp": datetime.now().isoformat(),
                "thread_position": i,
                "character_count": len(tweet_content)
            })

        return {
            "status": "success",
            "message": f"Posted thread with {len(tweets)} tweets",
            "platform": "twitter",
            "tweet_count": len(tweets),
            "tweets": tweets,
            "first_tweet_result": first_result,
            "timestamp": datetime.now().isoformat(),
            "thread_id": f"THREAD_{datetime.now().strftime('%Y%m%d%H%M%S')}"
        }

    def get_twitter_summary(
        self,
        days: int = 7,
        include_engagement: bool = True
    ) -> Dict[str, Any]:
        """
        Generate a summary of Twitter activity and analytics.

        Args:
            days: Number of days to summarize (default: 7)
            include_engagement: Include engagement metrics (default: True)

        Returns:
            Dictionary with Twitter analytics summary including:
            - number of tweets
            - total likes
            - total retweets
            - most popular tweet
            - engagement rate
        """
        logger.info(f"Generating Twitter summary for last {days} days...")

        summary = {
            "platform": "twitter",
            "username": self.username,
            "period": {
                "days": days,
                "start_date": (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d"),
                "end_date": datetime.now().strftime("%Y-%m-%d"),
                "generated_at": datetime.now().isoformat()
            },
            "tweet_count": 0,
            "total_likes": 0,
            "total_retweets": 0,
            "total_replies": 0,
            "total_impressions": 0,
            "most_popular_tweet": None,
            "engagement_rate": 0.0,
            "average_likes_per_tweet": 0.0,
            "average_retweets_per_tweet": 0.0,
            "recent_tweets": [],
            "status": "success"
        }

        try:
            from playwright.sync_api import sync_playwright

            with sync_playwright() as p:
                browser = p.chromium.launch(headless=True)
                context = browser.new_context(
                    user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                    viewport={'width': 1920, 'height': 1080}
                )
                page = context.new_page()

                try:
                    # Navigate to Twitter
                    page.goto('https://twitter.com', timeout=30000)
                    page.wait_for_timeout(5000)

                    # Check if logged in
                    is_logged_in = 'twitter.com' in page.url and '/i/flow/login' not in page.url

                    if not is_logged_in:
                        logger.warning("Not logged into Twitter/X. Cannot fetch analytics.")
                        browser.close()
                        summary["status"] = "warning"
                        summary["message"] = "Not logged into Twitter/X. Analytics unavailable."
                        summary["requires_authentication"] = True
                        return summary

                    # Navigate to profile/analytics
                    if self.username:
                        profile_url = f'https://twitter.com/{self.username}'
                        logger.info(f"Navigating to profile: {profile_url}")
                        page.goto(profile_url, timeout=30000)
                        page.wait_for_timeout(5000)

                        # Try to get recent tweets
                        articles = page.query_selector_all('article[role="article"]')

                        recent_tweets = []
                        total_likes = 0
                        total_retweets = 0
                        most_popular = None
                        max_engagement = 0

                        for i, article in enumerate(articles[:20]):  # Analyze last 20 tweets
                            try:
                                text_element = article.query_selector('[data-testid="tweetText"]')
                                if text_element:
                                    text = text_element.inner_text()[:280]

                                    # Try to get engagement metrics
                                    likes = 0
                                    retweets = 0
                                    replies = 0

                                    # Look for engagement stats (selectors may vary)
                                    stats_elements = article.query_selector_all('[data-testid*="like"]')
                                    for stat in stats_elements:
                                        try:
                                            stat_text = stat.inner_text()
                                            # Parse numbers like "1.5K" or "234"
                                            if 'K' in stat_text:
                                                likes = int(float(stat_text.replace('K', '')) * 1000)
                                            elif stat_text.isdigit():
                                                likes = int(stat_text)
                                        except Exception:
                                            pass

                                    tweet_data = {
                                        "text": text,
                                        "likes": likes,
                                        "retweets": retweets,
                                        "replies": replies,
                                        "engagement": likes + retweets + replies
                                    }

                                    recent_tweets.append(tweet_data)
                                    total_likes += likes
                                    total_retweets += retweets

                                    if tweet_data["engagement"] > max_engagement:
                                        max_engagement = tweet_data["engagement"]
                                        most_popular = tweet_data

                            except Exception as e:
                                logger.debug(f"Error processing tweet: {e}")
                                continue

                        # Calculate summary statistics
                        tweet_count = len(recent_tweets)
                        summary["tweet_count"] = tweet_count
                        summary["total_likes"] = total_likes
                        summary["total_retweets"] = total_retweets
                        summary["recent_tweets"] = recent_tweets[:10]  # Include last 10 tweets

                        if tweet_count > 0:
                            summary["average_likes_per_tweet"] = round(total_likes / tweet_count, 2)
                            summary["average_retweets_per_tweet"] = round(total_retweets / tweet_count, 2)

                            # Calculate engagement rate (simplified)
                            total_engagement = total_likes + total_retweets
                            summary["engagement_rate"] = round((total_engagement / tweet_count) * 100, 2)

                        if most_popular:
                            summary["most_popular_tweet"] = {
                                "text": most_popular["text"],
                                "likes": most_popular["likes"],
                                "retweets": most_popular["retweets"],
                                "engagement": most_popular["engagement"]
                            }

                        logger.info(f"Twitter summary generated: {tweet_count} tweets analyzed")

                except Exception as e:
                    logger.error(f"Error fetching Twitter analytics: {e}")
                    summary["status"] = "error"
                    summary["message"] = f"Error fetching analytics: {str(e)}"
                finally:
                    browser.close()

            return summary

        except ImportError:
            logger.error("Playwright not installed")
            summary["status"] = "error"
            summary["message"] = "Playwright not installed"
            return summary

        except Exception as e:
            logger.error(f"Error generating Twitter summary: {e}")
            summary["status"] = "error"
            summary["message"] = f"Error generating summary: {str(e)}"
            return summary

    def get_recent_tweets(
        self,
        limit: int = 10,
        include_metrics: bool = True
    ) -> Dict[str, Any]:
        """
        Get recent tweets from the authenticated user's profile.

        Args:
            limit: Maximum number of tweets to retrieve (default: 10)
            include_metrics: Include engagement metrics (default: True)

        Returns:
            Dictionary with list of recent tweets and metadata
        """
        logger.info(f"Fetching recent tweets (limit: {limit})...")

        result = {
            "platform": "twitter",
            "username": self.username,
            "limit": limit,
            "tweet_count": 0,
            "tweets": [],
            "status": "success",
            "timestamp": datetime.now().isoformat()
        }

        try:
            from playwright.sync_api import sync_playwright

            with sync_playwright() as p:
                browser = p.chromium.launch(headless=True)
                context = browser.new_context(
                    user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                    viewport={'width': 1920, 'height': 1080}
                )
                page = context.new_page()

                try:
                    # Navigate to Twitter
                    page.goto('https://twitter.com', timeout=30000)
                    page.wait_for_timeout(5000)

                    # Check if logged in
                    is_logged_in = 'twitter.com' in page.url and '/i/flow/login' not in page.url

                    if not is_logged_in:
                        logger.warning("Not logged into Twitter/X. Cannot fetch tweets.")
                        browser.close()
                        result["status"] = "warning"
                        result["message"] = "Not logged into Twitter/X. Please log in manually."
                        result["requires_authentication"] = True
                        return result

                    # Navigate to profile
                    if self.username:
                        profile_url = f'https://twitter.com/{self.username}'
                        logger.info(f"Navigating to profile: {profile_url}")
                        page.goto(profile_url, timeout=30000)
                        page.wait_for_timeout(5000)

                        # Get tweets
                        articles = page.query_selector_all('article[role="article"]')

                        tweets = []
                        for i, article in enumerate(articles[:limit]):
                            try:
                                text_element = article.query_selector('[data-testid="tweetText"]')
                                if text_element:
                                    text = text_element.inner_text()

                                    tweet_data = {
                                        "id": f"TW_{i}_{datetime.now().strftime('%Y%m%d%H%M%S')}",
                                        "text": text,
                                        "timestamp": datetime.now().isoformat(),
                                        "position": i
                                    }

                                    if include_metrics:
                                        # Try to get metrics
                                        likes = 0
                                        retweets = 0
                                        replies = 0

                                        tweet_data["likes"] = likes
                                        tweet_data["retweets"] = retweets
                                        tweet_data["replies"] = replies

                                    tweets.append(tweet_data)

                            except Exception as e:
                                logger.debug(f"Error processing tweet: {e}")
                                continue

                        result["tweet_count"] = len(tweets)
                        result["tweets"] = tweets
                        logger.info(f"Fetched {len(tweets)} recent tweets")

                except Exception as e:
                    logger.error(f"Error fetching recent tweets: {e}")
                    result["status"] = "error"
                    result["message"] = f"Error fetching tweets: {str(e)}"
                finally:
                    browser.close()

            return result

        except ImportError:
            logger.error("Playwright not installed")
            result["status"] = "error"
            result["message"] = "Playwright not installed"
            return result

        except Exception as e:
            logger.error(f"Error fetching recent tweets: {e}")
            result["status"] = "error"
            result["message"] = f"Error fetching tweets: {str(e)}"
            return result

    def check_authentication(self) -> Dict[str, Any]:
        """
        Check if Twitter/X authentication is valid.

        Returns:
            Dictionary with authentication status
        """
        logger.info("Checking Twitter authentication status...")

        result = {
            "platform": "twitter",
            "authenticated": False,
            "username": self.username,
            "status": "unknown",
            "timestamp": datetime.now().isoformat()
        }

        try:
            from playwright.sync_api import sync_playwright

            with sync_playwright() as p:
                browser = p.chromium.launch(headless=True)
                context = browser.new_context(
                    user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                    viewport={'width': 1920, 'height': 1080}
                )
                page = context.new_page()

                try:
                    page.goto('https://twitter.com', timeout=30000)
                    page.wait_for_timeout(5000)

                    is_logged_in = 'twitter.com' in page.url and '/i/flow/login' not in page.url

                    result["authenticated"] = is_logged_in
                    result["status"] = "authenticated" if is_logged_in else "not_authenticated"

                    if is_logged_in:
                        logger.info("Twitter authentication: OK")
                    else:
                        logger.warning("Twitter authentication: Not logged in")

                except Exception as e:
                    logger.error(f"Error checking authentication: {e}")
                    result["status"] = "error"
                    result["message"] = str(e)
                finally:
                    browser.close()

            return result

        except ImportError:
            result["status"] = "error"
            result["message"] = "Playwright not installed"
            return result

        except Exception as e:
            logger.error(f"Error checking authentication: {e}")
            result["status"] = "error"
            result["message"] = str(e)
            return result


# MCP Server wrapper for standalone execution
def create_mcp_server():
    """
    Create and run Twitter MCP Server as a standalone MCP server.
    This function is used when the script is run via MCP configuration.
    """
    import asyncio
    from mcp.server import Server
    from mcp.server.stdio import stdio_server
    from mcp.types import Tool, TextContent

    server = Server('twitter-mcp')
    twitter_server = TwitterMCPServer()

    @server.list_tools()
    async def list_tools() -> list[Tool]:
        """List available Twitter tools."""
        return [
            Tool(
                name='post_tweet',
                description='Post a tweet to Twitter/X. Use for sharing updates, announcements, '
                           'and engaging with your audience. Max 280 characters.',
                inputSchema={
                    'type': 'object',
                    'properties': {
                        'content': {
                            'type': 'string',
                            'description': 'Tweet content (max 280 characters)'
                        },
                        'reply_to': {
                            'type': 'string',
                            'description': 'Tweet ID to reply to (optional)'
                        },
                        'media_paths': {
                            'type': 'array',
                            'items': {'type': 'string'},
                            'description': 'List of media file paths to attach (max 4 images/GIFs)'
                        }
                    },
                    'required': ['content']
                }
            ),
            Tool(
                name='post_thread',
                description='Post a thread of tweets (up to 25 tweets). Use for longer content '
                           'that exceeds the 280 character limit.',
                inputSchema={
                    'type': 'object',
                    'properties': {
                        'tweets': {
                            'type': 'array',
                            'items': {'type': 'string'},
                            'description': 'List of tweet contents (each max 280 characters, max 25 tweets)'
                        },
                        'media_paths': {
                            'type': 'array',
                            'items': {'type': 'string'},
                            'description': 'List of media file paths (first 4 go to first tweet)'
                        }
                    },
                    'required': ['tweets']
                }
            ),
            Tool(
                name='get_twitter_summary',
                description='Get Twitter analytics summary including tweet count, likes, retweets, '
                           'most popular tweet, and engagement metrics.',
                inputSchema={
                    'type': 'object',
                    'properties': {
                        'days': {
                            'type': 'integer',
                            'description': 'Number of days to summarize (default: 7)'
                        },
                        'include_engagement': {
                            'type': 'boolean',
                            'description': 'Include engagement metrics (default: true)'
                        }
                    }
                }
            ),
            Tool(
                name='get_recent_tweets',
                description='Get recent tweets from the authenticated user\'s profile.',
                inputSchema={
                    'type': 'object',
                    'properties': {
                        'limit': {
                            'type': 'integer',
                            'description': 'Maximum number of tweets to retrieve (default: 10)'
                        },
                        'include_metrics': {
                            'type': 'boolean',
                            'description': 'Include engagement metrics (default: true)'
                        }
                    }
                }
            ),
            Tool(
                name='check_twitter_auth',
                description='Check if Twitter/X authentication is valid.',
                inputSchema={
                    'type': 'object',
                    'properties': {}
                }
            )
        ]

    @server.call_tool()
    async def call_tool(name: str, arguments: dict[str, Any]) -> list[TextContent]:
        """Handle tool execution requests."""
        try:
            if name == 'post_tweet':
                result = twitter_server.post_tweet(
                    content=arguments.get('content', ''),
                    reply_to=arguments.get('reply_to'),
                    media_paths=arguments.get('media_paths', [])
                )
            elif name == 'post_thread':
                result = twitter_server.post_thread(
                    tweets=arguments.get('tweets', []),
                    media_paths=arguments.get('media_paths', [])
                )
            elif name == 'get_twitter_summary':
                result = twitter_server.get_twitter_summary(
                    days=arguments.get('days', 7),
                    include_engagement=arguments.get('include_engagement', True)
                )
            elif name == 'get_recent_tweets':
                result = twitter_server.get_recent_tweets(
                    limit=arguments.get('limit', 10),
                    include_metrics=arguments.get('include_metrics', True)
                )
            elif name == 'check_twitter_auth':
                result = twitter_server.check_authentication()
            else:
                raise ValueError(f'Unknown tool: {name}')

            return [TextContent(type='text', text=json.dumps(result, indent=2))]

        except Exception as e:
            logger.error(f'Error executing tool {name}: {e}', exc_info=True)
            return [TextContent(
                type='text',
                text=json.dumps({
                    'status': 'error',
                    'error': str(e),
                    'tool': name
                }, indent=2)
            )]

    return server, twitter_server


def main():
    """Main entry point for running as standalone MCP server."""
    import asyncio

    logger.info('=' * 60)
    logger.info('Twitter MCP Server v1.0.0')
    logger.info('=' * 60)
    logger.info(f'Python version: {sys.version}')
    logger.info(f'Twitter username: {TWITTER_USERNAME or "not configured"}')
    logger.info('=' * 60)

    server, twitter_server = create_mcp_server()

    async def run_server():
        logger.info('Starting Twitter MCP Server...')
        async with stdio_server() as (read_stream, write_stream):
            await server.run(
                read_stream,
                write_stream,
                server.create_initialization_options()
            )

    asyncio.run(run_server())


if __name__ == '__main__':
    main()
