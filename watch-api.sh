#!/bin/bash

# Backend API Request Monitor
# Shows only backend API requests

# Kill any existing watch processes to prevent duplicates
pkill -f "tail.*logs/.*log" 2>/dev/null || true
sleep 1

echo "🔍 Backend API Monitor"
echo "====================="
echo "Monitoring backend API requests only..."
echo "Press Ctrl+C to stop"
echo ""

# Monitor only backend access logs
tail -f logs/backend.log | grep -E "(GET|POST|PUT|DELETE|PATCH)" --line-buffered | while read line; do
    echo "[API] $line"
done