#!/bin/bash

# Deployment Lab Keep-Alive Monitor

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "🔄 Starting Deployment Lab keep-alive monitor..."
echo "This will check every 30 seconds and restart failed services."
echo "Press Ctrl+C to stop monitoring."
echo ""

while true; do
    # Check if services are running
    RESTART_NEEDED=false
    
    # Check backend
    if [ -f "logs/backend.pid" ]; then
        BACKEND_PID=$(cat logs/backend.pid)
        if ! kill -0 "$BACKEND_PID" 2>/dev/null || ! sudo netstat -tuln | grep -q :8000; then
            echo "$(date): ❌ Backend died, restarting..."
            cd api
            nohup poetry run uvicorn main:app --host 0.0.0.0 --port 8000 --reload > ../logs/backend.log 2>&1 &
            echo $! > ../logs/backend.pid
            cd ..
            RESTART_NEEDED=true
        fi
    else
        echo "$(date): ❌ Backend not running, starting..."
        cd api
        nohup poetry run uvicorn main:app --host 0.0.0.0 --port 8000 --reload > ../logs/backend.log 2>&1 &
        echo $! > ../logs/backend.pid
        cd ..
        RESTART_NEEDED=true
    fi
    
    # Check frontend
    if [ -f "logs/frontend.pid" ]; then
        FRONTEND_PID=$(cat logs/frontend.pid)
        if ! kill -0 "$FRONTEND_PID" 2>/dev/null || ! sudo netstat -tuln | grep -q :3000; then
            echo "$(date): ❌ Frontend died, restarting..."
            nohup npx next start -H 0.0.0.0 -p 3000 > logs/frontend.log 2>&1 &
            echo $! > logs/frontend.pid
            RESTART_NEEDED=true
        fi
    else
        echo "$(date): ❌ Frontend not running, starting..."
        nohup npx next start -H 0.0.0.0 -p 3000 > logs/frontend.log 2>&1 &
        echo $! > logs/frontend.pid
        RESTART_NEEDED=true
    fi
    
    # Check tunnel
    if [ -f "logs/tunnel.pid" ]; then
        TUNNEL_PID=$(cat logs/tunnel.pid)
        if ! kill -0 "$TUNNEL_PID" 2>/dev/null; then
            echo "$(date): ❌ Tunnel died, restarting..."
            nohup cloudflared tunnel --config ~/.cloudflared/config.yml run > logs/tunnel.log 2>&1 &
            echo $! > logs/tunnel.pid
            RESTART_NEEDED=true
        fi
    else
        echo "$(date): ❌ Tunnel not running, starting..."
        nohup cloudflared tunnel --config ~/.cloudflared/config.yml run > logs/tunnel.log 2>&1 &
        echo $! > logs/tunnel.pid
        RESTART_NEEDED=true
    fi
    
    if [ "$RESTART_NEEDED" = true ]; then
        echo "$(date): 🔄 Services restarted"
    else
        echo "$(date): ✅ All services running"
    fi
    
    sleep 30
done