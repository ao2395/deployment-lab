#!/bin/bash

# Deployment Lab Start Script

echo "Starting Deployment Lab..."

# Create logs directory if it doesn't exist
mkdir -p logs

# Kill any existing processes (ignore errors if processes don't exist)
pkill -f "next start" 2>/dev/null || true
pkill -f "next-server" 2>/dev/null || true
pkill -f uvicorn 2>/dev/null || true
pkill -f cloudflared 2>/dev/null || true

# Force kill anything on port 3000
echo "Freeing port 3000..."
sudo fuser -k 3000/tcp 2>/dev/null || true

# Wait for processes to stop
sleep 3

# Verify port 3000 is actually free
if lsof -i :3000 > /dev/null 2>&1; then
    echo "⚠️  Port 3000 still in use after cleanup. Trying harder..."
    sudo pkill -f next-server 2>/dev/null || true
    sudo fuser -k 3000/tcp 2>/dev/null || true
    sleep 2
    
    if lsof -i :3000 > /dev/null 2>&1; then
        echo "❌ Could not free port 3000. Please check manually:"
        echo "   sudo lsof -i :3000"
        echo "   sudo fuser -k 3000/tcp"
        exit 1
    fi
fi
echo "✅ Port 3000 is free"

# Start FastAPI backend
echo "Starting FastAPI backend on port 8000..."
cd api
nohup poetry run uvicorn main:app --host 0.0.0.0 --port 8000 --reload > ../logs/backend.log 2>&1 &
BACKEND_PID=$!
echo "Backend started with PID: $BACKEND_PID"

# Go back to root directory
cd ..

# Build and start Next.js frontend
echo "Building Next.js frontend..."
npm run build

echo "Starting Next.js frontend on port 3000..."
nohup npx next start -H 0.0.0.0 -p 3000 > logs/frontend.log 2>&1 &
FRONTEND_PID=$!
echo "Frontend started with PID: $FRONTEND_PID"

# Wait a moment and check if frontend actually started
sleep 3
if ! kill -0 $FRONTEND_PID 2>/dev/null; then
    echo "❌ Frontend failed to start! Check logs/frontend.log"
    echo "Frontend error:"
    tail -n 10 logs/frontend.log
    echo ""
    echo "Frontend exit code: $?"
else
    echo "✅ Frontend is running"
fi

# Start Cloudflare tunnel
echo "Starting Cloudflare tunnel..."
nohup cloudflared tunnel --config ~/.cloudflared/config.yml run > logs/tunnel.log 2>&1 &
TUNNEL_PID=$!
echo "Tunnel started with PID: $TUNNEL_PID"

# Save PIDs for stop script
echo $BACKEND_PID > logs/backend.pid
echo $FRONTEND_PID > logs/frontend.pid
echo $TUNNEL_PID > logs/tunnel.pid

echo ""
echo "🚀 Deployment Lab Status:"
echo "=========================="

# Check if services are actually running
FRONTEND_RUNNING=false
BACKEND_RUNNING=false
TUNNEL_RUNNING=false

if kill -0 $FRONTEND_PID 2>/dev/null && lsof -i :3000 > /dev/null 2>&1; then
    echo "✅ Frontend: http://localhost:3000"
    FRONTEND_RUNNING=true
else
    echo "❌ Frontend: Failed to start"
fi

if kill -0 $BACKEND_PID 2>/dev/null && lsof -i :8000 > /dev/null 2>&1; then
    echo "✅ Backend API: http://localhost:8000"
    BACKEND_RUNNING=true
else
    echo "❌ Backend: Failed to start"
fi

if kill -0 $TUNNEL_PID 2>/dev/null; then
    echo "✅ Tunnel: https://deployment-lab.ao2395.com"
    TUNNEL_RUNNING=true
else
    echo "❌ Tunnel: Failed to start"
fi

echo ""
if $FRONTEND_RUNNING && $BACKEND_RUNNING && $TUNNEL_RUNNING; then
    echo "🎉 All services started successfully!"
    echo "🌐 Visit: https://deployment-lab.ao2395.com"
else
    echo "⚠️  Some services failed to start. Check logs:"
    echo "   ./logs.sh"
fi

echo ""
echo "Commands:"
echo "  View logs: ./logs.sh"
echo "  Check status: ./status.sh" 
echo "  Stop services: ./stop.sh"