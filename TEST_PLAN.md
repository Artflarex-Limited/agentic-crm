# Agentic CRM — Local Test & Verification Plan

**Project:** Agentic CRM v1.0
**Date:** 2026-05-11
**Phase:** Local Verification — "Agents claim tasks are done"
**Owner:** QA Engineer (b776c453) + CEO oversight

---

## Context

The agent team claims to have finished their tasks. This plan verifies that the work is actually complete, correct, and runnable. No Docker available on this machine — testing runs with native Python + Node.js where possible.

**Test Strategy:**
- Pillar 1: Backend (FastAPI, models, agents, services, migrations)
- Pillar 2: Frontend (Next.js, components, API client, build)
- Pillar 3: Integration (end-to-end data flow, Docker Compose dry-run)

---

## Prerequisites

```bash
# Required tools
python3 --version          # needs 3.12+
node --version             # needs 20+
npm --version
git --version
pip --version
```

---

## Phase 1 — Backend Verification

### Step 1.1 — Python Environment

```bash
cd /root/agentic-crm/backend

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Install dev/test dependencies
pip install pytest pytest-asyncio pytest-cov httpx faker black ruff mypy
```

**PASS criteria:** All packages install without error.

---

### Step 1.2 — Database Accessibility

```bash
# Check postgres availability
nc -zv localhost 5432 2>&1

# If not available, test with SQLite
export DATABASE_URL="sqlite:///./test_agentic.db"
```

**PASS criteria:** At least one database backend is reachable.

---

### Step 1.3 — Migrations

```bash
cd /root/agentic-crm/backend
export DATABASE_URL=${DATABASE_URL:-"postgresql+asyncpg://agentic_user:agentic_secret_pass@localhost:5432/agentic_crm"}
alembic upgrade head
```

**PASS criteria:** All migrations run, all tables created without errors.

---

### Step 1.4 — Python Lint

```bash
cd /root/agentic-crm/backend
source venv/bin/activate
ruff check app/ --fix
black --check app/
```

**PASS criteria:** No critical linting errors. Minor formatting issues auto-fixed.

---

### Step 1.5 — Type Check

```bash
cd /root/agentic-crm/backend
source venv/bin/activate
mypy app/ --ignore-missing-imports
```

**PASS criteria:** No type errors blocking compilation.

---

### Step 1.6 — FastAPI Starts

```bash
cd /root/agentic-crm/backend
source venv/bin/activate
DATABASE_URL=${DATABASE_URL:-"sqlite:///./test_agentic.db"} uvicorn app.main:app --port 8000 &
sleep 5
curl -s http://localhost:8000/health
```

**Expected output:** `{"status":"healthy","version":"0.1.0"}`

**PASS criteria:** FastAPI starts without crash, health endpoint responds.

---

### Step 1.7 — Backend Unit Tests

```bash
cd /root/agentic-crm/backend
source venv/bin/activate
pytest tests/ -v --cov=app --cov-report=term-missing
```

**PASS criteria:** All tests pass. Coverage > 60% for backend core.

---

### Step 1.8 — Agent Tasks Smoke Test

```bash
# Test that Celery tasks can at least be imported
cd /root/agentic-crm/backend
source venv/bin/activate
python3 -c "
from app.agents.email_outreach import *
from app.agents.follow_up import *
from app.agents.research import *
from app.agents.qualification import *
from app.agents.reporting import *
print('All agent tasks import OK')
"
```

**PASS criteria:** All agent modules import without errors.

---

### Step 1.9 — Services Smoke Test

```bash
cd /root/agentic-crm/backend
source venv/bin/activate
python3 -c "
from app.services.email_service import *
from app.services.enrichment_service import *
from app.services.linkedin_service import *
from app.services.phone_service import *
print('All services import OK')
"
```

**PASS criteria:** All service modules import without errors.

---

### Step 1.10 — API Endpoint Tests (while server is running)

```bash
# With uvicorn running on port 8000:
curl -s http://localhost:8000/api/contacts/ | python3 -m json.tool | head -5
curl -s http://localhost:8000/api/leads/ | python3 -m json.tool | head -5
curl -s http://localhost:8000/api/deals/ | python3 -m json.tool | head -5
curl -s http://localhost:8000/api/dashboard/stats | python3 -m json.tool | head -10
```

**PASS criteria:** All endpoints return valid JSON (empty arrays [] is fine — means DB is connected).

---

## Phase 2 — Frontend Verification

### Step 2.1 — Node.js Environment

```bash
cd /root/agentic-crm/frontend
node --version   # must be 18+
npm --version
```

---

### Step 2.2 — Install Dependencies

```bash
cd /root/agentic-crm/frontend
npm install
```

**PASS criteria:** All npm packages install without error.

