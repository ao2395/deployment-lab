#!/bin/bash

# Deployment Lab Stop Script

echo "Stopping Deployment Lab..."

# Kill processes by PID if available
if [ -f logs/backend.pid ]; then
    BACKEND_PID=$(cat logs/backend.pid)
    echo "Stopping backend (PID: $BACKEND_PID)..."
    kill $BACKEND_PID 2>/dev/null
    rm logs/backend.pid
fi

if [ -f logs/frontend.pid ]; then
    FRONTEND_PID=$(cat logs/frontend.pid)
    echo "Stopping frontend (PID: $FRONTEND_PID)..."
    kill $FRONTEND_PID 2>/dev/null
    rm logs/frontend.pid
fi

if [ -f logs/tunnel.pid ]; then
    TUNNEL_PID=$(cat logs/tunnel.pid)
    echo "Stopping tunnel (PID: $TUNNEL_PID)..."
    kill $TUNNEL_PID 2>/dev/null
    rm logs/tunnel.pid
fi

# Kill any remaining processes by name
echo "Cleaning up any remaining processes..."
pkill -f "next start"
pkill -f "uvicorn main:app"
pkill -f "cloudflared tunnel"

# Wait for processes to stop
sleep 2

echo "Deployment Lab stopped successfully!"

# Show remaining processes if any
REMAINING=$(ps aux | grep -E "(next|uvicorn|cloudflared)" | grep -v grep | wc -l)
if [ $REMAINING -gt 0 ]; then
    echo "Warning: Some processes may still be running:"
    ps aux | grep -E "(next|uvicorn|cloudflared)" | grep -v grep
fi