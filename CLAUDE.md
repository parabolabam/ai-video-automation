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
