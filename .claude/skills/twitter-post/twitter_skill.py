#!/usr/bin/env python3
"""
Twitter Post Skill - Gold Tier Integration

Provides Twitter/X posting capabilities to the AI Employee system.
Saves all tweet history to AI_Employee_Vault/Reports/twitter_history.json

Capabilities:
- Post tweets (text up to 280 characters)
- Post threads (multiple connected tweets)
- Save tweet history to vault
- Log all actions

Usage:
    from .claude.skills.twitter_post.twitter_skill import TwitterSkill

    twitter = TwitterSkill()
    result = twitter.post_tweet(
        content="Exciting news from our AI Employee project! #AI #Automation",
        save_history=True
    )

Environment Variables:
    TWITTER_API_KEY: Twitter API Key
    TWITTER_API_SECRET: Twitter API Secret
    TWITTER_ACCESS_TOKEN: Twitter Access Token
    TWITTER_ACCESS_TOKEN_SECRET: Twitter Access Token Secret
    TWITTER_BEARER_TOKEN: Twitter Bearer Token (for OAuth 2.0)
    LOG_LEVEL: Logging level (default: INFO)
"""

import json
import logging
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

# Configure logging
log_level = os.getenv('LOG_LEVEL', 'INFO')
logging.basicConfig(
    level=getattr(logging, log_level.upper(), logging.INFO),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    stream=sys.stderr
)
logger = logging.getLogger('twitter_skill')

# Configuration
VAULT_PATH = Path(os.getenv('VAULT_PATH', 'AI_Employee_Vault'))
REPORTS_PATH = VAULT_PATH / 'Reports'
TWITTER_HISTORY_FILE = REPORTS_PATH / 'twitter_history.json'

# Ensure directories exist
REPORTS_PATH.mkdir(parents=True, exist_ok=True)


