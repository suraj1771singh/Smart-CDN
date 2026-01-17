#!/bin/sh
set -e

echo "🚀 Starting enhanced edge server..."

# Start nginx in background
nginx -g 'daemon off;' &
NGINX_PID=$!

# Wait a bit for nginx to start
sleep 2

# Start log sender
echo "📡 Starting log sender..."
python3 /usr/local/bin/log_sender.py &
LOG_SENDER_PID=$!

# Function to handle shutdown
shutdown() {
    echo "🛑 Shutting down..."
    kill $LOG_SENDER_PID 2>/dev/null || true
    kill $NGINX_PID 2>/dev/null || true
    exit 0
}

# Trap signals
trap shutdown SIGTERM SIGINT

# Wait for processes
wait $NGINX_PID

