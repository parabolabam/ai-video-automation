#!/bin/bash

echo "========================================"
echo "   Local Setup Verification Script"
echo "========================================"
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check backend .env
echo "1. Checking environment files..."
if [ -f .env ]; then
  echo -e "   ${GREEN}✅ Backend .env exists${NC}"

  # Check for required vars
  if grep -q "SUPABASE_URL=" .env && grep -q "SUPABASE_SERVICE_KEY=" .env; then
    echo -e "   ${GREEN}✅ Required backend env vars present${NC}"
  else
    echo -e "   ${YELLOW}⚠️  Missing required env vars in .env${NC}"
    echo "      Required: SUPABASE_URL, SUPABASE_SERVICE_KEY"
  fi
else
  echo -e "   ${RED}❌ Backend .env missing${NC}"
  echo "      Run: cp .env.example .env"
  echo "      Then edit .env with your values"
fi

# Check frontend .env.local
if [ -f web/.env.local ]; then
  echo -e "   ${GREEN}✅ Frontend .env.local exists${NC}"

  # Check for required vars
  if grep -q "NEXT_PUBLIC_SUPABASE_URL=" web/.env.local && grep -q "NEXT_PUBLIC_SUPABASE_ANON_KEY=" web/.env.local; then
    echo -e "   ${GREEN}✅ Required frontend env vars present${NC}"
  else
    echo -e "   ${YELLOW}⚠️  Missing required env vars in web/.env.local${NC}"
    echo "      Required: NEXT_PUBLIC_SUPABASE_URL, NEXT_PUBLIC_SUPABASE_ANON_KEY"
  fi
else
  echo -e "   ${RED}❌ Frontend .env.local missing${NC}"
  echo "      Run: cp web/.env.example web/.env.local"
  echo "      Then edit web/.env.local with your values"
fi

echo ""
echo "2. Checking if services are running..."

# Check backend
if curl -s http://localhost:8000/health > /dev/null 2>&1; then
  HEALTH_STATUS=$(curl -s http://localhost:8000/health)
  echo -e "   ${GREEN}✅ Backend is running on http://localhost:8000${NC}"
  echo "      Health check: $HEALTH_STATUS"
else
  echo -e "   ${RED}❌ Backend not running${NC}"
  echo "      Start with: uv run python features/platform/server.py"
fi

# Check frontend
if curl -s http://localhost:3000 > /dev/null 2>&1; then
  echo -e "   ${GREEN}✅ Frontend is running on http://localhost:3000${NC}"
else
  echo -e "   ${RED}❌ Frontend not running${NC}"
  echo "      Start with: cd web && npm run dev"
fi

echo ""
echo "3. Checking dependencies..."

# Check if uv is installed
if command -v uv &> /dev/null; then
  echo -e "   ${GREEN}✅ uv is installed${NC}"
else
  echo -e "   ${RED}❌ uv not found${NC}"
  echo "      Install: curl -LsSf https://astral.sh/uv/install.sh | sh"
fi

# Check if node is installed
if command -v node &> /dev/null; then
  NODE_VERSION=$(node --version)
  echo -e "   ${GREEN}✅ Node.js is installed${NC} (${NODE_VERSION})"
else
  echo -e "   ${RED}❌ Node.js not found${NC}"
  echo "      Install from: https://nodejs.org/"
fi

# Check if npm is installed
if command -v npm &> /dev/null; then
  NPM_VERSION=$(npm --version)
  echo -e "   ${GREEN}✅ npm is installed${NC} (v${NPM_VERSION})"
else
  echo -e "   ${RED}❌ npm not found${NC}"
fi

echo ""
echo "4. Checking Python dependencies..."

if [ -d .venv ]; then
  echo -e "   ${GREEN}✅ Python virtual environment exists${NC}"
else
  echo -e "   ${YELLOW}⚠️  Virtual environment not found${NC}"
  echo "      Run: uv sync"
fi

echo ""
echo "5. Checking Node dependencies..."

if [ -d web/node_modules ]; then
  echo -e "   ${GREEN}✅ Node modules installed${NC}"
else
  echo -e "   ${YELLOW}⚠️  Node modules not found${NC}"
  echo "      Run: cd web && npm install"
fi

echo ""
echo "========================================"
echo "   Verification Complete"
echo "========================================"
echo ""

# Summary
READY=true

if [ ! -f .env ] || [ ! -f web/.env.local ]; then
  READY=false
fi

if ! curl -s http://localhost:8000/health > /dev/null 2>&1; then
  READY=false
fi

if ! curl -s http://localhost:3000 > /dev/null 2>&1; then
  READY=false
fi

if [ "$READY" = true ]; then
  echo -e "${GREEN}🎉 All systems ready!${NC}"
  echo ""
  echo "Next steps:"
  echo "1. Open http://localhost:3000 in your browser"
  echo "2. Click 'Sign in with Google'"
  echo "3. Verify you can sign in successfully"
  echo ""
  echo "Troubleshooting: See LOCAL-SETUP.md"
else
  echo -e "${YELLOW}⚠️  Some issues found - see above for details${NC}"
  echo ""
  echo "Quick fixes:"
  echo "1. Create .env files if missing"
  echo "2. Start backend: uv run python features/platform/server.py"
  echo "3. Start frontend: cd web && npm run dev"
  echo ""
  echo "Full guide: See LOCAL-SETUP.md"
fi
