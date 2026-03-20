# Twitter Post Skill

**Tier:** Gold
**Version:** 1.0.0
**Author:** AI Employee Hackathon Team

---

## Overview

The Twitter Post Skill provides Twitter/X posting capabilities to the AI Employee system. It supports posting individual tweets, threads, and maintains a complete history of all tweets in the AI Employee Vault for audit purposes.

---

## Capabilities

- **Tweet Posting**
  - `post_tweet()` - Post individual tweets (up to 280 characters)
  - `post_thread()` - Post connected tweet threads (up to 25 tweets)
  - Reply to existing tweets

- **History Management**
  - Automatic history saving to `AI_Employee_Vault/Reports/twitter_history.json`
  - Retrieve tweet history with filtering
  - Statistics and analytics

- **Integration**
  - Works with scheduler for automated posting
  - Compatible with human approval workflow
  - Logs all actions to `logs/social.log`

---

## Installation

### Prerequisites

1. Twitter Developer Account
2. Twitter App with API access
3. Python 3.8+
4. Required package: `tweepy`

### Setup

```bash
# Install tweepy
pip install tweepy

# Create Twitter app at https://developer.twitter.com/
# Get your API credentials
```

### Environment Variables

Create a `.env` file or set environment variables:

```bash
# Twitter API Credentials (OAuth 1.0a)
TWITTER_API_KEY=your_api_key
TWITTER_API_SECRET=your_api_secret
TWITTER_ACCESS_TOKEN=your_access_token
TWITTER_ACCESS_TOKEN_SECRET=your_access_token_secret

# OR use OAuth 2.0 Bearer Token
TWITTER_BEARER_TOKEN=your_bearer_token

# Optional
LOG_LEVEL=INFO
VAULT_PATH=AI_Employee_Vault
```

---

## Usage

### Basic Tweet

```python
from .claude.skills.twitter_post import TwitterSkill

twitter = TwitterSkill()

# Post a simple tweet
result = twitter.post_tweet(
    content="Exciting news from our AI Employee project! #AI #Automation"
)

if result['status'] == 'success':
    print(f"Tweet posted: {result['tweet_url']}")
else:
    print(f"Error: {result['message']}")
```

### Thread Posting

```python
# Post a thread
tweets = [
    "🧵 Thread: Introducing our AI Employee System",
    "1/4 The AI Employee automates business workflows including email, social media, and accounting.",
    "2/4 It features multiple tiers: Bronze (basic watchers), Silver (scheduler), Gold (MCP servers), and Platinum (human approval).",
    "3/4 Built with Python, it integrates with Gmail, LinkedIn, Twitter, Facebook, Odoo, and more.",
    "4/4 Check out the full project on GitHub! #OpenSource #AI #Automation"
]

result = twitter.post_thread(tweets)

if result['status'] == 'success':
    print(f"Thread posted: {result['thread_url']}")
    print(f"Total tweets: {result['tweet_count']}")
```

### Reply to Tweet

```python
# Reply to an existing tweet
result = twitter.post_tweet(
    content="Thank you for your interest! We'd love to show you a demo.",
    reply_to=1234567890  # Tweet ID to reply to
)
```

### Get History

```python
# Get recent tweets
history = twitter.get_history(limit=10)
print(f"Total entries: {history['count']}")

for entry in history['history']:
    print(f"{entry['timestamp']}: {entry['type']}")
```

### Get Statistics

```python
stats = twitter.get_stats()
print(f"Total tweets: {stats['total_tweets']}")
print(f"Total threads: {stats['total_threads']}")
print(f"Total published: {stats['total_published']}")
```

---

## API Reference

### `post_tweet()`

Post a single tweet to Twitter/X.

**Parameters:**
| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `content` | str | Yes | - | Tweet content (max 280 chars) |
| `reply_to` | int | No | None | Tweet ID to reply to |
| `save_history` | bool | No | True | Save to history file |

**Returns:**
```python
{
    "status": "success",
    "tweet_id": "1234567890",
    "content": "Tweet content here",
    "tweet_url": "https://twitter.com/user/status/1234567890",
    "timestamp": "2026-03-17T10:30:00",
    "reply_to": None
}
```

### `post_thread()`

Post a thread of connected tweets.

**Parameters:**
| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `tweets` | List[str] | Yes | - | List of tweet contents |
| `save_history` | bool | No | True | Save to history file |

**Returns:**
```python
{
    "status": "success",
    "thread_id": "1234567890",
    "tweet_count": 5,
    "tweet_ids": ["1234567890", "1234567891", ...],
    "thread_url": "https://twitter.com/user/status/1234567890",
    "timestamp": "2026-03-17T10:30:00",
    "tweets": [
        {"tweet_id": "1234567890", "content": "...", "position": 1},
        {"tweet_id": "1234567891", "content": "...", "position": 2},
        ...
    ]
}
```

### `get_history()`

Retrieve tweet history.

**Parameters:**
| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `limit` | int | No | 10 | Max entries to return |
| `tweet_type` | str | No | "all" | Filter: 'tweet', 'thread', 'all' |

