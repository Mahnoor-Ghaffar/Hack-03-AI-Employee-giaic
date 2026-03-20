# Social Media Agent Skill (Facebook + Instagram)

**Tier:** Gold
**Version:** 1.0.0
**Author:** AI Employee Hackathon Team

---

## Overview

The Social Media Agent Skill provides Facebook and Instagram posting capabilities to the AI Employee system via the Meta Graph API. All actions are logged to `logs/social.log` for audit purposes.

---

## Capabilities

- **Facebook Posting**
  - `post_facebook()` - Post text, images, and links to Facebook Pages
  - Scheduled posting support
  - Photo uploads

- **Instagram Posting**
  - `post_instagram()` - Post images with captions
  - `post_instagram_carousel()` - Post multiple images (2-10)
  - Cross-posting to Facebook

- **Cross-Platform**
  - `post_to_both()` - Post to both platforms simultaneously
  - Unified logging and error handling

- **Logging**
  - All actions logged to `logs/social.log`
  - JSON-formatted log entries
  - Timestamp and status tracking

---

## Installation

### Prerequisites

1. Meta Developer Account
2. Facebook Page (for Facebook posting)
3. Instagram Business Account connected to Facebook Page
4. Python 3.8+
5. Required package: `requests`

### Setup

```bash
# Install requests
pip install requests

# Create Meta app at https://developers.facebook.com/
# Get Page Access Token with required permissions
```

### Required Permissions

- **Facebook**: `pages_manage_posts`, `pages_read_engagement`, `publish_to_groups`
- **Instagram**: `instagram_basic`, `instagram_content_publish`, `pages_read_engagement`

### Environment Variables

```bash
# Facebook
FACEBOOK_PAGE_ID=your_page_id
FACEBOOK_ACCESS_TOKEN=your_page_access_token

# Instagram (must be Business account connected to Facebook Page)
INSTAGRAM_BUSINESS_ACCOUNT_ID=your_instagram_business_id
INSTAGRAM_ACCESS_TOKEN=your_access_token

# Optional
IMAGE_CDN_BASE=https://your-cdn.com/images
LOG_LEVEL=INFO
SOCIAL_LOG_FILE=logs/social.log
```

---

## Usage

### Post to Facebook

```python
from .claude.skills.social_meta import SocialMediaSkill

social = SocialMediaSkill()

# Text post
result = social.post_facebook(
    content="Exciting news from our company! #update"
)

# Post with image
result = social.post_facebook(
    content="Check out our new product!",
    image_path="images/product.jpg"
)

# Post with link
result = social.post_facebook(
    content="Read our latest blog post",
    link="https://example.com/blog"
)

# Scheduled post
result = social.post_facebook(
    content="Tomorrow's event reminder",
    scheduled_time="2026-03-18T09:00:00+0000"
)
```

### Post to Instagram

```python
# Single image post
result = social.post_instagram(
    content="Beautiful product photo! #instagram #business",
    image_path="images/product.jpg"
)

# With location
result = social.post_instagram(
    content="Great day at the office!",
    image_path="images/office.jpg",
    location_id="123456789"
)

# Share to Facebook too
result = social.post_instagram(
    content="Cross-platform post!",
    image_path="images/post.jpg",
    share_to_facebook=True
)
```

### Post Carousel to Instagram

```python
# Multiple images (2-10)
result = social.post_instagram_carousel(
    content="Product showcase - swipe to see more!",
    image_paths=[
        "images/product1.jpg",
        "images/product2.jpg",
        "images/product3.jpg"
    ]
)
```

### Post to Both Platforms

```python
result = social.post_to_both(
    content="Big announcement across all platforms!",
    image_path="images/announcement.jpg",
    facebook_link="https://example.com/announcement"
)

print(f"Facebook: {result['facebook']['status']}")
print(f"Instagram: {result['instagram']['status']}")
```

### Get Account Info

```python
info = social.get_account_info()
print(f"Facebook Page: {info['facebook']['name']}")
print(f"Instagram: @{info['instagram']['username']}")
```

---

## API Reference

### `post_facebook()`

Post to Facebook Page.

**Parameters:**
| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `content` | str | No* | "" | Post text |
| `image_path` | str | No | None | Path to image file |
| `link` | str | No | None | URL to share |
| `scheduled_time` | str | No | None | ISO 8601 datetime |

*At least one of content, image_path, or link is required

**Returns:**
```python
{
    "status": "success",
    "platform": "facebook",
    "post_id": "page_id_post_id",
    "post_url": "https://facebook.com/...",
    "content": "Post content...",
    "has_image": False,
    "has_link": False,
    "scheduled": False,
    "timestamp": "2026-03-17T10:30:00"
}
```

### `post_instagram()`

Post to Instagram Business Account.

**Parameters:**
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `content` | str | Yes | Caption (max 2200 chars) |
| `image_path` | str | Yes | Path to image (required) |
| `location_id` | str | No | Facebook Location ID |
| `share_to_facebook` | bool | No | Cross-post to Facebook |

**Returns:**
```python
{
    "status": "success",
    "platform": "instagram",
    "media_id": "media_id",
    "post_url": "https://instagram.com/p/...",
    "content": "Caption...",
    "image_path": "images/photo.jpg",
    "share_to_facebook": False,
    "timestamp": "2026-03-17T10:30:00"
}
```

