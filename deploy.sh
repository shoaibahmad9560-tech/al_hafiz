#!/bin/bash
set -e

echo "🚀 Starting Deployment: Al Hafiz Electronics WhatsApp Commerce..."

echo "📥 Pulling latest code..."
git pull origin main

echo "🏗️  Building Docker image..."
docker-compose build alhafiz-backend

echo "ℹ️  Reminder: No database migrations needed for Redis layer."

echo "🔄 Restarting containers..."
docker-compose up -d

echo "⏳ Waiting for services to initialize..."
sleep 5

echo "🩺 Running health check..."
HTTP_STATUS=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:5000/api/status/health)

if [ "$HTTP_STATUS" -eq 200 ]; then
    echo "✅ Health check passed (HTTP 200)!"
    echo "🎉 Deployment Successful!"
else
    echo "❌ Health check failed (HTTP $HTTP_STATUS)!"
    echo "Please check docker logs: docker-compose logs alhafiz-backend"
    exit 1
fi
