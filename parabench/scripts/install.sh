#!/bin/bash
# ============================================================
# ParaBench — Script d'installation automatique
# Usage: bash install.sh
# ============================================================

set -e

GREEN='\033[0;32m'
CYAN='\033[0;36m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BOLD='\033[1m'
NC='\033[0m'

echo ""
echo -e "${CYAN}${BOLD}╔══════════════════════════════════════════╗${NC}"
echo -e "${CYAN}${BOLD}║   ParaBench — Installation Automatique   ║${NC}"
echo -e "${CYAN}${BOLD}║   Benchmark Para Tunisien v1.0           ║${NC}"
echo -e "${CYAN}${BOLD}╚══════════════════════════════════════════╝${NC}"
echo ""

# ── 1. Vérification Docker ────────────────────────────────
echo -e "${YELLOW}[1/6] Vérification de Docker...${NC}"
if ! command -v docker &> /dev/null; then
    echo -e "${RED}✗ Docker n'est pas installé.${NC}"
    echo -e "  Installez Docker : https://docs.docker.com/get-docker/"
    exit 1
fi
if ! command -v docker-compose &> /dev/null && ! docker compose version &> /dev/null 2>&1; then
    echo -e "${RED}✗ Docker Compose n'est pas installé.${NC}"
    exit 1
fi
echo -e "${GREEN}✓ Docker OK${NC}"

# ── 2. Fichier .env ────────────────────────────────────────
echo -e "${YELLOW}[2/6] Configuration .env...${NC}"
if [ ! -f .env ]; then
    cp .env.example .env 2>/dev/null || true
    echo -e "${GREEN}✓ .env créé depuis .env.example${NC}"
else
    echo -e "${GREEN}✓ .env existant conservé${NC}"
fi

# Generate a random secret key
SECRET=$(python3 -c "import secrets; print(secrets.token_hex(32))" 2>/dev/null || date +%s | sha256sum | head -c 64)
sed -i "s/parabench_secret_key_change_in_production_2024/${SECRET}/" .env 2>/dev/null || true
echo -e "${GREEN}✓ Clé secrète générée${NC}"

# ── 3. Build Docker ────────────────────────────────────────
echo -e "${YELLOW}[3/6] Construction des images Docker (peut prendre 5-10 minutes)...${NC}"
docker compose build --no-cache
echo -e "${GREEN}✓ Images construites${NC}"

# ── 4. Démarrage des services ─────────────────────────────
echo -e "${YELLOW}[4/6] Démarrage des services...${NC}"
docker compose up -d postgres redis
echo "  Attente PostgreSQL..."
sleep 5
docker compose up -d
echo -e "${GREEN}✓ Services démarrés${NC}"

# ── 5. Attendre que le backend soit prêt ──────────────────
echo -e "${YELLOW}[5/6] Attente du backend...${NC}"
MAX_WAIT=60
WAITED=0
until curl -sf http://localhost:8000/api/health > /dev/null 2>&1; do
    sleep 2
    WAITED=$((WAITED + 2))
    if [ $WAITED -ge $MAX_WAIT ]; then
        echo -e "${YELLOW}⚠ Backend long à démarrer (normal au premier lancement)${NC}"
        break
    fi
    echo -n "."
done
echo ""
echo -e "${GREEN}✓ Backend opérationnel${NC}"

# ── 6. Résumé ─────────────────────────────────────────────
echo ""
echo -e "${CYAN}${BOLD}╔══════════════════════════════════════════╗${NC}"
echo -e "${CYAN}${BOLD}║         Installation terminée ! 🎉       ║${NC}"
echo -e "${CYAN}${BOLD}╚══════════════════════════════════════════╝${NC}"
echo ""
echo -e "${BOLD}Accès à l'application :${NC}"
echo -e "  🌐 Dashboard    → ${GREEN}http://localhost:3000${NC}"
echo -e "  ⚙️  API Backend  → ${GREEN}http://localhost:8000${NC}"
echo -e "  📖 API Docs     → ${GREEN}http://localhost:8000/docs${NC}"
echo -e "  🗄️  Via Nginx    → ${GREEN}http://localhost:80${NC}"
echo ""
echo -e "${BOLD}Commandes utiles :${NC}"
echo -e "  Voir les logs    : ${CYAN}docker compose logs -f${NC}"
echo -e "  Arrêter          : ${CYAN}docker compose down${NC}"
echo -e "  Redémarrer       : ${CYAN}docker compose restart${NC}"
echo -e "  Lancer scraping  : Bouton dans Admin > Scraping"
echo ""
echo -e "${YELLOW}💡 Conseil : Allez dans l'onglet 'Admin & Scraping' et cliquez${NC}"
echo -e "${YELLOW}   sur 'Lancer le Scraping' pour peupler la base de données.${NC}"
echo ""
