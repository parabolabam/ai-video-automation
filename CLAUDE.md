# Project Conventions

## Package Managers

- **Frontend (`web/`)**: Use `pnpm` only (not npm or yarn)
- **Backend (Python)**: Use `uv` for dependency management

## Architecture

- **Frontend**: Next.js 16 with React 19, TypeScript, Tailwind CSS
- **Backend**: Python FastAPI server
- **Database**: Supabase (PostgreSQL + Auth)

## API Architecture

The frontend communicates directly with the Python backend using REST API calls:

- **API Client**: `web/src/lib/api-client.ts` - Centralized fetch wrapper with auth
- **React Query Hooks**: `web/src/hooks/use-workflows.ts` - Data fetching hooks
- **Auth Context**: `web/src/lib/auth-context.tsx` - Supabase auth provider

All API calls include the Supabase JWT token in the Authorization header.

## Key API Endpoints

### Workflows
- `GET /api/workflows` - List all workflows (optional `?user_id=`)
- `GET /api/workflows/{id}` - Get workflow with agents and connections
- `POST /api/workflows` - Create workflow `{ name, description? }`
- `PUT /api/workflows/{id}` - Update workflow `{ name?, description?, is_active? }`
- `DELETE /api/workflows/{id}` - Delete workflow

### Agents & Connections
- `POST /api/agents` - Create agent `{ workflow_id, name, role, model, system_instructions, tools[] }`
- `DELETE /api/agents/{id}` - Delete agent
- `POST /api/connections` - Create connection `{ workflow_id, from_agent_id, to_agent_id }`

### Cron Jobs (Scheduling)
- `GET /api/cron/jobs` - List all jobs for current user
- `POST /api/cron/jobs/cron` - Create cron job `{ cron_expression, input: { workflow_id } }`
- `DELETE /api/cron/jobs/{job_id}` - Delete job

**CronJob Response Format:**
```typescript
{
  job_id: string;
  workflow_id: string;
  user_id: string;
  schedule: string;        // cron expression
  schedule_type: 'cron' | 'interval';
  next_run_time: string | null;
  paused: boolean;
}
```

## Environment Variables

### Frontend (`web/.env.local`)
```
NEXT_PUBLIC_SUPABASE_URL=...
NEXT_PUBLIC_SUPABASE_ANON_KEY=...
NEXT_PUBLIC_API_URL=http://localhost:8000
```

### Backend
```
SUPABASE_URL=...
SUPABASE_SERVICE_ROLE_KEY=...
```

## Running the Project

### Backend
```bash
uv run python -m features.platform.server
```

### Frontend
```bash
cd web
pnpm install
pnpm dev
```

## Testing Requirements

**When making changes to backend or frontend, always test integration:**

1. If changing backend API endpoints or response formats → verify frontend still works
2. If changing frontend API calls or types → verify backend returns expected format
3. Run both services and test the actual flow, don't assume compatibility

```bash
# Terminal 1 - Backend
uv run python -m features.platform.server

# Terminal 2 - Frontend
cd web && pnpm dev
```

## Key Directories

```
web/
├── src/
│   ├── app/           # Next.js app router pages
│   ├── components/    # React components
│   ├── hooks/         # Custom React hooks
│   ├── lib/           # Utility functions and API client
│   └── actions/       # Server actions (optional server-side operations)
features/
├── platform/          # FastAPI backend
```
