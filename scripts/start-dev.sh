#!/bin/bash
# ARGUS Development Environment Startup Script
# Starts: Real Graph API Server (port 9749) + Vite Dev Server (port 3001)

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Config
API_PORT=9749
VITE_PORT=3001
DASHBOARD_DIR="/Users/thedarkpcm/Desktop/Priyanshu/ARGUS/tools/dev-dashboard"
API_LOG="/tmp/argus-api.log"
VITE_LOG="/tmp/argus-vite.log"
PID_FILE="/tmp/argus-dev.pids"

echo -e "${BLUE}╔═══════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║     ARGUS Development Environment            ║${NC}"
echo -e "${BLUE}╚═══════════════════════════════════════════════╝${NC}"
echo ""

# Cleanup function
cleanup() {
    echo -e "\n${YELLOW}Shutting down...${NC}"
    if [[ -f "$PID_FILE" ]]; then
        while read pid; do
            kill "$pid" 2>/dev/null || true
        done < "$PID_FILE"
        rm -f "$PID_FILE"
    fi
    lsof -ti:$API_PORT | xargs kill -9 2>/dev/null || true
    lsof -ti:$VITE_PORT | xargs kill -9 2>/dev/null || true
    echo -e "${GREEN}Done.${NC}"
    exit 0
}

trap cleanup SIGINT SIGTERM EXIT

# Kill existing processes on our ports
echo -e "${YELLOW}Cleaning up existing processes...${NC}"
lsof -ti:$API_PORT | xargs kill -9 2>/dev/null || true
lsof -ti:$VITE_PORT | xargs kill -9 2>/dev/null || true
sleep 0.5

# Extract real graph data if not exists
if [[ ! -f "$DASHBOARD_DIR/real_graph_data.json" ]]; then
    echo -e "${BLUE}Extracting real graph from source code...${NC}"
    cd /Users/thedarkpcm/Desktop/Priyanshu/ARGUS
    python3 "$DASHBOARD_DIR/extract_real_graph.py" 2>&1 | tail -20
fi

# Start Real Graph API Server
echo -e "${BLUE}Starting Real Graph API Server on port $API_PORT...${NC}"
node "$DASHBOARD_DIR/real-api-server.js" > "$API_LOG" 2>&1 &
API_PID=$!
echo $API_PID > "$PID_FILE"

# Wait for API to be ready
for i in {1..10}; do
    if curl -s "http://localhost:$API_PORT/api/status" > /dev/null 2>&1; then
        echo -e "${GREEN}✓ API Server ready${NC}"
        break
    fi
    sleep 0.5
done

# Start Vite Dev Server
echo -e "${BLUE}Starting Vite Dev Server on port $VITE_PORT...${NC}"
cd "$DASHBOARD_DIR"
npx vite --host --port $VITE_PORT > "$VITE_LOG" 2>&1 &
VITE_PID=$!
echo $VITE_PID >> "$PID_FILE"

# Wait for Vite to be ready
for i in {1..20}; do
    if curl -s "http://localhost:$VITE_PORT" > /dev/null 2>&1; then
        echo -e "${GREEN}✓ Vite Dev Server ready${NC}"
        break
    fi
    sleep 0.5
done

echo ""
echo -e "${GREEN}═══════════════════════════════════════════${NC}"
echo -e "${GREEN}  ARGUS Dev Environment Running!${NC}"
echo -e "${GREEN}═══════════════════════════════════════════${NC}"
echo -e "  Dashboard: ${BLUE}http://localhost:$VITE_PORT${NC}"
echo -e "  API:       ${BLUE}http://localhost:$API_PORT/api/status${NC}"
echo -e "  Graph:     ${BLUE}http://localhost:$API_PORT/api/graph?project=ARGUS${NC}"
echo -e "  Reload:    ${BLUE}POST http://localhost:$API_PORT/api/reload${NC}"
echo ""
echo -e "${YELLOW}Press Ctrl+C to stop all services${NC}"
echo ""

# Show logs
tail -f "$API_LOG" "$VITE_LOG" 2>/dev/null &
TAIL_PID=$!

# Wait for interrupt
wait $TAIL_PID