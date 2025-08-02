#!/bin/bash

# Deployment Lab Process Monitor

echo "🔍 Deployment Lab Process Monitor"
echo "================================="

check_process() {
    local name=$1
    local pidfile=$2
    local port=$3
    
    if [ -f "$pidfile" ]; then
        local pid=$(cat "$pidfile")
        if kill -0 "$pid" 2>/dev/null; then
            if [ -n "$port" ] && lsof -i ":$port" > /dev/null 2>&1; then
                echo "✅ $name (PID: $pid) - Running on port $port"
            elif [ -z "$port" ]; then
                echo "✅ $name (PID: $pid) - Running"
            else
                echo "⚠️  $name (PID: $pid) - Process alive but port $port not bound"
            fi
            return 0
        else
            echo "❌ $name - Process $pid not found"
            rm -f "$pidfile"
            return 1
        fi
    else
        echo "❌ $name - No PID file found"
        return 1
    fi
}

echo "Process Status:"
check_process "Backend" "logs/backend.pid" "8000"
check_process "Frontend" "logs/frontend.pid" "3000"  
check_process "Tunnel" "logs/tunnel.pid"

echo ""
echo "Port Status:"
for port in 3000 8000; do
    if lsof -i ":$port" > /dev/null 2>&1; then
        process=$(lsof -i ":$port" | tail -n 1 | awk '{print $1 " (PID: " $2 ")"}')
        echo "Port $port: $process"
    else
        echo "Port $port: FREE"
    fi
done

echo ""
echo "Recent Log Errors:"
echo "Frontend errors:"
if [ -f "logs/frontend.log" ]; then
    grep -i "error\|failed\|exception" logs/frontend.log | tail -n 3 || echo "No recent errors"
else
    echo "No frontend log file"
fi

echo ""
echo "Backend errors:"
if [ -f "logs/backend.log" ]; then
    grep -i "error\|failed\|exception" logs/backend.log | tail -n 3 || echo "No recent errors"
else
    echo "No backend log file"
fi

echo ""
echo "Commands:"
echo "  Restart all: ./start.sh"
echo "  View logs: ./logs.sh"
echo "  Stop all: ./stop.sh"