#!/bin/bash
# ============================================================
# ParaBench — Mode développement (sans Docker)
# Nécessite: Python 3.10+, Node 18+, PostgreSQL, Redis
# ============================================================

set -e

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m'

echo -e "${CYAN}=== ParaBench Dev Mode ===${NC}"

# Check tools
command -v python3 &>/dev/null || { echo "Python3 requis"; exit 1; }
command -v node &>/dev/null || { echo "Node.js requis"; exit 1; }
command -v npm &>/dev/null || { echo "npm requis"; exit 1; }

# ── Backend ────────────────────────────────────────────────
echo -e "${YELLOW}Setup backend...${NC}"
cd backend

if [ ! -d "venv" ]; then
    python3 -m venv venv
    echo -e "${GREEN}✓ venv créé${NC}"
fi

source venv/bin/activate
pip install -r requirements.txt -q
playwright install chromium
playwright install-deps chromium

echo -e "${GREEN}✓ Backend deps installées${NC}"

# Copy dev env
if [ ! -f .env ]; then
    cp ../.env .env
    sed -i 's|DATABASE_URL=.*|DATABASE_URL=postgresql://parabench:parabench2024@localhost:5432/parabench|' .env
    sed -i 's|REDIS_URL=.*|REDIS_URL=redis://localhost:6379|' .env
fi

# Start backend in background
echo -e "${YELLOW}Démarrage backend (port 8000)...${NC}"
uvicorn main:app --host 0.0.0.0 --port 8000 --reload &
BACKEND_PID=$!

cd ..

# ── Frontend ───────────────────────────────────────────────
echo -e "${YELLOW}Setup frontend...${NC}"
cd frontend

if [ ! -d "node_modules" ]; then
    npm install
fi

echo -e "${GREEN}✓ Frontend deps installées${NC}"
echo -e "${YELLOW}Démarrage frontend (port 3000)...${NC}"
REACT_APP_API_URL=http://localhost:8000 npm start &
FRONTEND_PID=$!

cd ..

echo ""
echo -e "${GREEN}=== Dev servers démarrés ===${NC}"
echo -e "  Frontend : http://localhost:3000"
echo -e "  Backend  : http://localhost:8000"
echo -e "  API Docs : http://localhost:8000/docs"
echo ""
echo "Ctrl+C pour arrêter"

trap "kill $BACKEND_PID $FRONTEND_PID 2>/dev/null; exit" INT TERM
wait
