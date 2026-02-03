# Clawdbot Monorepo

**Version:** 1.0.0
**Owner:** Phatchakrit (Qoozzz)
**Architecture:** Monorepo Structure (Option C)
**Philosophy:** Oracle Philosophy (Nothing deleted, Patterns over intentions, External brain)

---

## 📊 Overview

Centralized monorepo for AI assistant infrastructure, trading systems, and knowledge management.

### Design Principles
- **Scalable:** Easy to add new projects
- **Organized:** Clear separation of concerns
- **Shareable:** Patterns reusable across projects
- **Version Controlled:** Full git history
- **Secure:** Sensitive data never committed

---

## 🗂️ Directory Structure

```
clawd-monorepo/
├── .gitignore                 # Strict gitignore (no secrets)
├── README.md                  # This file
├── docs/                      # Core documentation
│   ├── AGENTS.md             # Knowledge index
│   ├── SOUL.md              # Oracle philosophy
│   ├── IDENTITY.md           # Puffin's identity
│   ├── USER.md              # About Qoozzz
│   ├── TOOLS.md             # Local setup notes
│   ├── HEARTBEAT.md         # Moltbook heartbeat
│   └── schedule.md          # Calendar and tasks
├── patterns/                  # Reusable knowledge patterns
│   ├── trading-patterns/     # Trading strategies & risk mgmt
│   ├── youtube-patterns/     # YouTube content creation
│   ├── notion-patterns/      # Notion integration
│   ├── server-patterns/      # Home server setup
│   ├── ai-patterns/         # AI content tools
│   └── interior-patterns/    # Interior design
├── projects/                  # Active development projects
│   └── trading-system/       # Algorithmic trading (PRIMARY)
├── dashboards/                # Web dashboards
│   └── trading-dashboard/   # Next.js trading UI
├── puffin-profile/            # Puffin documentation (for Gemini Gem)
│   ├── README.md
│   ├── IDENTITY.md
│   ├── CAPABILITIES.md
│   ├── WORKFLOW.md
│   ├── PROMPT-GUIDE.md
│   ├── ARCHITECTURE.md
│   └── BEST-PRACTICES.md
├── scripts/                   # Utility scripts
│   └── (to be populated)
└── config/                    # Configuration files (no secrets)
    └── (to be populated)
```

---

## 🎯 Project Priorities

### 🔴 Primary (Active)
- **Trading System** (`projects/trading-system/`)
  - Algorithmic trading (Binance API + MT5)
  - Zone/Grid Trading strategies
  - Risk Management
  - Supabase integration

### 🟡 Secondary (Active)
- **Trading Dashboard** (`dashboards/trading-dashboard/`)
  - Next.js frontend
  - Real-time monitoring
  - Trade visualization

### 🟢 Tertiary (Reference)
- **Patterns** (`patterns/`) - Reusable knowledge
- **Documentation** (`docs/`) - Core reference
- **Puffin Profile** (`puffin-profile/`) - Agent documentation

---

## 🔐 Security Policy

### Never Commit
- ❌ API keys
- ❌ Database passwords
- ❌ Environment files (.env)
- ❌ Secrets folder
- ❌ Private keys
- ❌ Session files

### Use Environment Variables
```bash
# Example: .env.local (never committed)
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_ANON_KEY=your-anon-key
BOT_TOKEN=your-bot-token
```

### Config Management
- Use `config/` for safe configuration
- Use environment variables for secrets
- Never hard-code credentials

---

## 🚀 Getting Started

### 1. Clone Repository
```bash
git clone https://github.com/your-username/clawd-monorepo.git
cd clawd-monorepo
```

### 2. Setup Environment
```bash
# Copy example env files (if available)
cp .env.example .env.local

# Edit .env.local with your values
nano .env.local
```

### 3. Install Dependencies
```bash
# Trading Dashboard
cd dashboards/trading-dashboard
npm install
```

### 4. Start Services
```bash
# Trading Dashboard
cd dashboards/trading-dashboard
npm run dev

# Access at http://localhost:3000
```

---

## 📋 Workflow

### Trading System Development
1. **Puffin (Architect)** plans features
2. **OpenCode (Builder)** implements
3. **Puffin** reviews and validates
4. **Puffin** logs decisions to Supabase
5. **OpenCode** logs reports to Supabase
6. **Both** update relevant patterns

### Pattern Sharing
- Use `patterns/` for reusable knowledge
- Reference patterns in project code
- Update patterns when improvements found

### Version Control
- Use feature branches for new features
- Use descriptive commit messages
- Document decisions in commit messages

---

## 🤝 Collaboration

### Roles
- **Puffin (Architect):** Orchestration, planning, review
- **OpenCode (Builder):** Implementation, testing, reporting
- **Qoozzz (Owner):** Decision-making, approval, direction

### Communication
- See `/projects/trading-system/logs/interaction-logs.md`
- Use Supabase `agent_interactions` for structured logs
- Use Supabase `qoozzz_decisions` for decision tracking

---

## 📊 Oracle Philosophy Integration

### Nothing is Deleted
- Use git history for all changes
- Never delete branches, archive instead
- Keep all RRR (retrospectives)

### Patterns Over Intentions
- Observe actual behavior via logs
- Document patterns in `patterns/`
- Mirror back to Qoozzz

### External Brain, Not Command
- Puffin shows options, Qoozzz decides
- Log all decisions to database
- Never make autonomous strategic decisions

---

## 🔗 External Services

### Supabase (Primary Data Store)
- **URL:** https://veybuxmpnizojtnehtrw.supabase.co
- **Tables:** 8 (portfolio_summary, zones_config, trade_log, paper_trade_log, bot_settings, ohlcv_data, trades, agent_interactions, qoozzz_decisions)
- **Purpose:** Structured data storage

### Notion (Secondary Knowledge)
- **Purpose:** Soft knowledge storage (Markdown)
- **Status:** To be configured

### Moltbook (AI Social Network)
- **Agent:** Puffin-VPS
- **Status:** Claimed
- **Purpose:** Agent community engagement

---

## 📝 Documentation Standards

### Commit Messages
```
<type>(<scope>): <subject>

<body>

<footer>
```

**Types:** feat, fix, docs, style, refactor, test, chore

**Example:**
```
feat(trading): Add zone trading configuration

Implemented zones_config table structure and added
bot_settings integration for zone trading strategies.

Closes #123
```

### Pattern Documentation
- Use markdown format
- Include examples
- Note when to use/avoid
- Link to related patterns

---

## 🔄 Continuous Improvement

### Weekly Reviews
- Review interaction patterns
- Identify bottlenecks
- Update workflows

### Monthly Reviews
- Deep analysis of performance
- Update patterns
- Refine architecture

---

## 📞 Contact

- **Owner:** Phatchakrit (Qoozzz)
- **Location:** Bangkok, Thailand (UTC+7)
- **Architecture:** Systems Architect & Strategic Operations

---

*Monorepo created: 2026-02-03 07:10 UTC*
*Last updated: 2026-02-03 07:10 UTC*
