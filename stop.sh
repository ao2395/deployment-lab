#!/bin/bash

# Deployment Lab Stop Script

echo "Stopping Deployment Lab..."

# Kill processes by PID if available
if [ -f logs/backend.pid ]; then
    BACKEND_PID=$(cat logs/backend.pid)
    echo "Stopping backend (PID: $BACKEND_PID)..."
    kill $BACKEND_PID 2>/dev/null || true
    rm logs/backend.pid 2>/dev/null || true
fi

if [ -f logs/frontend.pid ]; then
    FRONTEND_PID=$(cat logs/frontend.pid)
    echo "Stopping frontend (PID: $FRONTEND_PID)..."
    kill $FRONTEND_PID 2>/dev/null || true
    rm logs/frontend.pid 2>/dev/null || true
fi

if [ -f logs/tunnel.pid ]; then
    TUNNEL_PID=$(cat logs/tunnel.pid)
    echo "Stopping tunnel (PID: $TUNNEL_PID)..."
    kill $TUNNEL_PID 2>/dev/null || true
    rm logs/tunnel.pid 2>/dev/null || true
fi

# Kill any remaining processes by name (ignore errors)
echo "Cleaning up any remaining processes..."
pkill -f "next start" 2>/dev/null || true
pkill -f "uvicorn main:app" 2>/dev/null || true
pkill -f "cloudflared tunnel" 2>/dev/null || true

# Wait for processes to stop
sleep 2

echo "Deployment Lab stopped successfully!"

# Show remaining processes if any
REMAINING=$(ps aux | grep -E "(next|uvicorn|cloudflared)" | grep -v grep | wc -l)
if [ $REMAINING -gt 0 ]; then
    echo "Warning: Some processes may still be running:"
    ps aux | grep -E "(next|uvicorn|cloudflared)" | grep -v grep
fi