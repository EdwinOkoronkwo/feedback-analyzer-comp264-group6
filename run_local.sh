#!/bin/bash

# --- CONFIGURATION ---
DB_PATH="/home/edwin/projects/feedback_analyzer/local_db_storage/"
JAR_PATH="/home/edwin/projects/feedback_analyzer/dynamodb_local/DynamoDBLocal.jar"
LIB_PATH="/home/edwin/projects/feedback_analyzer/dynamodb_local/DynamoDBLocal_lib"
PORT=8000

echo "🚀 [1/3] Starting DynamoDB Local Engine..."

# Start Java in the background and save its Process ID (PID)
java -Djava.library.path=$LIB_PATH -jar $JAR_PATH -sharedDb -dbPath $DB_PATH -port $PORT &
DB_PID=$!

# Wait for the engine to wake up
echo "⏳ Waiting for database to initialize on port $PORT..."
while ! nc -z localhost $PORT; do   
  sleep 1
done

echo "✅ Database Engine is Online (PID: $DB_PID)"

echo "🏗️  [2/3] Running Infrastructure Setup & Seeding..."
# This runs the setup script we made earlier to ensure Tables/Admin exist
python3 scripts/setup_local_env.py

echo "🖥️  [3/3] Launching Streamlit UI..."
# Use 'trap' to kill the Java engine when you hit Ctrl+C on the Streamlit app
trap "echo '🛑 Shutting down...'; kill $DB_PID; exit" SIGINT SIGTERM

streamlit run web/app.py