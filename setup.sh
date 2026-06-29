#!/bin/bash

echo "=========================================="
echo "  Gesture Media Controller Setup Script   "
echo "=========================================="

# 1. Check if Python 3 is installed
if ! command -v python3 &> /dev/null; then
    echo "Error: Python 3 is not installed. Please install it first."
    exit 1
fi

# 2. Create virtual environment if it doesn't exist
if [ ! -d ".venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv .venv
else
    echo "Virtual environment already exists."
fi

# 3. Activate environment and install dependencies from requirements.txt
echo "Installing dependencies..."
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt

# 4. Check for model file
if [ ! -f "hand_landmarker.task" ]; then
    echo ""
    echo "⚠️  Warning: 'hand_landmarker.task' not found in project directory."
    echo "Please download the model from Google MediaPipe and place it in this folder."
    echo "Download URL: https://storage.googleapis.com/mediapipe-models/hand_landmarker/hand_landmarker/float16/1/hand_landmarker.task"
else
    echo "✅ 'hand_landmarker.task' detected."
fi

echo ""
echo "=========================================="
echo "Setup Complete! To start the program, run:"
echo "source .venv/bin/activate && python main.py"
echo "=========================================="