**Returns:**
```python
{
    "status": "success",
    "count": 5,
    "history": [...]
}
```

### `get_stats()`

Get tweet statistics.

**Returns:**
```python
{
    "status": "success",
    "total_tweets": 25,
    "total_threads": 3,
    "total_thread_tweets": 12,
    "total_published": 37,
    "history_file": "AI_Employee_Vault/Reports/twitter_history.json"
}
```

---

## History File Format

Tweets are saved to `AI_Employee_Vault/Reports/twitter_history.json`:

```json
[
  {
    "type": "tweet",
    "timestamp": "2026-03-17T10:30:00",
    "data": {
      "status": "success",
      "tweet_id": "1234567890",
      "content": "Tweet content",
      "tweet_url": "https://twitter.com/user/status/1234567890"
    }
  },
  {
    "type": "thread",
    "timestamp": "2026-03-17T11:00:00",
    "data": {
      "status": "success",
      "thread_id": "1234567895",
      "tweet_count": 3,
      "tweets": [...]
    }
  }
]
```

---

## Integration with AI Employee

### With Scheduler

```python
from .claude.skills.twitter_post import TwitterSkill
from scripts.scheduler import run_scheduled_task

twitter = TwitterSkill()

# Schedule daily tweet
def post_daily_update():
    result = twitter.post_tweet(
        content=f"Daily AI Employee Update - {datetime.now().strftime('%Y-%m-%d')} #DailyUpdate"
    )
    return result

# Add to scheduler
# Runs every day at 9:00 AM
```

### With Human Approval

```python
from .claude.skills.twitter_post import TwitterSkill
from .claude.skills.human_approval import check_approval

twitter = TwitterSkill()

# Create approval request
approval_id = create_approval_request(
    action_type="twitter_post",
    data={"content": "Marketing tweet content..."}
)

# Check approval before posting
if check_approval(approval_id):
    result = twitter.post_tweet(content="Marketing tweet content...")
```

### With Content Planner

```python
# Plan and schedule tweets
from .claude.skills.twitter_post import TwitterSkill

twitter = TwitterSkill()

# Read content plan from vault
plan = read_plan("Plan_Social_Media_Campaign.md")

# Execute planned tweets
for tweet_content in plan['tweets']:
    result = twitter.post_tweet(content=tweet_content)
    log_action("tweet_posted", result)
```

---

## Logging

All actions are logged to `logs/social.log`:

```
[2026-03-17 10:30:00] [INFO] [twitter_skill] TwitterSkill initialized
[2026-03-17 10:30:05] [INFO] [twitter_skill] Posting tweet: Exciting news from our AI...
[2026-03-17 10:30:06] [INFO] [twitter_skill] Tweet posted successfully: 1234567890
[2026-03-17 10:30:06] [INFO] [twitter_skill] Saved tweet to history: AI_Employee_Vault/Reports/twitter_history.json
```

---

## Error Handling

| Error | Cause | Solution |
|-------|-------|----------|
| Credentials not configured | Missing env vars | Set TWITTER_* environment variables |
| Tweet too long | Content > 280 chars | Shorten content |
| Authentication failed | Invalid tokens | Regenerate Twitter API tokens |
| Rate limit exceeded | Too many requests | Wait and retry later |
| Duplicate content | Twitter spam filter | Vary content |

---

## Best Practices

1. **Content Length**: Keep tweets under 240 characters for safety margin
2. **Hashtags**: Use 2-3 relevant hashtags per tweet
3. **Timing**: Schedule tweets for optimal engagement times
4. **Threads**: Use threads for longer content (up to 25 tweets)
5. **History**: Always save to history for audit purposes
6. **Approval**: Use human approval for sensitive content

---

## Security Considerations

- Store API credentials in environment variables
- Never commit credentials to version control
- Use OAuth 2.0 when possible
- Implement rate limiting in automated workflows
- Review content before posting (human approval)
- Monitor for API usage limits

---

## Troubleshooting

### Authentication Errors

```bash
# Verify credentials
echo $TWITTER_API_KEY
echo $TWITTER_BEARER_TOKEN

# Test connection
python -c "from .claude.skills.twitter_post import TwitterSkill; t = TwitterSkill(); print(t.get_stats())"
```

### Rate Limiting

Twitter API has rate limits:
- Tweets: 200 per 15 minutes (user context)
- Read: 300 per 15 minutes

Solution: Implement retry logic with exponential backoff.

### Import Errors

```bash
# Install tweepy
pip install tweepy

# Verify installation
python -c "import tweepy; print(tweepy.__version__)"
```

---

## Related Files

| File | Purpose |
|------|---------|
| `.claude/skills/twitter-post/twitter_skill.py` | Main implementation |
| `.claude/skills/twitter-post/SKILL.md` | This documentation |
| `AI_Employee_Vault/Reports/twitter_history.json` | Tweet history |
| `logs/social.log` | Social media logs |

---

## Changelog

| Version | Date | Changes |
|---------|------|---------|
| 1.0.0 | 2026-03-17 | Initial Gold Tier implementation |
