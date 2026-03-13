# Weekly Update Skill

An [Agent Skill](https://agentskills.io) for generating weekly notes from MindNode daily notes, calendar events, and GitHub commits, then populating Salesforce timesheet and Lattice weekly update. Works with Cursor and any tool that supports the Agent Skills open standard.

## What it does

Given a client/project context and a MindNode file with daily notes, this skill:

1. **Gathers inputs** — MindNode "Daily Notes" branch, iCal calendar for the week, GitHub commits (66degrees org)
2. **Generates weekly notes** — Header, intro, daily breakdown (bullets &lt; 255 chars), and personal summary (four questions, first person)
3. **Optionally fills Salesforce** — Copies schedules and populates daily notes (user reviews and submits)
4. **Optionally fills Lattice** — Populates focus, plans, challenges, anything else (user reviews and submits)

Tools run from `~/.cursor/tools/` (mindnode_tool, calendar_tool, salesforce_timesheet, lattice_update). Browser automation uses Playwright to connect to a second Chrome instance via CDP so the user's main browser is untouched.

**When to use:** "Give me my weekly notes", "Weekly summary for [client]", "What did I do this week?", "Fill my timesheet" / "Populate Lattice".

---

## Prerequisites

Before installing the skill or running setup, ensure you have everything below. The skill does **not** require any MCP (Model Context Protocol) servers; the agent runs shell commands that invoke the Python tools directly.

### System & apps

| Requirement | Purpose |
|-------------|---------|
| **Python 3** | Run the tools and setup script; recommend 3.10+ |
| **Cursor** | So the skill can be linked under `~/.cursor/skills/` |
| **Chrome** | Required for Salesforce and Lattice. Must be installed (e.g. `/Applications/Google Chrome.app` on macOS). The tools launch a second Chrome instance with CDP and use a copy of your profile so you're already logged in. |
| **GitHub CLI (`gh`)** | Must be installed and logged in (`gh auth login`). The skill uses it to get your username and fetch commits for the week. |

### Directory: `~/.cursor/tools/`

The workflow expects a dedicated tools directory with a virtualenv and these scripts:

| File | Purpose |
|------|---------|
| `mindnode_tool.py` | Read MindNode files (Daily Notes branch). Stdlib only (plistlib). |
| `calendar_tool.py` | Fetch iCal feed for the week; configured by setup. |
| `salesforce_timesheet.py` | PSE time entry: view schedules, copy week, fill daily notes. Uses Playwright + CDP. |
| `lattice_update.py` | Lattice weekly check-in: fill focus, plans, challenges, anything else. Uses Playwright + CDP. |
| `browser_helper.py` | Shared helper: sync Chrome profile to `~/.chrome-automation/`, launch Chrome with `--remote-debugging-port=9222`, connect via Playwright’s `connect_over_cdp`. |

Create the venv and install dependencies:

```bash
mkdir -p ~/.cursor/tools
cd ~/.cursor/tools
python3 -m venv .venv
.venv/bin/pip install playwright icalendar requests
.venv/bin/playwright install
```

- **playwright** — Used by `salesforce_timesheet.py` and `lattice_update.py` to connect to Chrome via CDP and automate the pages. The tools do **not** launch a Playwright-managed browser; they connect to an existing Chrome instance (or launch Chrome with CDP and then connect). The `playwright install` step installs browser drivers Playwright may use; for CDP-only use, `pip install playwright` is often enough.
- **icalendar** — Parse iCal feeds in `calendar_tool.py`.
- **requests** — Fetch the iCal URL in `calendar_tool.py`.

Copy or symlink the five Python files above into `~/.cursor/tools/`. On first run of Salesforce or Lattice, the browser helper copies your default Chrome profile into `~/.chrome-automation/` so the automation window is already logged in.

### What is not required

- **MCP** — No MCP servers are used. The skill instructs the agent to run the Python tools via Bash.
- **Node.js** — Not required for this skill. (You may see a Node deprecation warning from Playwright’s internals; it can be ignored.)

---

## Setup (one-time, per user)

**Only the iCal feed is per-user.** GitHub username is read automatically from `gh` (logged-in user). The Lattice URL is the same for everyone and lives in the repo (see `org-defaults.md`).

### 1. Clone the repo

```bash
git clone <your-repo-url> weekly-update-skill
cd weekly-update-skill
```

### 2. Run the setup script (iCal only)

From the repo root:

```bash
python3 scripts/setup.py
```

You will be prompted once:

| Prompt | What it does |
|--------|--------------|
| **iCal feed URL** | Passed to `calendar_tool.py --setup` so weekly notes can include your calendar. Get it from Google Calendar (Settings → your calendar → "Secret address in iCal format"), Outlook (Publish calendar → ICS link), or Apple Calendar. |

The script configures the calendar tool in `~/.cursor/tools/.calendar_config.json`. You can run setup again to change your iCal URL, or run manually:

```bash
~/.cursor/tools/.venv/bin/python ~/.cursor/tools/calendar_tool.py --setup "https://..."
```

### 3. Install the skill into Cursor

**Symlink (recommended):**

```bash
ln -s "$(pwd)" ~/.cursor/skills/weekly-update
```

**Or copy:**

```bash
cp -r . ~/.cursor/skills/weekly-update
```

Cursor loads skills from `~/.cursor/skills/`. The entry point is `SKILL.md`.

### 4. Optional: rule for discovery

**File:** `~/.cursor/rules/weekly-notes.mdc`

```yaml
---
description: Generate weekly notes by combining MindNode daily notes and calendar events. Use when the user asks for weekly notes, weekly summary, or what they did this week.
---
Use the weekly-update skill (~/.cursor/skills/weekly-update) for the full workflow.
```

---

## File structure

```
.
├── SKILL.md           # Skill definition (entry point)
├── workflow.md        # Full step-by-step workflow
├── org-defaults.md    # Shared Lattice URL (same for everyone)
├── README.md          # This file
├── .gitignore
└── scripts/
    └── setup.py       # One-time setup: iCal feed only
```

---

## Configuration reference

| Item | How it's set |
|------|----------------|
| **iCal feed** | Per user. Run `python3 scripts/setup.py` or `calendar_tool.py --setup "<url>"`. Stored in `~/.cursor/tools/.calendar_config.json`. |
| **GitHub username** | Automatic. The skill uses `gh api user --jq '.login'` (logged-in `gh` user). |
| **Lattice URL** | Same for everyone. Edit `org-defaults.md` in the repo; the workflow reads it from the skill directory. |
| **Salesforce / Lattice login** | Chrome profile is copied to `~/.chrome-automation/` by the browser helper; automation uses that profile so you're already logged in. |
