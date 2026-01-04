# CLAUDE.md - AI Video Automation Platform Guide

**Last Updated:** 2026-01-04
**Purpose:** Comprehensive guide for AI assistants working with this codebase

---

## Table of Contents

1. [Overview](#overview)
2. [Architecture](#architecture)
3. [Tech Stack](#tech-stack)
4. [Directory Structure](#directory-structure)
5. [Development Workflows](#development-workflows)
6. [Database Schema](#database-schema)
7. [API Structure](#api-structure)
8. [Agent Pipeline](#agent-pipeline)
9. [Authentication](#authentication)
10. [Deployment](#deployment)
11. [Key Conventions](#key-conventions)
12. [Common Tasks](#common-tasks)
13. [Important Files](#important-files)
14. [Troubleshooting](#troubleshooting)

---

## Overview

**AI Video Automation** is a full-stack platform that uses multi-agent AI systems to automatically create viral science video content for YouTube Shorts, TikTok, and Instagram.

### What It Does

1. **Research** - AI agents search the web for mind-blowing science facts
2. **Evaluate** - Validates accuracy and filters unreliable claims
3. **Analyze** - Scores viral potential and selects the best fact
4. **Plan** - Designs 4 hyper-realistic video scenes (IMAX documentary style)
5. **Script** - Writes perfectly timed narration with scene synchronization
6. **Generate** - Creates video using Kie.ai/Veo, voiceover with OpenAI TTS
7. **Post-Process** - Burns in subtitles and audio
8. **Publish** - Uploads to YouTube, TikTok, Instagram with proper attribution

### Dual Purpose

This repository serves two purposes:

1. **Video Automation Pipeline** - Python-based AI agent system for automated video creation
2. **Workflow Builder Platform** - Next.js web app for creating custom AI agent workflows (visual no-code builder)

---

## Architecture

### System Components

```
┌─────────────────────────────────────────────────────────────┐
│                    Production Architecture                   │
└─────────────────────────────────────────────────────────────┘

                          ┌──────────────┐
                          │   Nginx      │
                          │ (SSL/Proxy)  │
                          └──────┬───────┘
                                 │
                ┌────────────────┴────────────────┐
                │                                 │
         ┌──────▼──────┐                  ┌──────▼──────┐
         │   Frontend  │                  │   Backend   │
         │   Next.js   │◄────────────────►│   FastAPI   │
         │   (Port     │    tRPC/REST     │   (Port     │
         │    3000)    │                  │    8000)    │
         └──────┬──────┘                  └──────┬──────┘
                │                                 │
                │         ┌──────────────┐        │
                └────────►│   Supabase   │◄───────┘
                          │  (Postgres)  │
                          │    + Auth    │
                          └──────┬───────┘
                                 │
                   ┌─────────────┴─────────────┐
                   │                           │
            ┌──────▼──────┐           ┌───────▼────────┐
            │  External   │           │   External     │
            │   APIs      │           │   Services     │
            │             │           │                │
            │ • OpenAI    │           │ • YouTube      │
            │ • Kie.ai    │           │ • TikTok       │
            │             │           │ • Instagram    │
            └─────────────┘           └────────────────┘
```

### Data Flow

1. **Frontend** → User creates workflows via visual builder
2. **tRPC** → Frontend calls backend via type-safe RPC
3. **FastAPI** → Backend executes workflows using OpenAI Agents SDK
4. **Supabase** → Stores users, workflows, agents, executions
5. **External APIs** → Video generation, publishing, AI processing

---

## Tech Stack

### Backend (`/`)

- **Language:** Python 3.13+
- **Package Manager:** uv
- **Framework:** FastAPI (async web server)
- **AI Agents:** OpenAI Agents SDK
- **Database Client:** Supabase Python SDK
- **Video Processing:** FFmpeg
- **Task Scheduling:** APScheduler
- **Key Libraries:**
  - `openai-agents` - Multi-agent orchestration
  - `google-genai` - Google AI integration
  - `aiohttp` - Async HTTP client
  - `python-dotenv` - Environment management

### Frontend (`/web`)

- **Language:** TypeScript
- **Framework:** Next.js 16 (App Router)
- **UI Library:** React 19
- **Styling:** Tailwind CSS 4
- **State Management:** TanStack Query (React Query)
- **RPC:** tRPC (type-safe API calls)
- **Components:** Radix UI primitives
- **Workflow Builder:** ReactFlow (@xyflow/react)
- **Authentication:** Supabase Auth (Google OAuth)
- **Key Libraries:**
  - `@trpc/client` - Type-safe RPC
  - `@supabase/ssr` - Supabase for Next.js
  - `@xyflow/react` - Visual workflow builder
  - `zod` - Schema validation

### Infrastructure

- **Database:** Supabase (PostgreSQL + Auth)
- **Deployment:** Docker + Docker Compose
- **CI/CD:** GitHub Actions
- **Registry:** GitHub Container Registry (GHCR)
- **Hosting:** Digital Ocean Droplet
- **Domain:** DuckDNS (vingine.duckdns.org)
- **SSL:** Let's Encrypt (via certbot)
- **Reverse Proxy:** Nginx

### External Services

- **Video Generation:** Kie.ai (Veo 3)
- **AI:** OpenAI (GPT-4o, TTS)
- **Search:** DuckDuckGo
- **Publishing:** YouTube, TikTok, Instagram APIs

---

## Directory Structure

```
ai-video-automation/
│
├── features/                    # Python backend modules
│   ├── agents/                  # AI agent implementations
│   │   └── science_agents/      # Science video pipeline agents
│   │       ├── researcher.py    # Finds science facts
│   │       ├── evaluator.py     # Validates facts
│   │       ├── analyst.py       # Scores viral potential
│   │       ├── scene_planner.py # Designs video scenes
│   │       ├── script_writer.py # Writes narration
│   │       ├── pipeline.py      # Orchestrates multi-agent flow
│   │       └── models.py        # Pydantic models
│   │
│   ├── platform/                # Platform backend (workflows)
│   │   ├── server.py            # FastAPI app + endpoints
│   │   ├── runner.py            # Dynamic workflow executor
│   │   ├── scheduler.py         # Cron job scheduling
│   │   ├── auth.py              # Supabase JWT verification
│   │   └── tool_registry.py     # Available agent tools
│   │
│   ├── audio/                   # Audio processing
│   │   ├── tts.py               # OpenAI TTS
│   │   └── service.py           # Audio utilities
│   │
│   ├── video/                   # Video processing
│   │   ├── service.py           # Main video service
│   │   ├── composer.py          # Multi-scene composition
│   │   ├── subtitles.py         # Subtitle generation
│   │   └── stitcher.py          # Scene stitching
│   │
│   ├── kie/                     # Kie.ai video generation
│   │   ├── video_apis.py        # Video API abstraction
│   │   ├── generate_kie_video.py
│   │   └── poll_kie_status.py
│   │
│   ├── publishing/              # Multi-platform publishing
│   │   └── service.py           # Publishing orchestration
│   │
│   ├── youtube/                 # YouTube integration
│   ├── tiktok/                  # TikTok integration
│   ├── instagram/               # Instagram integration
│   ├── blotato/                 # Blotato API (multi-platform)
│   │
│   ├── openai/                  # OpenAI utilities
│   ├── content/                 # Content generation
│   ├── post_production/         # Post-production pipeline
│   └── core/                    # Core utilities (logging, env)
│
├── web/                         # Next.js frontend
│   ├── src/
│   │   ├── app/                 # Next.js App Router
│   │   │   ├── page.tsx         # Homepage
│   │   │   ├── layout.tsx       # Root layout
│   │   │   ├── providers.tsx    # React Query + tRPC provider
│   │   │   ├── api/             # API routes
│   │   │   │   ├── trpc/        # tRPC endpoint
│   │   │   │   └── workflows/   # Workflow REST endpoints
│   │   │   ├── auth/            # Auth pages
│   │   │   ├── actions/         # Server Actions (workflow builder)
│   │   │   ├── docs/            # Documentation UI
│   │   │   └── user/            # User dashboard
│   │   │
│   │   ├── components/          # React components
│   │   │   ├── ui/              # Radix UI components
│   │   │   └── workflow/        # Workflow builder components
│   │   │
│   │   ├── server/              # Server-side code
│   │   │   ├── trpc.ts          # tRPC setup
│   │   │   └── routers/         # tRPC routers
│   │   │       └── workflow.ts  # Workflow CRUD
│   │   │
│   │   ├── lib/                 # Utilities
│   │   │   └── supabase.ts      # Supabase client
│   │   │
│   │   ├── hooks/               # React hooks
│   │   ├── types/               # TypeScript types
│   │   └── proxy.ts             # API proxy utilities
│   │
│   ├── package.json
│   ├── tsconfig.json
│   ├── tailwind.config.ts
│   └── Dockerfile               # Frontend Docker image
│
├── nginx/                       # Nginx reverse proxy
│   ├── Dockerfile
│   └── nginx.conf               # SSL + routing config
│
├── .github/
│   └── workflows/
│       ├── deploy-all-services.yml  # CI/CD pipeline
│       └── pr-checks.yml            # PR validation
│
├── scripts/                     # Deployment scripts
│   ├── setup-backend-droplet.sh
│   └── deploy/
│
├── docs/                        # Documentation
│   ├── AUTH-SETUP-QUICKSTART.md
│   ├── DEPLOYMENT-SETUP.md
│   ├── GOOGLE-AUTH-SETUP.md
│   └── ...
│
├── main.py                      # Legacy pipeline runner
├── main_v2.py                   # New platform runner
├── cron_setup.py                # Cron job setup utility
├── docker-compose.yml           # Local development
├── docker-compose.prod.yml      # Production deployment
├── Dockerfile                   # Backend Docker image
├── pyproject.toml               # Python dependencies
├── .env.example                 # Environment template
├── README.md                    # Project overview
└── CLAUDE.md                    # This file
```

---

## Development Workflows

### Local Development Setup

#### Prerequisites

- Python 3.13+ with `uv` installed
- Node.js 18+ with npm
- Docker & Docker Compose (for containerized setup)
- Supabase account + project
- Google OAuth credentials

#### Backend Setup

```bash
# 1. Clone repository
git clone https://github.com/parabolabam/ai-video-automation.git
cd ai-video-automation

# 2. Create environment file
cp .env.example .env

# 3. Edit .env with your API keys
# Required: OPENAI_API_KEY, KIE_API_KEY, SUPABASE_URL, SUPABASE_SERVICE_KEY

# 4. Install Python dependencies
uv sync

# 5. Run FastAPI server
uv run uvicorn features.platform.server:app --reload --port 8000
```

**Backend runs on:** http://localhost:8000
**API Docs:** http://localhost:8000/docs

#### Frontend Setup

```bash
# 1. Navigate to web directory
cd web

# 2. Create environment file
cp .env.example .env.local

# 3. Edit web/.env.local
# Required: NEXT_PUBLIC_API_URL=http://localhost:8000
#           NEXT_PUBLIC_SUPABASE_URL, NEXT_PUBLIC_SUPABASE_ANON_KEY

# 4. Install dependencies
npm install

# 5. Run development server
npm run dev
```

**Frontend runs on:** http://localhost:3000

#### Docker Local Setup

```bash
# Option 1: Manual docker-compose
DOCKER_HOST=unix:///Users/YOUR_USER/.colima/default/docker.sock docker-compose up

# Option 2: Use helper script
./docker-local.sh up

# Option 3: Automated setup
./setup-local-env.sh
```

See `DOCKER-LOCAL.md` for detailed Docker setup instructions.

### Database Setup

```bash
# 1. Create Supabase project at https://supabase.com

# 2. Run migrations in Supabase SQL Editor
# Execute: platform_migration.sql (workflows, agents, executions)
# Execute: supabase_migration.sql (conversation_state)

# 3. Configure OAuth
# Follow: docs/GOOGLE-AUTH-SETUP.md

# 4. Seed database (optional)
uv run python -m features.platform.seed_db
```

See `SUPABASE-SETUP.md` for detailed database setup.

### Running the Agent Pipeline

```bash
# Run the science video automation pipeline
uv run python -m features.app.run_pipeline_v2

# Or use the platform server (with scheduling)
uv run uvicorn features.platform.server:app --reload
```

---

## Database Schema

### Core Tables

#### `profiles`
```sql
id            UUID PRIMARY KEY (references auth.users)
full_name     TEXT
avatar_url    TEXT
created_at    TIMESTAMP
updated_at    TIMESTAMP
```

Auto-created when users sign up via Google OAuth.

#### `workflows`
```sql
id            UUID PRIMARY KEY
user_id       UUID REFERENCES profiles(id)
name          TEXT NOT NULL
description   TEXT
is_active     BOOLEAN DEFAULT true
created_at    TIMESTAMP
updated_at    TIMESTAMP
```

Represents a custom AI agent workflow.

#### `agents`
```sql
id                    UUID PRIMARY KEY
workflow_id           UUID REFERENCES workflows(id)
name                  TEXT NOT NULL
role                  TEXT NOT NULL
model                 TEXT DEFAULT 'gpt-4o'
system_instructions   TEXT NOT NULL
tools                 TEXT[] (array of tool IDs)
output_schema         JSONB (Pydantic schema)
created_at            TIMESTAMP
```

Individual AI agents within a workflow.

#### `workflow_connections`
```sql
id              UUID PRIMARY KEY
workflow_id     UUID REFERENCES workflows(id)
from_agent_id   UUID REFERENCES agents(id) (nullable - start node)
to_agent_id     UUID REFERENCES agents(id)
description     TEXT
created_at      TIMESTAMP
```

Defines the graph edges (agent connections).

#### `executions`
```sql
id              UUID PRIMARY KEY
workflow_id     UUID REFERENCES workflows(id)
user_id         UUID REFERENCES profiles(id)
status          TEXT (pending, running, completed, failed)
started_at      TIMESTAMP
completed_at    TIMESTAMP
result          JSONB
input_params    JSONB
error_message   TEXT
```

Tracks workflow execution history.

#### `conversation_state`
```sql
key             TEXT PRIMARY KEY
response_id     TEXT NOT NULL
updated_at      TIMESTAMP
```

Stores OpenAI Agents SDK conversation continuity.

### Relationships

```
profiles (1) ───< (N) workflows
workflows (1) ───< (N) agents
workflows (1) ───< (N) workflow_connections
workflows (1) ───< (N) executions
```

---

## API Structure

### Backend: FastAPI (`/features/platform/server.py`)

**Base URL:** `http://localhost:8000` (dev) / `https://vingine.duckdns.org` (prod)

#### Endpoints

**Public:**
- `GET /health` - Health check (no auth)

**Authenticated (requires JWT):**
- `POST /execute` - Execute a workflow
- `GET /workflows` - List user workflows
- `POST /workflows` - Create workflow
- `GET /workflows/{id}` - Get workflow details
- `POST /cron` - Create cron job
- `POST /interval` - Create interval job
- `GET /jobs` - List scheduled jobs
- `DELETE /jobs/{id}` - Delete scheduled job
- `POST /stream/execute` - Execute with streaming response

**Authentication:**
All endpoints (except `/health`) require `Authorization: Bearer <JWT_TOKEN>` header.

Get token from frontend:
```javascript
// In browser console
(await window.supabase.auth.getSession()).data.session.access_token
```

**CORS:**
Configured for:
- `http://localhost:3000` (local dev)
- `https://vingine.duckdns.org` (production)

### Frontend: tRPC (`/web/src/server/routers/`)

**Base URL:** `/api/trpc`

#### Procedures

**workflow.list** - Get user workflows
```typescript
const workflows = await trpc.workflow.list.useQuery({ userId: 'uuid' });
```

**workflow.get** - Get single workflow with agents & connections
```typescript
const workflow = await trpc.workflow.get.useQuery({ id: 'uuid' });
```

**workflow.create** - Create new workflow
```typescript
const workflow = await trpc.workflow.create.mutate({
  userId: 'uuid',
  name: 'My Workflow',
  description: 'Description'
});
```

**workflow.saveGraph** - Save workflow graph (agents + connections)
```typescript
await trpc.workflow.saveGraph.mutate({
  workflowId: 'uuid',
  agents: [...],
  connections: [...]
});
```

### API Authentication Flow

1. User signs in via Google OAuth (Supabase)
2. Supabase returns JWT token
3. Frontend stores token in session
4. Frontend passes token to backend in `Authorization` header
5. Backend verifies JWT with Supabase public key
6. Backend extracts `user_id` from JWT claims
7. Backend enforces row-level security

---

## Agent Pipeline

### Science Video Automation Pipeline

Located in: `features/agents/science_agents/`

#### Agent Roles

1. **Researcher** (`researcher.py`)
   - **Task:** Find 5 mind-blowing science facts
   - **Tools:** Web search (DuckDuckGo)
   - **Output:** List of facts with explanations

2. **Evaluator** (`evaluator.py`)
   - **Task:** Validate accuracy and filter unreliable claims
   - **Tools:** Web search, fact-checking
   - **Output:** Validated facts with confidence scores

3. **Analyst** (`analyst.py`)
   - **Task:** Score viral potential and select best fact
   - **Output:** Single fact with reasoning

4. **Scene Planner** (`scene_planner.py`)
   - **Task:** Design 4 hyper-realistic IMAX-style scenes
   - **Output:** Scene descriptions with visual details

5. **Script Writer** (`script_writer.py`)
   - **Task:** Write 32-second narration (2.2 words/sec)
   - **Output:** Timed script with scene synchronization

#### Pipeline Flow

```python
# features/agents/science_agents/pipeline.py

async def run_science_research_pipeline() -> dict:
    runner = Runner()

    # Step 1: Research
    research_result = await runner.run(researcher, "Find 5 facts...")
    facts = research_result.final_output.facts

    # Step 2: Evaluate
    eval_result = await runner.run(evaluator, facts_text)
    validated = eval_result.final_output.validated_facts

    # Step 3: Analyze
    analyst_result = await runner.run(analyst, validated_text)
    best_fact = analyst_result.final_output.best_fact

    # Step 4: Plan Scenes
    scene_result = await runner.run(scene_planner, best_fact)
    scenes = scene_result.final_output.scenes

    # Step 5: Write Script
    script_result = await runner.run(script_writer, scenes)
    script = script_result.final_output

    return {
        'fact': best_fact,
        'scenes': scenes,
        'script': script.voiceover_script
    }
```

#### Key Patterns

- **Structured Output:** All agents use Pydantic models for type-safe outputs
- **Conversation Continuity:** Uses `previous_response_id` for context
- **Error Handling:** Pipeline fails fast with descriptive errors
- **Logging:** Comprehensive logging at each step

---

## Authentication

### Technology

- **Provider:** Supabase Auth
- **Method:** Google OAuth (OAuth 2.0)
- **Token Type:** JWT (JSON Web Token)
- **Storage:** HTTP-only cookies (frontend), in-memory (backend verification)

### Flow

#### Sign In

1. User clicks "Sign in with Google" on frontend
2. Frontend calls `supabase.auth.signInWithOAuth({ provider: 'google' })`
3. Redirects to Google OAuth consent screen
4. User grants permissions
5. Google redirects back to `/auth/callback`
6. Supabase creates user session and JWT
7. Frontend stores session in cookies
8. User redirected to dashboard

#### API Calls

1. Frontend retrieves session from cookies
2. Extracts `access_token` from session
3. Includes in API request: `Authorization: Bearer <token>`
4. Backend verifies JWT signature using Supabase public key
5. Backend extracts user claims (`sub`, `email`, etc.)
6. Backend executes request with user context

#### Sign Out

```typescript
await supabase.auth.signOut();
```

### Files

- **Frontend Auth:** `web/src/app/auth/callback/route.ts`
- **Backend Auth:** `features/platform/auth.py`
- **Auth Setup Guide:** `docs/GOOGLE-AUTH-SETUP.md`

---

## Deployment

### CI/CD Pipeline

**Workflow:** `.github/workflows/deploy-all-services.yml`

#### Trigger

- Push to `main` branch
- Manual workflow dispatch

#### Jobs

1. **build-backend** - Build Python backend Docker image
2. **build-frontend** - Build Next.js frontend Docker image
3. **build-nginx** - Build Nginx reverse proxy image
4. **deploy-backend** - SSH to droplet, pull & deploy backend
5. **deploy-frontend** - SSH to droplet, pull & deploy frontend
6. **deploy-nginx** - SSH to droplet, pull & deploy nginx
7. **deployment-summary** - Report deployment status

#### Image Registry

- **Registry:** GitHub Container Registry (GHCR)
- **Backend Image:** `ghcr.io/parabolabam/ai-video-automation/backend:latest`
- **Frontend Image:** `ghcr.io/parabolabam/ai-video-automation/frontend:latest`
- **Nginx Image:** `ghcr.io/parabolabam/ai-video-automation/nginx:latest`

#### Deployment Strategy

1. Build Docker images on GitHub Actions runners
2. Push to GHCR
3. SSH to Digital Ocean droplet
4. Pull latest images
5. Stop old containers
6. Start new containers with `docker-compose.prod.yml`
7. Run health checks

### Production Environment

- **Host:** Digital Ocean Droplet
- **Domain:** vingine.duckdns.org
- **SSL:** Let's Encrypt (auto-renewal via certbot)
- **Services:**
  - Backend: Port 8000 (internal)
  - Frontend: Port 3000 (internal)
  - Nginx: Ports 80, 443 (external)

### Environment Variables

**GitHub Secrets (required):**
```
DO_DROPLET_IP              # Droplet IP address
DO_DROPLET_USER            # SSH username
DO_SSH_PRIVATE_KEY         # SSH private key
KIE_API_KEY                # Kie.ai API key
OPENAI_API_KEY             # OpenAI API key
SUPABASE_URL               # Supabase project URL
SUPABASE_KEY               # Supabase anon key
SUPABASE_SERVICE_KEY       # Supabase service role key
YOUTUBE_CLIENT_ID          # YouTube OAuth client ID
YOUTUBE_CLIENT_SECRET      # YouTube OAuth secret
YOUTUBE_REFRESH_TOKEN      # YouTube refresh token
NEXT_PUBLIC_API_URL        # Frontend API URL
NEXT_PUBLIC_SITE_URL       # Frontend site URL
API_URL                    # Internal backend URL
NEXT_PUBLIC_SUPABASE_URL   # Frontend Supabase URL
NEXT_PUBLIC_SUPABASE_ANON_KEY  # Frontend Supabase key
```

### Deployment Guides

- **Quick Start:** `DEPLOYMENT-QUICKSTART.md`
- **Full Guide:** `DEPLOYMENT.md`
- **SSL Setup:** `SSL-SETUP.md`
- **Docker Local:** `DOCKER-LOCAL.md`
- **Domain Setup:** `docs/VINGINE-DOMAIN-SETUP.md`

---

## Key Conventions

### Python Code Style

- **Async First:** Use `async/await` for all I/O operations
- **Type Hints:** Always include type hints
- **Docstrings:** Use Google-style docstrings
- **Logging:** Use structured logging with `logging.getLogger(__name__)`
- **Error Handling:** Fail fast with descriptive exceptions
- **Imports:** Group by stdlib, third-party, local (separated by blank lines)

**Example:**
```python
import logging
from typing import Any

from openai import OpenAI

from features.core.load_env import load_environment

logger = logging.getLogger(__name__)

async def process_data(data: dict[str, Any]) -> str:
    """Process data and return result.

    Args:
        data: Input data dictionary

    Returns:
        Processed result as string

    Raises:
        ValueError: If data is invalid
    """
    logger.info(f"Processing data with {len(data)} keys")
    # Implementation
```

### TypeScript Code Style

- **Strict Mode:** Enable TypeScript strict mode
- **Type Safety:** Avoid `any`, prefer explicit types
- **Server Components:** Use React Server Components by default
- **Client Components:** Mark with `"use client"` only when needed
- **Async/Await:** Use async/await, avoid `.then()`
- **Error Handling:** Use try/catch with typed errors

**Example:**
```typescript
// Server Component (default)
async function UserDashboard({ userId }: { userId: string }) {
  const workflows = await getWorkflows(userId);
  return <div>{workflows.map(w => <WorkflowCard key={w.id} {...w} />)}</div>
}

// Client Component (when needed)
"use client"

import { useState } from 'react';

export function InteractiveButton() {
  const [count, setCount] = useState(0);
  return <button onClick={() => setCount(c => c + 1)}>{count}</button>
}
```

### Environment Variables

- **Backend (.env):** Use `VARIABLE_NAME` (uppercase snake_case)
- **Frontend (.env.local):** Public vars must start with `NEXT_PUBLIC_`
- **Never commit:** `.env` files (use `.env.example` templates)
- **Validation:** Validate required env vars at startup

### Commit Messages

Use conventional commits:
```
feat: Add workflow execution streaming
fix: Resolve tRPC authentication error
docs: Update deployment guide
refactor: Simplify agent pipeline structure
test: Add workflow runner tests
chore: Update dependencies
```

### Git Branch Strategy

- **main** - Production branch (auto-deploys)
- **claude/claude-md-*-<session_id>** - Claude Code feature branches
- Feature branches: `feature/workflow-builder`
- Bugfix branches: `fix/auth-token-expiry`

### API Design

- **RESTful:** Use HTTP verbs correctly (GET, POST, PUT, DELETE)
- **Status Codes:** Use appropriate HTTP status codes
- **Error Responses:** Return structured error objects
- **Pagination:** Use limit/offset for large datasets
- **Versioning:** Include version in URL if breaking changes

**Example Error Response:**
```json
{
  "error": "Workflow not found",
  "details": "Workflow with ID abc-123 does not exist",
  "code": "WORKFLOW_NOT_FOUND"
}
```

---

## Common Tasks

### Add a New Agent to Pipeline

1. Create agent file: `features/agents/science_agents/new_agent.py`

```python
from agents import Agent
from pydantic import BaseModel

class NewAgentOutput(BaseModel):
    result: str

def create_new_agent() -> Agent:
    return Agent(
        name="New Agent",
        model="gpt-4o",
        instructions="You are a helpful agent...",
        output_schema=NewAgentOutput
    )
```

2. Import in `pipeline.py`:
```python
from .new_agent import create_new_agent

async def run_science_research_pipeline():
    # ... existing code
    new_agent = create_new_agent()
    result = await runner.run(new_agent, "Your prompt")
```

### Add a New tRPC Procedure

1. Edit `web/src/server/routers/workflow.ts`:

```typescript
export const workflowRouter = router({
  // ... existing procedures

  myNewProcedure: publicProcedure
    .input(z.object({ id: z.string() }))
    .query(async ({ input }) => {
      // Implementation
      return result;
    }),
});
```

2. Use in frontend:
```typescript
const { data } = trpc.workflow.myNewProcedure.useQuery({ id: '123' });
```

### Add a New Environment Variable

1. Add to `.env.example`:
```bash
# New Feature
NEW_API_KEY=your_api_key_here
```

2. Add to validation (`validate_env.py`):
```python
required_vars = [
    'NEW_API_KEY',
    # ... existing
]
```

3. Add to GitHub Secrets (for deployment)

4. Add to `docker-compose.prod.yml`:
```yaml
environment:
  - NEW_API_KEY=${NEW_API_KEY}
```

### Run Database Migration

1. Write SQL migration: `migrations/001_add_feature.sql`
2. Run in Supabase SQL Editor
3. Update `CLAUDE.md` database schema section
4. Commit migration file to repo

### Add a New Tool for Agents

1. Edit `features/platform/tool_registry.py`:

```python
from agents import function_tool

@function_tool
def my_new_tool(param: str) -> str:
    """Tool description for AI."""
    return result

AVAILABLE_TOOLS = {
    'my_new_tool': my_new_tool,
    # ... existing
}
```

2. Use in agent system instructions:
```python
instructions = """
You have access to the following tools:
- my_new_tool: Description
"""
```

### Debug Production Issues

```bash
# SSH to droplet
ssh user@YOUR_DROPLET_IP

# View logs
docker logs ai-video-backend -f
docker logs ai-video-frontend -f
docker logs ai-video-nginx -f

# Check status
docker ps

# Restart service
docker restart ai-video-backend

# Check health
curl http://localhost:8000/health
curl http://localhost:3000
```

---

## Important Files

### Configuration Files

| File | Purpose |
|------|---------|
| `pyproject.toml` | Python dependencies (uv) |
| `web/package.json` | Node.js dependencies |
| `.env.example` | Backend environment template |
| `web/.env.example` | Frontend environment template |
| `docker-compose.yml` | Local Docker setup |
| `docker-compose.prod.yml` | Production Docker setup |
| `Dockerfile` | Backend Docker image |
| `web/Dockerfile` | Frontend Docker image |
| `nginx/nginx.conf` | Nginx reverse proxy config |
| `tsconfig.json` | TypeScript config |
| `tailwind.config.ts` | Tailwind CSS config |

### Documentation Files

| File | Purpose |
|------|---------|
| `README.md` | Project overview |
| `CLAUDE.md` | This file (AI assistant guide) |
| `LOCAL-SETUP.md` | Local development setup |
| `DEPLOYMENT.md` | Production deployment guide |
| `DEPLOYMENT-QUICKSTART.md` | Quick deployment guide |
| `DOCKER-LOCAL.md` | Docker local setup |
| `SSL-SETUP.md` | SSL certificate setup |
| `SUPABASE-SETUP.md` | Supabase configuration |
| `docs/AUTH-SETUP-QUICKSTART.md` | OAuth setup |
| `docs/GOOGLE-AUTH-SETUP.md` | Google OAuth details |

### Entry Points

| File | Purpose |
|------|---------|
| `main.py` | Legacy pipeline runner |
| `main_v2.py` | New platform runner |
| `features/platform/server.py` | FastAPI server |
| `web/src/app/layout.tsx` | Next.js root layout |
| `web/src/app/page.tsx` | Next.js homepage |

### Database Files

| File | Purpose |
|------|---------|
| `platform_migration.sql` | Main platform schema |
| `supabase_migration.sql` | Conversation state table |
| `features/platform/seed_db.py` | Seed demo data |

---

## Troubleshooting

### Common Issues

#### "Module not found" errors (Python)

```bash
# Ensure dependencies are installed
uv sync

# Check Python version
python --version  # Should be 3.13+
```

#### "Type error" in TypeScript

```bash
# Rebuild TypeScript
cd web
npm run build

# Check for type errors
npx tsc --noEmit
```

#### Authentication errors

1. Check `.env` has correct Supabase keys
2. Verify OAuth redirect URLs in Supabase dashboard
3. Check JWT token expiry (tokens expire after 1 hour)
4. Clear browser cookies and sign in again

#### Docker container won't start

```bash
# Check logs
docker logs <container_name>

# Check environment variables
docker exec <container_name> env

# Restart container
docker restart <container_name>
```

#### Supabase connection errors

1. Verify `SUPABASE_URL` and `SUPABASE_SERVICE_KEY` in `.env`
2. Check Supabase project status (not paused)
3. Verify RLS policies allow service role access
4. Check network connectivity

#### Video generation fails

1. Verify `KIE_API_KEY` is valid
2. Check Kie.ai API status
3. Review logs for error messages
4. Ensure sufficient API credits

### Getting Help

1. **Check logs** - Most issues are logged with descriptive messages
2. **Review documentation** - Check relevant `.md` files in `/docs`
3. **Check GitHub Issues** - Search for similar problems
4. **API Documentation** - Visit `/docs` endpoint for backend API
5. **Supabase Dashboard** - Check database, auth, and logs

---

## Development Best Practices

### Before Making Changes

1. **Read relevant documentation** - Check docs for the area you're modifying
2. **Understand the flow** - Trace data flow through the system
3. **Check dependencies** - Understand what depends on your changes
4. **Run tests** - Ensure existing functionality works

### When Adding Features

1. **Update documentation** - Add to relevant `.md` files
2. **Update `.env.example`** - Document new environment variables
3. **Add type safety** - Use Pydantic (Python) and Zod (TypeScript)
4. **Log appropriately** - Add structured logging
5. **Handle errors** - Add proper error handling
6. **Update CLAUDE.md** - Keep this file current

### Before Committing

1. **Lint code** - Run linters (ESLint for TypeScript)
2. **Format code** - Consistent formatting
3. **Test locally** - Verify changes work
4. **Check git status** - Don't commit `.env` or sensitive files
5. **Write good commit message** - Use conventional commits

### Security Considerations

1. **Never commit secrets** - Use environment variables
2. **Validate input** - Always validate user input
3. **Use parameterized queries** - Prevent SQL injection
4. **Sanitize output** - Prevent XSS attacks
5. **Rate limit APIs** - Prevent abuse
6. **Use HTTPS** - Always encrypt in production
7. **Verify JWT tokens** - Don't trust client-provided auth
8. **RLS policies** - Enable row-level security on all tables

---

## Quick Reference

### Start Development

```bash
# Backend
uv sync
uv run uvicorn features.platform.server:app --reload

# Frontend
cd web && npm install && npm run dev

# Docker (full stack)
./docker-local.sh up
```

### Test Endpoints

```bash
# Health check
curl http://localhost:8000/health

# API docs
open http://localhost:8000/docs

# Frontend
open http://localhost:3000
```

### Deploy to Production

```bash
git push origin main
# Watch: https://github.com/parabolabam/ai-video-automation/actions
```

### Common Commands

```bash
# Backend
uv add <package>              # Add Python dependency
uv run python -m <module>     # Run Python module

# Frontend
npm install <package>         # Add Node dependency
npm run build                 # Build for production
npm run lint                  # Run ESLint

# Docker
docker-compose up -d          # Start services
docker-compose logs -f        # Follow logs
docker-compose down           # Stop services
```

---

## Changelog

### 2026-01-04
- Initial CLAUDE.md created
- Documented full architecture and workflows
- Added comprehensive development guide
- Included deployment and troubleshooting sections

---

**For Questions or Updates:**
Update this file when making significant architectural changes.
Keep it synchronized with actual codebase structure.
