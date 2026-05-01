#!/bin/bash

# 1. Navigate to the git repository
cd /home/denis/findabook

# 2. Run the Python miner using the venv Python
/home/denis/venv/bin/python3 main.py

# 3. Check if the Python script succeeded before pushing
if [ $? -eq 0 ]; then
    echo "Python script finished. Pushing to GitHub..."
    git add index.html
    git commit -m "Daily scrolls update: $(date +'%Y-%m-%d')"
    git push origin main
else
    echo "Error: Python script failed. Aborting git push."
    exit 1
fi

