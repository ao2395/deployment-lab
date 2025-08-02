#!/bin/bash

# Deployment Lab Request Monitor
# Shows all HTTP requests in real-time

echo "🔍 Deployment Lab Request Monitor"
echo "================================="
echo "Monitoring all HTTP requests..."
echo "Press Ctrl+C to stop"
echo ""

# Function to colorize output
colorize() {
    local color=$1
    shift
    echo -e "\033[${color}m$@\033[0m"
}

# Start monitoring multiple log sources simultaneously
{
    # Monitor backend access logs (simple format)
    tail -f logs/backend.log | grep -E "(GET|POST|PUT|DELETE|PATCH)" --line-buffered | grep -v "Headers" | while read line; do
        colorize "32" "[API] $line"
    done &
    
    # Monitor nginx access logs (if they exist)
    if [ -f /var/log/nginx/access.log ]; then
        sudo tail -f /var/log/nginx/access.log | while read line; do
            colorize "34" "[NGINX] $line"
        done &
    fi
    
    # Monitor frontend logs for any requests
    tail -f logs/frontend.log | grep -E "(GET|POST|PUT|DELETE|PATCH|fetch|axios)" --line-buffered | while read line; do
        colorize "35" "[FRONTEND] $line"
    done &
    
    # Monitor tunnel logs for connection activity
    tail -f logs/tunnel.log | grep -E "(request|response|connection)" --line-buffered | while read line; do
        colorize "36" "[TUNNEL] $line"
    done &
    
    # Keep the script running
    wait
}