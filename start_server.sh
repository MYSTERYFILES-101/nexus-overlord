#!/bin/bash
#
# NEXUS OVERLORD v2.0 - Server Start Script
# Starts Flask server with correct PYTHONPATH for multi-agent workflow
#

cd /home/nexus/nexus-overlord

# Activate venv
source venv/bin/activate

# Set PYTHONPATH so background threads can import 'app' module
export PYTHONPATH=/home/nexus/nexus-overlord:$PYTHONPATH

# Start server
python app/main.py
