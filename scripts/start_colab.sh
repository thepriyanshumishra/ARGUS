#!/bin/bash
# ==============================================================================
# ARGUS — Colab/Kaggle GPU Server Startup Script
# ==============================================================================
set -e

echo "=================================================================="
echo "    ARGUS Server Initialization (GPU/Colab/Kaggle Environment)   "
echo "=================================================================="

# 1. Install Ubuntu system packages (GDAL, Fiona, Rtree prerequisites)
echo "--> Installing Ubuntu system dependencies..."
sudo apt-get update -y
sudo apt-get install -y binutils libproj-dev gdal-bin python3-gdal libgdal-dev rtree-common wget curl

# 2. Install python packages
echo "--> Installing Python packages..."
pip install --upgrade pip
pip install geopandas osmnx shapely fiona rasterio networkx scikit-image rtree albumentations segmentation-models-pytorch uvicorn fastapi python-multipart requests PyYAML omegaconf

# 3. Create necessary workspace folders
echo "--> Preparing workspace directories..."
mkdir -p /tmp/argus_workspace/input
mkdir -p /tmp/argus_workspace/results
mkdir -p assets/checkpoints

# 4. Download SAM weights if missing
if [ ! -f "assets/checkpoints/sam_vit_b_01ec64.pth" ]; then
    echo "--> Downloading SAM base checkpoint..."
    wget -q https://dl.fbaipublicfiles.com/segment_anything/sam_vit_b_01ec64.pth -O assets/checkpoints/sam_vit_b_01ec64.pth
fi

# 5. Download Cloudflare Tunnel (cloudflared)
if [ ! -f "./cloudflared" ]; then
    echo "--> Downloading Cloudflare Tunnel..."
    wget -q https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64 -O cloudflared
    chmod +x cloudflared
fi

# 6. Start the FastAPI backend server in the background
echo "--> Starting FastAPI server on port 8000..."
export ARGUS_ENV="colab"
export ARGUS_PASSWORD=${ARGUS_PASSWORD:-"argus2026"}
python -m uvicorn src.argus.api.main:app --host 0.0.0.0 --port 8000 --reload &

# Wait for server to bind
sleep 3

# 7. Start Cloudflare Tunnel
echo "=================================================================="
echo "    STARTING TUNNEL — CLICK THE CHOSEN LINK IN YOUR BROWSER      "
echo "=================================================================="
./cloudflared tunnel --url http://localhost:8000
