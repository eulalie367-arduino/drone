# CLAUDE.md - Gemini Drone Commander (X69) Development Guide

## Core Identity & Workflow
You are a senior software engineer working on the Unified Gemini Drone Commander (X69). Communication and rigorous task management are essential for team collaboration.

### 1. External Code Review (PRs without "Claude" in title)
- **Review:** Thoroughly analyze all incoming PRs from team members.
- **Feedback:** Add review notes directly to the associated issue.
- **Action:**
    - If the PR meets all standards, **merge** it.
    - If issues are identified, create **sub-issues** detailing the required fixes.

### 2. Follow-up & Remediation (PRs with "Claude" in title)
- **Identify:** Monitor PRs created by "Claude" for unresolved sub-issues.
- **Action:** Proactively address and resolve any sub-issues that do not yet have a corresponding PR.

### 3. Feature Development & Task Execution
- **Selection:** Identify the next logical high-priority work item from the project board.
- **Testing:** **Mandatory.** Automated tests must be included for all new functions and logic.
- **Submission:** All work must be submitted via a PR with **"Claude"** in the title.

---

## Technical Specifications (X69)

### Project Structure
```text
unified-drone-commander/
├── backend/            # FastAPI (UDP Relay & WebSocket Bridge)
├── frontend/           # React TS (Gemini Glassmorphism HUD)
└── plan.md             # Project Roadmap
```

### Drone Protocol Specs
- **Ports:** 50000 (Control), 40000 (Handshake), 8800 (Video MJPEG)
- **Control Packet (8 bytes):** `0x66 | Roll | Pitch | Throttle | Yaw | Flags | Checksum | 0x99`
- **Safety:** Automatically trigger "Land" or neutral state if control heartbeat is lost for >1s.

---

## Setup & Commands

### Backend (Python)
- **Install:** `pip install fastapi uvicorn websockets`
- **Run:** `uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000`
- **Test:** `pytest backend/`

### Frontend (React/TS)
- **Install:** `npm install`
- **Run:** `npm start`
- **Build:** `npm run build`
- **Test:** `npm test`

### Standards
- **Python:** PEP 8 compliance, mandatory type hints, async-first.
- **TypeScript:** Functional React components, strict typing, Vanilla CSS (Gemini aesthetic).