class TwitterSkill:
    """
    Twitter Post Skill for AI Employee integration.

    Supports posting tweets via Twitter API v2.
    All tweets are saved to history for audit purposes.
    """

    def __init__(
        self,
        api_key: str = None,
        api_secret: str = None,
        access_token: str = None,
        access_token_secret: str = None,
        bearer_token: str = None
    ):
        """
        Initialize Twitter skill.

        Args:
            api_key: Twitter API Key
            api_secret: Twitter API Secret
            access_token: Twitter Access Token
            access_token_secret: Twitter Access Token Secret
            bearer_token: Twitter Bearer Token (OAuth 2.0)
        """
        self.api_key = api_key or os.getenv('TWITTER_API_KEY', '')
        self.api_secret = api_secret or os.getenv('TWITTER_API_SECRET', '')
        self.access_token = access_token or os.getenv('TWITTER_ACCESS_TOKEN', '')
        self.access_token_secret = access_token_secret or os.getenv('TWITTER_ACCESS_TOKEN_SECRET', '')
        self.bearer_token = bearer_token or os.getenv('TWITTER_BEARER_TOKEN', '')

        self._client = None
        logger.info('TwitterSkill initialized')

    def _get_client(self):
        """Get Twitter API client."""
        try:
            import tweepy

            if self.bearer_token:
                # OAuth 2.0 Bearer Token
                client = tweepy.Client(bearer_token=self.bearer_token)
            elif all([self.api_key, self.api_secret, self.access_token, self.access_token_secret]):
                # OAuth 1.0a User Context
                client = tweepy.Client(
                    consumer_key=self.api_key,
                    consumer_secret=self.api_secret,
                    access_token=self.access_token,
                    access_token_secret=self.access_token_secret
                )
            else:
                raise ValueError(
                    "Twitter credentials not configured. Set environment variables:\n"
                    "  TWITTER_API_KEY, TWITTER_API_SECRET,\n"
                    "  TWITTER_ACCESS_TOKEN, TWITTER_ACCESS_TOKEN_SECRET\n"
                    "Or use TWITTER_BEARER_TOKEN for OAuth 2.0"
                )

            self._client = client
            return client

        except ImportError:
            raise ImportError(
                "tweepy not installed. Install with: pip install tweepy"
            )

    def post_tweet(
        self,
        content: str,
        reply_to: int = None,
        save_history: bool = True
    ) -> Dict[str, Any]:
        """
        Post a tweet to Twitter/X.

        Args:
            content: Tweet content (max 280 characters)
            reply_to: Tweet ID to reply to (optional)
            save_history: Whether to save to history file (default: True)

        Returns:
            Dictionary with tweet details and status
        """
        # Validate content
        if not content:
            raise ValueError("Tweet content is required")

        if len(content) > 280:
            raise ValueError(f"Tweet content exceeds 280 character limit (current: {len(content)})")

        logger.info(f"Posting tweet: {content[:50]}...")

        try:
            client = self._get_client()

            # Post the tweet
            response = client.create_tweet(
                text=content,
                in_reply_to_tweet_id=reply_to
            )

            tweet_id = response.data['id']
            tweet_url = f"https://twitter.com/user/status/{tweet_id}"

            result = {
                "status": "success",
                "tweet_id": tweet_id,
                "content": content,
                "tweet_url": tweet_url,
                "timestamp": datetime.now().isoformat(),
                "reply_to": reply_to
            }

            logger.info(f"Tweet posted successfully: {tweet_id}")

            # Save to history
            if save_history:
                self._save_to_history(result)

            return result

        except Exception as e:
            logger.error(f"Failed to post tweet: {e}", exc_info=True)
            return {
                "status": "error",
                "message": str(e),
                "content": content,
                "timestamp": datetime.now().isoformat()
            }

    def post_thread(
        self,
        tweets: List[str],
        save_history: bool = True
    ) -> Dict[str, Any]:
        """
        Post a thread of tweets.

        Args:
            tweets: List of tweet contents (each max 280 characters)
            save_history: Whether to save to history file (default: True)

        Returns:
            Dictionary with thread details and status
        """
        if not tweets:
            raise ValueError("At least one tweet is required")

        if len(tweets) > 25:
            raise ValueError("Twitter threads are limited to 25 tweets")

        logger.info(f"Posting thread with {len(tweets)} tweets")

        try:
            client = self._get_client()
            tweet_ids = []
            results = []

            # Post first tweet
            first_response = client.create_tweet(text=tweets[0])
            first_id = first_response.data['id']
            tweet_ids.append(first_id)

            results.append({
                "tweet_id": first_id,
                "content": tweets[0],
                "position": 1
            })

            logger.info(f"First tweet posted: {first_id}")

            # Post reply tweets
            previous_id = first_id
            for i, tweet_content in enumerate(tweets[1:], start=2):
                response = client.create_tweet(
                    text=tweet_content,
                    in_reply_to_tweet_id=previous_id
                )
                tweet_id = response.data['id']
                tweet_ids.append(tweet_id)
                previous_id = tweet_id

                results.append({
                    "tweet_id": tweet_id,
                    "content": tweet_content,
                    "position": i
                })

                logger.info(f"Thread tweet {i} posted: {tweet_id}")

            thread_url = f"https://twitter.com/user/status/{first_id}"

            thread_result = {
                "status": "success",
                "thread_id": first_id,
                "tweet_count": len(tweets),
                "tweet_ids": tweet_ids,
                "thread_url": thread_url,
                "timestamp": datetime.now().isoformat(),
                "tweets": results
            }

            # Save to history
            if save_history:
                self._save_to_history(thread_result, is_thread=True)

            return thread_result

        except Exception as e:
            logger.error(f"Failed to post thread: {e}", exc_info=True)
            return {
                "status": "error",
                "message": str(e),
                "tweet_count": len(tweets),
                "timestamp": datetime.now().isoformat()
            }

    def _save_to_history(self, result: Dict[str, Any], is_thread: bool = False):
        """Save tweet/thread to history file."""
        try:
            history = self._load_history()

            entry = {
                "type": "thread" if is_thread else "tweet",
                "timestamp": result.get("timestamp", datetime.now().isoformat()),
                "data": result
            }

            history.append(entry)

            # Save updated history
            with open(TWITTER_HISTORY_FILE, 'w', encoding='utf-8') as f:
                json.dump(history, f, indent=2)

            logger.info(f"Saved {entry['type']} to history: {TWITTER_HISTORY_FILE}")

        except Exception as e:
            logger.error(f"Failed to save to history: {e}")

    def _load_history(self) -> List[Dict[str, Any]]:
        """Load tweet history from file."""
        try:
            if TWITTER_HISTORY_FILE.exists():
                with open(TWITTER_HISTORY_FILE, 'r', encoding='utf-8') as f:
                    return json.load(f)
        except (json.JSONDecodeError, IOError) as e:
            logger.warning(f"Failed to load history: {e}")

        return []

    def get_history(
        self,
        limit: int = 10,
        tweet_type: str = "all"
    ) -> Dict[str, Any]:
        """
        Get tweet history.

        Args:
            limit: Maximum number of entries to return
            tweet_type: Filter by type ('tweet', 'thread', 'all')

        Returns:
            Dictionary with history entries
        """
        history = self._load_history()

        # Filter by type
        if tweet_type != "all":
            history = [h for h in history if h.get('type') == tweet_type]

        # Limit results
        history = history[-limit:] if limit else history

        return {
            "status": "success",
            "count": len(history),
            "history": history
        }

    def get_stats(self) -> Dict[str, Any]:
        """Get tweet statistics."""
        history = self._load_history()

        total_tweets = len([h for h in history if h.get('type') == 'tweet'])
        total_threads = len([h for h in history if h.get('type') == 'thread'])
        total_thread_tweets = sum(
            len(h.get('data', {}).get('tweets', []))
            for h in history if h.get('type') == 'thread'
        )

        return {
            "status": "success",
            "total_tweets": total_tweets,
            "total_threads": total_threads,
            "total_thread_tweets": total_thread_tweets,
            "total_published": total_tweets + total_thread_tweets,
            "history_file": str(TWITTER_HISTORY_FILE)
        }


# Convenience function
def get_twitter_client() -> TwitterSkill:
    """Get a Twitter skill client."""
    return TwitterSkill()


if __name__ == '__main__':
    # Test the skill
    print("=" * 60)
    print("Twitter Skill - Test Mode")
    print("=" * 60)

    twitter = TwitterSkill()

    # Test stats
    stats = twitter.get_stats()
    print(f"\nTwitter Stats: {json.dumps(stats, indent=2)}")

    # Test history
    history = twitter.get_history(limit=5)
    print(f"\nRecent History: {json.dumps(history, indent=2)}")

    print("\nNote: To post tweets, configure Twitter API credentials in environment variables.")
