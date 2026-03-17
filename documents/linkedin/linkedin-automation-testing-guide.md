# LinkedIn Automation — Manual Testing

## 1. Run Automated Tests

```bash
python -m pytest tests/test_linkedin.py -v --tb=short
```

Expected: 74 passed, 1 skipped.

## 2. Check Config & Schedule

```bash
python -c "
import sys; sys.path.insert(0,'scripts')
from linkedin_poster import load_config, load_state, should_generate_post
config = load_config()
print('Topics:', len(config['content_topics']))
print('Times:', config['posting_schedule']['preferred_times'])
print('Schedule:', should_generate_post(config, load_state()))
"
```

## 3. Generate a Draft

```bash
echo trigger > Plans/generate_linkedin_post.trigger
python scripts/linkedin_poster.py
# Ctrl+C after draft is created
ls Plans/LinkedInPost_*.md
```

## 4. Approve (Dry Run)

```bash
# Check the APPROVE box in the plan file, then:
LINKEDIN_DRY_RUN=true python scripts/approval_watcher.py
# Should print [DRY RUN] and move plan to Done/
```

## 5. Approve (Real Post)

```bash
# Generate a new draft (step 3), check APPROVE, then:
python scripts/approval_watcher.py
# Post appears on LinkedIn, plan moves to Done/
```

## 6. Verify Analytics

```bash
python scripts/linkedin_analytics.py
```

## 7. Full System

```bash
start_system.bat
# Opens 6 watcher windows including LinkedIn Poster
```

## Quick Smoke Test

```bash
python -m pytest tests/test_linkedin.py -v --tb=short
python scripts/linkedin_analytics.py
python -c "import sys;sys.path.insert(0,'scripts');from linkedin_poster import load_config;print('OK:',len(load_config()['content_topics']),'topics')"
```
