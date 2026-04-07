#!/bin/bash
# setup_dev.sh - Configuración rápida para el equipo

echo "🚀 Configurando entorno de desarrollo de Tars..."

# 1. Crear carpeta de certificados si no existe
mkdir -p certs

# 2. Generar certificados locales (para que el SSL no truene)
if [ ! -f certs/key.pem ]; then
    openssl req -x509 -newkey rsa:4096 -keyout certs/key.pem -out certs/cert.pem -sha256 -days 365 -nodes -subj "/CN=localhost"
    echo "✅ Certificados de desarrollo creados."
fi

# 3. Crear un .env básico si no existe
if [ ! -f .env ]; then
    echo "CERTS_PATH=./certs" > .env
    echo "✅ Archivo .env configurado para modo local."
fi

echo "¡Listo! Ahora puedes correr: docker compose up -d --build"