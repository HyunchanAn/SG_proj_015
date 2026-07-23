#!/bin/bash
# ========================================================
# Boot All SG Adhesion Nexus Microservices (Mac OS)
# ========================================================

echo "Initializing Environment..."
export HF_TOKEN=$(cat ~/.cache/huggingface/token)
export KMP_DUPLICATE_LIB_OK=TRUE
BASE_DIR="/Users/hyunchanan/Documents/GitHub"
export PYTHONPATH="$BASE_DIR/SG_sys/shared_schemas:$PYTHONPATH"
LOG_DIR="$BASE_DIR/SG_proj_015/demo_ui/logs"
mkdir -p "$LOG_DIR"

start_service() {
    PROJ=$1
    PORT=$2
    MODULE=$3
    echo "Booting $PROJ on port $PORT..."
    cd "$BASE_DIR/$PROJ" || exit
    # Run uvicorn in the background and redirect output to a specific log file
    nohup /opt/homebrew/Caskroom/miniconda/base/bin/python3 -m uvicorn $MODULE --host 0.0.0.0 --port $PORT > "$LOG_DIR/${PROJ}_${PORT}.log" 2>&1 &
}

echo "Starting Backend Microservices..."

start_service "SG_proj_001" "8001" "api.main:app"
start_service "SG_proj_002" "8002" "api.main:app"
start_service "SG_proj_003" "8003" "api:app"
start_service "SG_proj_006" "8006" "api:app"
start_service "SG_proj_007" "8007" "api:app"
start_service "SG_proj_009" "8009" "api:app"
start_service "SG_proj_010" "8010" "src.main:app"
start_service "SG_proj_011" "8011" "src.main:app"
start_service "SG_proj_012" "8012" "src.main:app"
start_service "SG_proj_013" "8013" "src.main:app"
start_service "SG_proj_014" "8024" "src.main:app"

echo "========================================================"
echo "All backend microservices (001~014) have been scheduled to start."
echo "Wait a few seconds for Uvicorn to bind the ports before using the UI."
echo "Check $LOG_DIR for individual service logs."
echo "========================================================"
