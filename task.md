# AI Video Automation - Project Roadmap & Tasks

## 🚀 Phase 1: Platform Foundation (Current Status: v0.1 Complete)
Establishes the core infrastructure, backend-for-frontend (BFF) pattern, and execution engine.

- [x] **Backend Infrastructure**
  - [x] Dockerize FastAPI application (`app` service)
  - [x] Implement `DynamicWorkflowRunner` for linear chains
  - [x] Create Streaming API (`/api/run_stream`) for real-time feedback
  - [x] Set up Supabase Client & Database Schema (`platform_migration.sql`)

- [x] **Frontend Architecture**
  - [x] Initialize Next.js 15 + Tailwind + shadcn/ui (`web` service)
  - [x] Configure Docker for development (hot-reloading)
  - [x] Set up tRPC for type-safe Client <-> BFF communication
  - [x] Implement User-scoped Routing (`/user/[userId]`)

- [x] **Core UI Components**
  - [x] **Dashboard:** List workflows, run dialog (Legacy), Create new (tRPC mutation)
  - [x] **Visualizer:** Real-time graph visualization with active state & log streaming
  - [x] **Editor:** Graphical Node-based editor (React Flow) to modify agents & connections

---

## 🛠 Phase 2: Agent Intelligence & Reliability
Focus on making the agents smarter, stateful, and more robust.

- [ ] **Agent Memory & Context**
  - [ ] Implement robust Short-term Memory (Conversation History per execution)
  - [ ] Implement Long-term Memory (Vector DB retrieval for "Content Brain")
  - [ ] Structured Outputs: Enforce Pydantic schemas for all agent tools reliably

- [ ] **Advanced Tooling**
  - [ ] **Browser Use:** Integrate Headless Browser tool for dynamic research
  - [ ] **Video Processing:** Expose generic video editing tools to agents (FFmpeg wrapper)
  - [ ] **File System:** Safe sandbox for agents to read/write intermediate assets

- [ ] **Execution Patterns**
  - [ ] Support Branching/Parallel execution in `runner.py` (DAGs, not just chains)
  - [ ] Implement "Human-in-the-loop" breakpoints (Agent pauses for user approval)

---

## 🎨 Phase 3: Enhanced User Experience
Polishing the UI/UX to a professional standard.

- [ ] **Editor Improvements**
  - [ ] Drag-and-drop Tool assignment from a sidebar
  - [ ] Schema Editor for defining Agent Output properties visually
  - [ ] Layout Auto-arrangement (Dagre/Elk)

- [ ] **Monitoring & Observability**
  - [ ] Execution History Page: View past runs, tokens used, cost estimation
  - [ ] Detailed Step Tracing: Inspect inputs/outputs of every single node step
  - [ ] Error Recovery: "Retry from failed step" button

---

## 🔒 Phase 4: Production Readiness & Scale
Preparing the system for multi-user deployment.

- [ ] **Authentication & Security**
  - [ ] Replace "Seed User" with real Supabase Auth (Login/Signup)
  - [ ] Row Level Security (RLS) policies enforcement
  - [ ] API Key Management for user-provided LLM keys

- [ ] **Infrastructure**
  - [ ] Migration strategy (FastAPI -> Async Workers like Celery/Temporal for long jobs)
  - [ ] Deploy scripts (Vercel for Web, Fly.io/AWS for Backend)
  - [ ] CI/CD Pipelines
