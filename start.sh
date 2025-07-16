#!/usr/bin/env bash
# Start script for Render with Chrome

# Download Chrome
apt update && apt install -y wget unzip
wget https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb
apt install -y ./google-chrome-stable_current_amd64.deb

# Launch FastAPI app
uvicorn main:app --host 0.0.0.0 --port 10000
