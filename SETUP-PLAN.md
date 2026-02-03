# Monorepo Setup Plan

**Date:** 2026-02-03 07:10 UTC
**Status:** ✅ STRUCTURE CREATED
**Owner:** Puffin (Architect)
**Builder:** OpenCode (to execute git operations)

---

## 🎯 Objective

Create Monorepo Structure (Option C) for centralized, scalable codebase.

---

## 📊 Monorepo Structure

### Root: `/root/clawd-monorepo/`

```
clawd-monorepo/
├── .gitignore                 # Strict gitignore (no secrets)
├── README.md                  # Monorepo documentation
├── docs/                      # Core documentation
│   ├── AGENTS.md             # Knowledge index
│   ├── SOUL.md              # Oracle philosophy
│   ├── IDENTITY.md           # Puffin's identity
│   ├── USER.md              # About Qoozzz
│   ├── TOOLS.md             # Local setup notes
│   ├── HEARTBEAT.md         # Moltbook heartbeat
│   └── schedule.md          # Calendar and tasks
├── patterns/                  # Reusable knowledge patterns
│   ├── trading-patterns/     # Trading strategies
│   ├── youtube-patterns/     # YouTube content
│   ├── notion-patterns/      # Notion integration
│   ├── server-patterns/      # Home server
│   ├── ai-patterns/         # AI content tools
│   └── interior-patterns/    # Interior design
├── projects/                  # Active development
│   └── trading-system/       # PRIMARY PROJECT
├── dashboards/                # Web dashboards
│   └── trading-dashboard/   # Next.js UI
├── puffin-profile/            # Puffin docs (Gem)
├── scripts/                   # Utility scripts
└── config/                    # Config files (no secrets)
```

---

## 🔐 Security Rules (.gitignore)

### Never Commit
- ❌ API keys (*.key, *apikey*)
- ❌ Environment files (*.env, *.env.local)
- ❌ Secrets (secrets/, secrets.*)
- ❌ Database files (*.db, *.sqlite)
- ❌ Logs (*.log, logs/)
- ❌ Node modules (node_modules/)
- ❌ Build outputs (dist/, build/, .next/)
- ❌ Cache files (.cache/)
- ❌ Editor files (.vscode/, .idea/)
- ❌ OS files (Thumbs.db, .DS_Store)
- ❌ Temporary files (tmp/, temp/)
- ❌ Clawdbot sessions (.clawdbot/sessions/)

### Clawdbot Specific
- ❌ Authentication profiles (*.auth-profiles.json)
- ❌ Heartbeat state (heartbeat-state.json)
- ❌ Agent cache (.clawdbot/cache/)

---

## 📋 Migration Plan

### Phase 1: Copy Core Files (Puffin)
**Status:** ✅ DONE
- [x] Create directory structure
- [x] Create .gitignore
- [x] Create README.md

### Phase 2: Copy Documentation (Puffin)
**Status:** ⏳ PENDING
- [ ] Copy docs/ from /root/clawd/
- [ ] Copy patterns/ from /root/clawd/
- [ ] Copy puffin-profile/ from /root/clawd/
- [ ] Verify all files copied

### Phase 3: Copy Projects (Puffin)
**Status:** ⏳ PENDING
- [ ] Copy projects/trading-system/ from /root/clawd/
- [ ] Copy dashboards/trading-dashboard/ from /root/clawd/
- [ ] Verify project integrity

### Phase 4: Git Operations (OpenCode)
**Status:** ⏳ PENDING
- [ ] git init
- [ ] Add remote (private GitHub repo URL from Qoozzz)
- [ ] Stage all files
- [ ] Initial commit
- [ ] Push to main branch

### Phase 5: Cleanup (Puffin)
**Status:** ⏳ PENDING
- [ ] Verify repo is working
- [ ] Test clone from GitHub
- [ ] Update references in docs
- [ ] Keep /root/clawd/ as active workspace (reference only)

---

## 🔄 After Migration

### Workspace Strategy
- **Keep** `/root/clawd/` as active workspace (where Puffin works)
- **Use** `clawd-monorepo` as version control backup
- **Reference** monorepo when needed

### Git Workflow
- **Daily:** Push changes to monorepo
- **Weekly:** Tag releases for milestones
- **Always:** Write meaningful commit messages

### Branching
- `main` - Stable production
- `develop` - Active development
- `feature/*` - New features
- `bugfix/*` - Bug fixes
- `docs/*` - Documentation updates

---

## 🎯 Next Steps

### Immediate
1. ⏳ Receive GitHub private repo URL from Qoozzz
2. ⏳ Complete file migration (Phases 2-3)
3. ⏳ OpenCode executes git operations (Phase 4)

### Short Term
1. ⏳ Clone and verify monorepo
2. ⏳ Test git workflow
3. ⏳ Integrate with existing processes

### Medium Term
1. ⏳ Setup CI/CD (if needed)
2. ⏳ Add automated backups
3. ⏳ Integrate with deployment workflows

---

## 📝 Notes

### Why Keep /root/clawd/ Active?
- Puffin's workspace is configured here
- All tools expect this location
- Minimizes disruption to current workflow
- Monorepo serves as version control backup

### When to Use Monorepo?
- Version control: Always commit to monorepo
- Collaboration: Clone monorepo for others
- Deployment: Pull from monorepo
- Reference: Check monorepo for history

---

*Setup plan created: 2026-02-03 07:10 UTC*
*Last updated: 2026-02-03 07:10 UTC*
