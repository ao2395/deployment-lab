#!/bin/bash

# Deployment Lab Status Checker

echo "=== DEPLOYMENT LAB STATUS ==="
echo ""

echo "📱 Main App Status:"
echo "Frontend (port 3000): $(lsof -i :3000 | wc -l) processes"
echo "Backend (port 8000): $(lsof -i :8000 | wc -l) processes"
echo ""

echo "🌐 Nginx Status:"
sudo systemctl is-active nginx
echo "Configs available: $(ls /etc/nginx/sites-available/ | grep ao2395 | wc -l)"
echo "Configs enabled: $(ls /etc/nginx/sites-enabled/ | grep ao2395 | wc -l)"
echo ""

echo "🚇 Tunnel Status:"
if ps aux | grep -q "cloudflared tunnel"; then
    echo "✅ Tunnel is running"
else
    echo "❌ Tunnel is not running"
fi
echo ""

echo "🐳 Docker Deployments:"
echo "Running containers: $(docker ps | grep -v CONTAINER | wc -l)"
docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"
echo ""

echo "🌍 DNS Check (deployment-lab.ao2395.com):"
nslookup deployment-lab.ao2395.com | grep -A 2 "Name:"
echo ""

echo "🔗 Active Nginx Configs:"
for config in /etc/nginx/sites-enabled/*.ao2395.com; do
    if [ -f "$config" ]; then
        basename "$config"
    fi
done
echo ""

echo "📊 Port Usage:"
echo "Port 3000: $(lsof -i :3000 | tail -n +2 | wc -l) processes"
echo "Port 8000: $(lsof -i :8000 | tail -n +2 | wc -l) processes"
echo "Ports 3001-3010:"
for port in {3001..3010}; do
    if lsof -i :$port > /dev/null 2>&1; then
        echo "  Port $port: IN USE"
    fi
done