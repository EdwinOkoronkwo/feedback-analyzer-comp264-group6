#!/bin/bash

echo "🧼 Starting Project Cleanup..."

# 1. Create Clean Structure
mkdir -p scripts tests storage/db storage/audio storage/uploads logs

# 2. Move Core Infrastructure & Admin scripts
# These are things you run once or for maintenance
mv deploy_all.py destroy_all.py setup_infra.py repair_cloud_permissions.sh scripts/ 2>/dev/null
mv create_admin_user.py seed_admin.py scripts/ 2>/dev/null
mv local_api.py scripts/ 2>/dev/null

# 3. Move Testing & Pipeline verification
mv test_pipeline.py run_all_tests.sh run_pipeline.py tests/ 2>/dev/null

# 4. Consolidate Local Data
mv shared-local-instance.db storage/db/ 2>/dev/null
mv audio_outputs/* storage/audio/ 2>/dev/null
mv uploads/* storage/uploads/ 2>/dev/null

# 5. Remove Debug Clutter (The JSON "Noise")
echo "🗑️  Removing temporary debug files..."
rm -f clean_res.json master_debug.json ocr_debug.json res.json response.json \
      notification.json summary_debug.json trigger_test.txt wake_up.txt \
      Untitled coffee_joke.mp3 output_summary.mp3 feedback_backup.json \
      dynamodb-local-metadata.json

# 6. Clean up redundant environment files (Keeping requirements.txt as primary)
rm -f Pipfile Pipfile.lock

echo "✨ Cleanup Complete! Your root directory is now professional."