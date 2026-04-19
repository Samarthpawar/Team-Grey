#!/bin/bash
# ============================================================
#  CRISIS-X AI — Start Script
#  Run this from the project root: bash start.sh
# ============================================================

echo ""
echo "  ╔═══════════════════════════════════╗"
echo "  ║        CRISIS-X AI v2.0           ║"
echo "  ║   Financial Risk Intelligence     ║"
echo "  ╚═══════════════════════════════════╝"
echo ""

cd "$(dirname "$0")/backend"

# Check Python
if ! command -v python3 &> /dev/null; then
    echo "❌  Python 3 not found. Please install Python 3.9+"
    exit 1
fi

# Create venv if needed
if [ ! -d "venv" ]; then
    echo "📦  Creating virtual environment..."
    python3 -m venv venv
fi

# Activate
source venv/bin/activate 2>/dev/null || source venv/Scripts/activate 2>/dev/null

# Install deps
echo "📦  Installing dependencies..."
pip install -r requirements.txt -q

# Check .env
if [ ! -f ".env" ]; then
    cp .env.example .env 2>/dev/null || true
    echo "⚠️   Created .env from template. Edit backend/.env to add your API keys."
fi

echo ""
echo "✅  Starting CRISIS-X AI backend..."
echo "    Backend API : http://localhost:5000"
echo "    API Docs    : http://localhost:5000/docs"
echo "    Database    : backend/crisis_x.db"
echo ""
echo "    Demo login  : demo@crisisx.ai / demo1234"
echo ""
echo "    Open login.html in your browser, or serve the frontend:"
echo "    cd frontend && python3 -m http.server 8080"
echo "    Then visit: http://localhost:8080/login.html"
echo ""

python3 main.py
