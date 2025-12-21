#!/bin/bash

echo "========================================"
echo "   Local Environment Setup Wizard"
echo "========================================"
echo ""
echo "This script will help you configure your local environment variables."
echo "You'll need the following from your Supabase project:"
echo "  - Project URL"
echo "  - Anon (public) key"
echo "  - Service role (secret) key"
echo ""
echo "Get these from: https://supabase.com/dashboard/project/_/settings/api"
echo ""

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

# Check if .env files exist
if [ -f .env ] && [ -f web/.env.local ]; then
  echo -e "${YELLOW}Warning: .env and web/.env.local already exist.${NC}"
  read -p "Do you want to reconfigure? (y/N): " RECONFIGURE
  if [[ ! $RECONFIGURE =~ ^[Yy]$ ]]; then
    echo "Setup cancelled. Existing files unchanged."
    exit 0
  fi
fi

# Create .env files if they don't exist
if [ ! -f .env ]; then
  cp .env.example .env
fi

if [ ! -f web/.env.local ]; then
  cp web/.env.example web/.env.local
fi

echo ""
echo "Step 1: Supabase Configuration"
echo "================================"
echo ""

# Get Supabase URL
read -p "Enter your Supabase Project URL (e.g., https://xxxxx.supabase.co): " SUPABASE_URL
if [ -z "$SUPABASE_URL" ]; then
  echo "Error: Supabase URL is required"
  exit 1
fi

# Get Supabase Anon Key
echo ""
read -p "Enter your Supabase Anon Key (public key): " SUPABASE_ANON_KEY
if [ -z "$SUPABASE_ANON_KEY" ]; then
  echo "Error: Supabase Anon Key is required"
  exit 1
fi

# Get Supabase Service Key
echo ""
read -p "Enter your Supabase Service Role Key (secret key): " SUPABASE_SERVICE_KEY
if [ -z "$SUPABASE_SERVICE_KEY" ]; then
  echo "Error: Supabase Service Role Key is required"
  exit 1
fi

echo ""
echo "Step 2: API Keys (Optional - skip if you don't have them yet)"
echo "=============================================================="
echo ""

# Get KIE API Key
read -p "Enter your KIE API Key (press Enter to skip): " KIE_API_KEY

# Get OpenAI API Key
read -p "Enter your OpenAI API Key (press Enter to skip): " OPENAI_API_KEY

echo ""
echo "Updating configuration files..."
echo ""

# Update backend .env
if [ -n "$SUPABASE_URL" ]; then
  # Use sed compatible with both macOS and Linux
  if [[ "$OSTYPE" == "darwin"* ]]; then
    # macOS
    sed -i '' "s|SUPABASE_URL=.*|SUPABASE_URL=$SUPABASE_URL|g" .env
    sed -i '' "s|SUPABASE_SERVICE_KEY=.*|SUPABASE_SERVICE_KEY=$SUPABASE_SERVICE_KEY|g" .env
    [ -n "$KIE_API_KEY" ] && sed -i '' "s|KIE_API_KEY=.*|KIE_API_KEY=$KIE_API_KEY|g" .env
    [ -n "$OPENAI_API_KEY" ] && sed -i '' "s|OPENAI_API_KEY=.*|OPENAI_API_KEY=$OPENAI_API_KEY|g" .env
  else
    # Linux
    sed -i "s|SUPABASE_URL=.*|SUPABASE_URL=$SUPABASE_URL|g" .env
    sed -i "s|SUPABASE_SERVICE_KEY=.*|SUPABASE_SERVICE_KEY=$SUPABASE_SERVICE_KEY|g" .env
    [ -n "$KIE_API_KEY" ] && sed -i "s|KIE_API_KEY=.*|KIE_API_KEY=$KIE_API_KEY|g" .env
    [ -n "$OPENAI_API_KEY" ] && sed -i "s|OPENAI_API_KEY=.*|OPENAI_API_KEY=$OPENAI_API_KEY|g" .env
  fi
fi

# Update frontend web/.env.local
if [ -n "$SUPABASE_URL" ]; then
  if [[ "$OSTYPE" == "darwin"* ]]; then
    # macOS
    sed -i '' "s|NEXT_PUBLIC_SUPABASE_URL=.*|NEXT_PUBLIC_SUPABASE_URL=$SUPABASE_URL|g" web/.env.local
    sed -i '' "s|NEXT_PUBLIC_SUPABASE_ANON_KEY=.*|NEXT_PUBLIC_SUPABASE_ANON_KEY=$SUPABASE_ANON_KEY|g" web/.env.local
    sed -i '' "s|NEXT_PUBLIC_API_URL=.*|NEXT_PUBLIC_API_URL=http://localhost:8000|g" web/.env.local
  else
    # Linux
    sed -i "s|NEXT_PUBLIC_SUPABASE_URL=.*|NEXT_PUBLIC_SUPABASE_URL=$SUPABASE_URL|g" web/.env.local
    sed -i "s|NEXT_PUBLIC_SUPABASE_ANON_KEY=.*|NEXT_PUBLIC_SUPABASE_ANON_KEY=$SUPABASE_ANON_KEY|g" web/.env.local
    sed -i "s|NEXT_PUBLIC_API_URL=.*|NEXT_PUBLIC_API_URL=http://localhost:8000|g" web/.env.local
  fi
fi

echo -e "${GREEN}✅ Backend .env updated${NC}"
echo -e "${GREEN}✅ Frontend web/.env.local updated${NC}"

echo ""
echo "========================================"
echo "   Configuration Complete!"
echo "========================================"
echo ""
echo "Your environment is configured. Next steps:"
echo ""
echo "1. Configure Google OAuth redirect URL in Supabase:"
echo "   → Go to: https://supabase.com/dashboard/project/_/auth/url-configuration"
echo "   → Add redirect URL: http://localhost:3000/auth/callback"
echo ""
echo "2. Start the backend (Terminal 1):"
echo "   → uv run python features/platform/server.py"
echo ""
echo "3. Start the frontend (Terminal 2):"
echo "   → cd web && npm run dev"
echo ""
echo "4. Test authentication:"
echo "   → Open http://localhost:3000"
echo "   → Click 'Sign in with Google'"
echo ""
echo "For detailed setup instructions, see: LOCAL-SETUP.md"
echo "For authentication guide, see: docs/AUTH-SETUP-QUICKSTART.md"
echo ""
