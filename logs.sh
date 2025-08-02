#!/bin/bash

# Deployment Lab Logs Viewer

if [ ! -d "logs" ]; then
    echo "Logs directory not found. Are the services running?"
    exit 1
fi

echo "Deployment Lab Logs Viewer"
echo "=========================="
echo ""
echo "1. Frontend logs"
echo "2. Backend logs" 
echo "3. Tunnel logs"
echo "4. All logs (tail -f)"
echo "5. Exit"
echo ""
read -p "Choose an option (1-5): " choice

case $choice in
    1)
        echo "Frontend logs:"
        echo "=============="
        if [ -f "logs/frontend.log" ]; then
            tail -f logs/frontend.log
        else
            echo "Frontend log file not found"
        fi
        ;;
    2)
        echo "Backend logs:"
        echo "============="
        if [ -f "logs/backend.log" ]; then
            tail -f logs/backend.log
        else
            echo "Backend log file not found"
        fi
        ;;
    3)
        echo "Tunnel logs:"
        echo "============"
        if [ -f "logs/tunnel.log" ]; then
            tail -f logs/tunnel.log
        else
            echo "Tunnel log file not found"
        fi
        ;;
    4)
        echo "All logs (Press Ctrl+C to exit):"
        echo "================================"
        tail -f logs/*.log 2>/dev/null || echo "No log files found"
        ;;
    5)
        echo "Exiting..."
        exit 0
        ;;
    *)
        echo "Invalid option"
        exit 1
        ;;
esac