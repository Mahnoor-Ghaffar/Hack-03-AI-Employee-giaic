# LinkedIn Automation — System Overview

## What It Does

- **Automatically drafts LinkedIn posts** on a configurable schedule (e.g., Mon-Fri at 9am, 12pm, 5pm)
- **Never posts without your approval** — every draft goes to `Plans/` folder in Obsidian where you check APPROVE, EDIT, or REJECT
- **Publishes approved posts** to your real LinkedIn profile via the LinkedIn REST API, including image uploads
- **Tracks everything locally** — post history, analytics, image usage, topic/format rotation

---

## How the Pipeline Works (End-to-End)

1. **`linkedin_poster.py`** runs as a watcher loop, checking the schedule every 5 minutes
2. When it's time to post, it picks a **topic** (avoids last 3 used) and a **format** (avoids last 2 used)
3. It selects an **image** from `assets/linkedin-images/` using LRU (least recently used) logic
4. It invokes the **`/draft-linkedin-post` Claude skill** which:
   - Searches the web for current trends on the topic
   - Generates a post in the chosen format (story, listicle, question, or hot_take)
   - Creates a plan file in `Plans/LinkedInPost_YYYYMMDD_HHMMSS.md`
5. **You review** the plan in Obsidian and check one of:
   - `[x] APPROVE` — publish as-is
   - `[x] EDIT` — you modify the post text/image below, then it publishes your version
   - `[x] REJECT` — discard, moves to Done/
6. **`approval_watcher.py`** detects your checkbox, calls `linkedin_post.py` to publish
7. If an image is attached, it does a **3-step upload**: initialize upload -> PUT binary -> use the image URN in the post
8. After publishing, it writes a record to `linkedin_analytics.json` and moves the plan to `Done/`

---

## Key Files

| File | Role |
|------|------|
| `scripts/linkedin_poster.py` | Main watcher — schedule checking, topic/format/image selection, draft generation |
| `scripts/linkedin_post.py` | Direct LinkedIn API publisher — handles text posts and image uploads |
| `scripts/linkedin_auth.py` | One-time OAuth helper — gets your LinkedIn access token |
| `scripts/approval_watcher.py` | Monitors Plans/ for approved posts, sends them, writes analytics |
| `scripts/linkedin_analytics.py` | CLI tool to print posting stats from local analytics JSON |
| `scripts/linkedin_config.json` | All configuration — schedule, topics, image categories, business context |
| `scripts/posted_linkedin.json` | State file — post history, format history, last draft time |
| `scripts/linkedin_analytics.json` | Analytics records — one entry per published post |
| `.claude/skills/draft-linkedin-post/SKILL.md` | The Claude skill that generates post content |
| `assets/linkedin-images/` | Image library organized by category (ai/, coding/, general/) |

---

## Scheduling System

- **Global preferred times**: e.g., `["09:00", "12:00", "17:00"]` — checked with a +/-10 minute window
- **Per-day overrides**: e.g., `{"Monday": ["09:00"], "Friday": ["17:00"]}` — overrides global times for specific days
- **Active days**: only drafts on configured weekdays (default: Mon-Fri)
- **Max posts per day**: default 1 — won't draft again if already posted today
- **Minimum interval**: default 24 hours between drafts
- **Catch-up logic**: if the watcher was offline and missed a window, it generates a catch-up draft within 2 hours of the missed time
- **Timezone support**: configurable via `posting_schedule.timezone` (e.g., `"Asia/Karachi"`)

---

## Content Generation

- **5 topics** rotate using recency-weighted random selection (avoids last 3)
- **4 format types** rotate (avoids last 2):
  - `story` — personal narrative arc
  - `listicle` — numbered tips/insights
  - `question` — provocative question + discussion
  - `hot_take` — bold contrarian opinion
- **Web search** is performed before generating to find current trends
- **Post rules**: max 1300 characters, 3-5 hashtags, call-to-action at end, hook in first sentence

---

## Image System

- Images stored in `assets/linkedin-images/{category}/` (e.g., ai/, coding/, general/)
- Each topic maps to a category via `topic_image_categories` in config
- **LRU selection**: picks the image used longest ago, tracked in `.last_used.json`
- Image path is passed through the entire pipeline: skill -> plan file -> approval watcher -> LinkedIn API
- User can override the image in the plan file under `### Modified Image`
- If image upload fails, it gracefully falls back to a text-only post

---

## Human-In-The-Loop (HITL) Approval

- Plan files use Obsidian-compatible markdown with YAML frontmatter
- Three checkboxes: APPROVE, EDIT, REJECT
- EDIT mode lets you:
  - Rewrite the post under `### Modified Post`
  - Swap the image under `### Modified Image`
- Plan file includes metadata: character count, read time, hashtag count, format type
- Rejected plans move to Done/ without publishing

---

## Authentication

- Uses LinkedIn OAuth 2.0 with scopes: `openid profile email w_member_social`
- Token stored at `~/.linkedin-mcp/tokens/token.json`
- Run `python scripts/linkedin_auth.py` to authenticate (opens browser, captures callback)
- `r_member_postAnalytics` scope is NOT available for standalone apps — analytics is local-only

---

## Analytics (Local-Only)

- Every published post gets a record in `scripts/linkedin_analytics.json` with:
  - Post ID, publish date, topic, format type, image used, visibility, source file
- Run `python scripts/linkedin_analytics.py` to see:
  - Total posts, posts by topic, posts by format, image usage ratio, posting frequency, last 5 posts
- No LinkedIn API calls for analytics — purely tracks what you've posted locally

---

## Return Signatures (For Developers)

| Function | Returns |
|----------|---------|
| `generate_draft(topic, config, format_type)` | `(success: bool, image_path: str)` |
| `send_linkedin_post(content, visibility, image_path)` | `(success: bool, error: str\|None, post_id: str\|None)` |
| `pick_topic(config, state)` | `str` (topic name) |
| `pick_format(state)` | `str` (format type) |
| `select_image(topic, config)` | `str` (absolute path or empty string) |
| `should_generate_post(config, state)` | `(should: bool, reason: str)` |
| `check_missed_windows(config, state)` | `bool` |

---

## Manual Trigger

- Create a file `Plans/generate_linkedin_post.trigger` to force an immediate draft
- The watcher detects it, removes it, and generates a post regardless of schedule

---

## Test Coverage

- **75 tests** in `tests/test_linkedin.py` covering:
  - Config loading, state tracking, schedule logic, trigger file
  - Topic rotation (recency-weighted), format rotation
  - Catch-up logic, per-day scheduling, timezone handling
  - Image selection (LRU), plan file parsing (image/format fields)
  - LinkedIn sending (3-tuple returns), plan processing, analytics writing
- Run: `python -m pytest tests/test_linkedin.py -v`
