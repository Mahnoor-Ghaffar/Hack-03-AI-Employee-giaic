# Personal AI Employee - Bronze Tier

> **Your life and business on autopilot. Local-first, agent-driven, human-in-the-loop.**

[![Status](https://img.shields.io/badge/status-bronze%20tier%20complete-brightgreen)]()
[![Python](https://img.shields.io/badge/python-3.13+-blue)]()
[![Claude Code](https://img.shields.io/badge/Claude%20Code-enabled-orange)]()

A **Personal AI Employee** built with Claude Code and Obsidian that proactively manages your personal and business affairs 24/7. This is a **Bronze Tier** implementation - a fully functional foundation for an autonomous digital FTE (Full-Time Equivalent).

---

## 🏆 Bronze Tier Status: COMPLETE

All 5 Bronze Tier requirements implemented and tested:

| # | Requirement | Status |
|---|-------------|--------|
| 1 | Obsidian vault with Dashboard.md and Company_Handbook.md | ✅ |
| 2 | One working Watcher script (File System) | ✅ |
| 3 | Claude Code reading/writing to vault | ✅ |
| 4 | Basic folder structure: /Inbox, /Needs_Action, /Done | ✅ |
| 5 | All AI functionality as Agent Skills | ✅ |

---

## 🚀 Quick Start

### Prerequisites
- Python 3.13+
- Claude Code subscription
- Obsidian (optional, for viewing vault)

### Installation

```bash
# Clone the repository
git clone https://github.com/Mahnoor-Ghaffar/Hack-03-AI-Employee-giaic.git
cd Hack-03-AI-Employee-giaic

# Create and activate virtual environment
python -m venv venv
venv\Scripts\activate  # Windows
# source venv/bin/activate  # Mac/Linux

# Install dependencies
pip install watchdog
```

### Usage

**Option 1: Automated File Watching**
```bash
# Terminal 1: Start file watcher
python filesystem_watcher.py

# Terminal 2: Drop files into drop_zone/ folder
# Then run Claude Code
claude
```

**Option 2: Process Tasks Directly**
```bash
python process_tasks.py
```

---

## 📁 Project Structure

```
Hack-03-AI-Employee-giaic/
├── AI_Employee_Vault/          # Obsidian vault (Brain & Memory)
│   ├── Inbox/                  # Raw incoming items
│   ├── Needs_Action/           # Tasks pending processing
│   ├── Done/                   # Completed tasks
│   ├── Dashboard.md            # Real-time status overview
│   └── Company_Handbook.md     # Rules & preferences
├── drop_zone/                  # Drop files here for auto-processing
├── skills/                     # Agent Skills for Claude Code
│   ├── vault_skills.py         # Vault operations (7 functions)
│   └── process_file_skill.py   # File processing skill
├── filesystem_watcher.py       # Monitors drop_zone folder
├── process_tasks.py            # Automated task processor
├── test_vault_skills.py        # Test suite
├── .claude/mcp.json            # Claude Code MCP config
└── QUICKSTART.md               # Detailed user guide
```

---

## 🛠️ Available Vault Skills

| Skill | Description |
|-------|-------------|
| `list_pending_tasks()` | List all tasks in Needs_Action |
| `read_task("file.md")` | Read a specific task file |
| `write_response("file.md", "response")` | Add AI response to task |
| `move_to_done("file.md", "summary")` | Move completed task to Done |
| `get_task_summary()` | Get formatted summary of pending tasks |
| `update_dashboard("Section", "Content")` | Update Dashboard.md |

---

## 🔄 Workflow

```
┌─────────────┐     ┌──────────────┐     ┌─────────────┐     ┌─────────────┐
│  drop files │ ──▶ │ File Watcher │ ──▶ │ Needs_Action │ ──▶ │ Claude Code │
│  in drop_zone│     │ (background) │     │   folder     │     │  + Skills   │
└─────────────┘     └──────────────┘     └──────────────┘     └─────────────┘
                                                                    │
                                                                    ▼
┌─────────────┐     ┌──────────────┐     ┌─────────────┐     ┌─────────────┐
│  Dashboard  │ ◀── │   Update     │ ◀── │   Done      │ ◀── │  Process    │
│   Updated   │     │   Status     │     │   Folder    │     │  & Move     │
└─────────────┘     └──────────────┘     └──────────────┘     └─────────────┘
```

---

## 📋 Example Use Cases

### 📧 Process Client Emails
1. Save email as `.md` or `.txt` in `drop_zone/`
2. File watcher copies to `Needs_Action/`
3. Claude reads with `read_task()`, drafts response
4. Move to `Done/` with `move_to_done()`

### 📄 Process Documents
1. Drop PDF/DOCX/TXT in `drop_zone/`
2. Claude summarizes content with skills
3. Extracts action items and recommendations

### 📊 Generate Reports
```bash
python -c "from skills.vault_skills import get_task_summary; print(get_task_summary())"
```

---

## 🧪 Testing

```bash
# Run test suite
python test_vault_skills.py
```

**Expected Output:**
```
==================================================
Testing AI Employee Vault Skills
==================================================

[TEST 1] Listing pending tasks...
Found 2 pending task(s)

[TEST 2] Getting task summary...
**Pending Tasks:** 2

[TEST 3] Reading a task...
Reading: email_client_proposal_review.md

==================================================
All tests completed successfully!
==================================================
```

---

## 📖 Documentation

| Document | Description |
|----------|-------------|
| [`QUICKSTART.md`](QUICKSTART.md) | Getting started guide |
| [`BRONZE_TIER_COMPLETE.md`](BRONZE_TIER_COMPLETE.md) | Bronze tier completion report |
| [`skills/SKILL.md`](skills/SKILL.md) | Agent skills documentation |
| [Hackathon Doc](Personal%20AI%20Employee%20Hackathon%200_%20Building%20Autonomous%20FTEs%20in%202026.md) | Full hackathon requirements |

---

## 🎯 Next Steps (Silver Tier)

To advance to **Silver Tier**, add:
- [ ] Gmail Watcher for email monitoring
- [ ] WhatsApp Watcher for message monitoring
- [ ] MCP server for sending emails
- [ ] Plan.md creation by Claude
- [ ] Human-in-the-loop approval workflow
- [ ] Scheduled tasks via Task Scheduler

---

## 🏗️ Architecture

| Component | Role | Technology |
|-----------|------|------------|
| **Brain** | Reasoning engine | Claude Code |
| **Memory/GUI** | Dashboard & knowledge base | Obsidian |
| **Senses** | File/system monitoring | Python Watchers |
| **Hands** | External actions | MCP Servers |
| **Persistence** | Autonomous loops | Ralph Wiggum Pattern |

---

## 📊 Digital FTE vs Human FTE

| Feature | Human FTE | Digital FTE |
|---------|-----------|-------------|
| Availability | 40 hours/week | 168 hours/week (24/7) |
| Monthly Cost | $4,000 - $8,000+ | $500 - $2,000 |
| Ramp-up Time | 3-6 months | Instant |
| Consistency | 85-95% accuracy | 99%+ consistency |
| Scaling | Linear | Exponential |

---

## 🤝 Contributing

This project is part of the **GIAIC Hackathon 0: Building Autonomous FTEs in 2026**.

Join the weekly meetings:
- **When:** Wednesdays at 10:00 PM PKT
- **Zoom:** [Link in hackathon doc](Personal%20AI%20Employee%20Hackathon%200_%20Building%20Autonomous%20FTEs%20in%202026.md)

---

## 📄 License

This project is part of the GIAIC hackathon series.

---

## 🙏 Acknowledgments

- [Claude Code](https://claude.com/claude-code) - Reasoning engine
- [Obsidian](https://obsidian.md/) - Knowledge base
- [Model Context Protocol](https://modelcontextprotocol.io/) - Action framework

---

**Built with ❤️ for the future of autonomous AI employees**
