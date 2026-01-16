#!/bin/bash
# RedFlag-AI - Script de démarrage (Linux/Mac)

echo "============================================"
echo "  RedFlag-AI - Démarrage de l'application"
echo "============================================"
echo ""

# Vérification de Docker
if ! command -v docker &> /dev/null; then
    echo "❌ Docker n'est pas installé."
    echo "   Installez Docker : https://docs.docker.com/get-docker/"
    exit 1
fi

if ! command -v docker-compose &> /dev/null && ! docker compose version &> /dev/null; then
    echo "❌ Docker Compose n'est pas installé."
    exit 1
fi

# Détection de la commande docker compose
if docker compose version &> /dev/null; then
    COMPOSE="docker compose"
else
    COMPOSE="docker-compose"
fi

echo "✅ Docker détecté"
echo ""

# Construction et démarrage
echo "🔨 Construction des images Docker..."
$COMPOSE build

echo ""
echo "🚀 Démarrage des services..."
$COMPOSE up -d

echo ""
echo "============================================"
echo "  ✅ Application démarrée avec succès!"
echo "============================================"
echo ""
echo "  🌐 Interface Streamlit : http://localhost:8501"
echo ""
echo "  📋 Commandes utiles :"
echo "     - Voir les logs    : $COMPOSE logs -f"
echo "     - Arrêter          : $COMPOSE down"
echo "     - Triage CLI       : $COMPOSE run --rm cli"
echo ""
