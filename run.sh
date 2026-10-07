#!/usr/bin/env bash
echo "========================================================"
echo "  🌿 GROUNDED: TouchGrass AI - Open-Source Outdoor Companion"
echo "========================================================"
echo ""
echo "Installing / checking requirements..."
pip install -r requirements.txt
echo ""
echo "Starting Grounded..."
python3 run.py
