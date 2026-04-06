#!/bin/bash

echo "🛑 Cleaning up VMware Local Resources..."

# 1. Kill any process running on Port 8000 (The DynamoDB Engine)
PID=$(lsof -t -i:8000)
if [ -z "$PID" ]; then
    echo "ℹ️  No DynamoDB process found on port 8000."
else
    echo "💀 Killing DynamoDB process (PID: $PID)..."
    kill -9 $PID
fi

# 2. Optional: Wipe the database files if you want a TOTAL reset
# Warning: This deletes all users, metadata, and summaries!
# read -p "Do you want to wipe all local data? (y/n) " -n 1 -r
# if [[ $REPLY =~ ^[Yy]$ ]]; then
#    rm -rf /home/edwin/projects/feedback_analyzer/local_db_storage/*.db
#    echo -e "\n🔥 Local database files deleted."
# fi

echo "✨ Local environment is clean."