### `post_instagram_carousel()`

Post multiple images to Instagram.

**Parameters:**
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `content` | str | Yes | Caption |
| `image_paths` | list | Yes | List of 2-10 image paths |
| `share_to_facebook` | bool | No | Cross-post |

### `post_to_both()`

Post to both Facebook and Instagram.

**Parameters:**
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `content` | str | Yes | Post content |
| `image_path` | str | No | Image path |
| `facebook_link` | str | No | Link for Facebook |

### `get_account_info()`

Get connected account information.

**Returns:**
```python
{
    "facebook": {
        "configured": True,
        "page_id": "123456789...",
        "name": "My Business Page"
    },
    "instagram": {
        "configured": True,
        "account_id": "987654321...",
        "username": "mybusiness",
        "name": "My Business"
    },
    "timestamp": "2026-03-17T10:30:00"
}
```

---

## Logging

All actions are logged to `logs/social.log`:

```
[2026-03-17 10:30:00] [INFO] [social_media_skill] SocialMediaSkill initialized
[2026-03-17 10:30:05] [INFO] [social_media_skill] Posting to Facebook: Exciting news from our...
[2026-03-17 10:30:06] [INFO] [social_media_skill] facebook_post: {
  "status": "success",
  "platform": "facebook",
  "post_id": "123456_789012",
  ...
}
[2026-03-17 10:30:10] [INFO] [social_media_skill] Posting to Instagram: Beautiful product photo...
[2026-03-17 10:30:15] [INFO] [social_media_skill] instagram_post: {
  "status": "success",
  "platform": "instagram",
  "media_id": "17841400123456789",
  ...
}
```

---

## Integration with AI Employee

### With Scheduler

```python
from .claude.skills.social_meta import SocialMediaSkill

social = SocialMediaSkill()

# Daily social media post
def post_daily_update():
    result = social.post_to_both(
        content=f"Daily update from AI Employee! #Day{day_count} #Automation",
        image_path="images/daily_update.jpg"
    )
    return result
```

### With Content Planner

```python
# Execute planned social media content
from .claude.skills.social_meta import SocialMediaSkill

social = SocialMediaSkill()
plan = read_plan("Plan_Social_Media_Week.md")

for post in plan['posts']:
    if post['platform'] == 'facebook':
        social.post_facebook(
            content=post['content'],
            image_path=post.get('image')
        )
    elif post['platform'] == 'instagram':
        social.post_instagram(
            content=post['content'],
            image_path=post['image']
        )
```

### With Human Approval

```python
from .claude.skills.social_meta import SocialMediaSkill
from .claude.skills.human_approval import check_approval

social = SocialMediaSkill()

# Create approval request for sensitive content
approval_id = create_approval_request(
    action_type="social_media_post",
    data={
        "platform": "facebook",
        "content": "Important company announcement..."
    }
)

if check_approval(approval_id):
    social.post_facebook(content="Important company announcement...")
```

---

## Error Handling

| Error | Cause | Solution |
|-------|-------|----------|
| Page ID not configured | Missing env var | Set FACEBOOK_PAGE_ID |
| Access token expired | Token validity period | Generate new token |
| Image not found | Invalid path | Check file path |
| Image URL required | Instagram needs public URL | Upload to CDN, set IMAGE_CDN_BASE |
| Permission denied | Missing app permissions | Add required permissions in Meta Developer |
| Rate limit exceeded | Too many requests | Wait and retry |

---

## Important Notes

### Instagram Image Requirements

Instagram API requires images to be hosted on a **publicly accessible URL**. Local file paths won't work directly.

**Solutions:**
1. Upload to cloud storage (AWS S3, Google Cloud Storage)
2. Use a CDN (Cloudinary, Imgur)
3. Host on your website

```bash
# Set CDN base URL
export IMAGE_CDN_BASE="https://cdn.yourcompany.com"
```

### Token Expiration

- Facebook Page Access Tokens: 60 days (extendable)
- Instagram Access Tokens: Same as Facebook

**To extend token:**
1. Go to Meta Developer Tools
2. Use Access Token Debugger
3. Click "Extend Access Token"

---

## Security Considerations

- Store tokens in environment variables
- Never commit tokens to version control
- Use app secrets for token generation
- Implement token refresh mechanism
- Monitor API usage for anomalies
- Review posted content before publishing

---

## Troubleshooting

### Check Account Connection

```bash
python -c "
from .claude.skills.social_meta import SocialMediaSkill
social = SocialMediaSkill()
print(social.get_account_info())
"
```

### Test Facebook Posting

```python
social = SocialMediaSkill()
result = social.post_facebook(content="Test post")
print(result)
```

### Common Issues

1. **Instagram not posting**: Ensure Business account is connected to Facebook Page
2. **Image upload fails**: Verify image is accessible via public URL
3. **Permission errors**: Check app permissions in Meta Developer Dashboard

---

## Related Files

| File | Purpose |
|------|---------|
| `.claude/skills/social-meta/social_skill.py` | Main implementation |
| `.claude/skills/social-meta/SKILL.md` | This documentation |
| `logs/social.log` | Social media activity log |

---

## Changelog

| Version | Date | Changes |
|---------|------|---------|
| 1.0.0 | 2026-03-17 | Initial Gold Tier implementation |
