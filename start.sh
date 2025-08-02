#!/bin/bash

# Deployment Lab Start Script

echo "Starting Deployment Lab..."

# Create logs directory if it doesn't exist
mkdir -p logs

# Kill any existing processes
pkill -f "next start"
pkill -f uvicorn
pkill -f cloudflared

# Wait for processes to stop
sleep 2

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
echo "Deployment Lab started successfully!"
echo "Frontend: http://localhost:3000"
echo "Backend API: http://localhost:8000"
echo "Domain: https://deployment-lab.ao2395.com"
echo ""
echo "To monitor logs:"
echo "  Frontend: tail -f logs/frontend.log"
echo "  Backend:  tail -f logs/backend.log"
echo "  Tunnel:   tail -f logs/tunnel.log"
echo ""
echo "To stop: ./stop.sh"