---

### Step 2.3 — TypeScript Check

```bash
cd /root/agentic-crm/frontend
npx tsc --noEmit
```

**PASS criteria:** TypeScript compiles without errors.

---

### Step 2.4 — Build

```bash
cd /root/agentic-crm/frontend
NEXT_PUBLIC_API_URL=http://localhost:8000 npm run build
```

**PASS criteria:** Next.js builds successfully with no errors.

---

### Step 2.5 — Frontend Dev Server

```bash
cd /root/agentic-crm/frontend
# In one terminal:
NEXT_PUBLIC_API_URL=http://localhost:8000 npm run dev &
sleep 10

# In another terminal:
curl -s http://localhost:3000 | grep -o "<title>.*</title>"
```

**Expected:** Dashboard page loads.

**PASS criteria:** Dev server starts and responds to requests.

---

### Step 2.6 — UI Components Exist

Verify these files exist and are non-empty:

```bash
ls -la frontend/components/ui/button.tsx
ls -la frontend/components/ui/card.tsx
ls -la frontend/components/ui/badge.tsx
ls -la frontend/components/ui/table.tsx
ls -la frontend/components/ui/dialog.tsx
```

**PASS criteria:** All shadcn/ui component files exist.

---

## Phase 3 — Infrastructure Verification

### Step 3.1 — docker-compose.yml Syntax

```bash
cd /root/agentic-crm
# Check if docker-compose or docker is available
docker compose config --quiet 2>&1 || echo "Docker not available — validate YAML manually"

# Manual YAML validation
python3 -c "import yaml; yaml.safe_load(open('docker-compose.yml'))" && echo "docker-compose.yml is valid YAML"
```

---

### Step 3.2 — Kubernetes Manifests

```bash
cd /root/agentic-crm/kubernetes
for f in *.yaml; do
  python3 -c "import yaml; yaml.safe_load(open('$f'))" && echo "$f: OK"
done
```

**PASS criteria:** All K8s YAML files are valid.

---

### Step 3.3 — CI/CD Workflows

```bash
cd /root/agentic-crm
ls -la .github/workflows/
python3 -c "import yaml; yaml.safe_load(open('.github/workflows/ci.yml'))" && echo "ci.yml: valid YAML"
python3 -c "import yaml; yaml.safe_load(open('.github/workflows/cd.yml'))" && echo "cd.yml: valid YAML"
```

**PASS criteria:** Both workflow files are valid YAML.

---

### Step 3.4 — Makefile

```bash
cd /root/agentic-crm
make help 2>&1 || make 2>&1 | head -20
```

**PASS criteria:** Makefile parses without error.

---

### Step 3.5 — Scripts

```bash
cd /root/agentic-crm/scripts
for f in *.sh; do bash -n "$f" && echo "$f: syntax OK"; done
```

**PASS criteria:** All shell scripts pass syntax check.

---

## Phase 4 — Issue Verification Checklist

Go through each agent's assigned issues and verify:

| Issue | Agent | Task | Verified |
|-------|-------|------|----------|
| ART-15 | Backend Lead | All agents + services + migrations | [ ] |
| ART-16 | Frontend Lead | Next.js dashboard + components | [ ] |
| ART-17 | DevOps | Docker + K8s + CI/CD + scripts | [ ] |
| ART-18 | QA Engineer | Test suite + pytest + Playwright | [ ] |

---

## Phase 5 — Integration Run (If Docker Available)

```bash
cd /root/agentic-crm

# Full stack up
docker compose up --build -d

# Wait for services
sleep 30

# Check all containers
docker compose ps

# Run full test suite
docker compose exec backend pytest tests/ -v

# Check frontend
curl -s http://localhost:3000 | grep -o "Agentic"

# Logs check
docker compose logs --tail=50 | grep -i error
```

---

## Summary: Pass Criteria

```
[ ] Phase 1 — Backend: ≥ 7/10 steps pass
[ ] Phase 2 — Frontend: ≥ 4/6 steps pass
[ ] Phase 3 — Infrastructure: ≥ 3/5 steps pass
[ ] Phase 4 — Issues: ≥ 3/4 verified complete
[ ] No critical errors in any phase
```

**Overall: PASS if all critical blockers resolved.**

---

## Current State (Pre-Test)

```
Backend:   ✅ 12 agent/service files exist
Frontend:  ✅ 7 pages + 8 UI components exist
Infra:     ✅ docker-compose.yml, K8s, CI/CD, Makefile, scripts all present
Tests:     ⚠️  pytest files exist, not yet executed
DB:        ⚠️  migrations exist, not yet executed
```

**This plan must be executed by QA Engineer. Report results to CEO.**

---

*Generated: 2026-05-11 | Owner: QA Engineer + CEO*
