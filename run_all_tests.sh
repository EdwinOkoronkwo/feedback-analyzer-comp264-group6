#!/bin/bash

# Set Python Path to current directory
export PYTHONPATH=$PYTHONPATH:.

echo "---------------------------------------"
echo "🚀 STARTING FULL N-TIER SYSTEM TEST"
echo "---------------------------------------"

# List of tests to run
TESTS=(
    "tests/test_sanitizer.py"
    "tests/test_security.py"
    "tests/test_translator.py"
    "tests/test_sentiment.py"
    "tests/test_persistence.py"
)

for test in "${TESTS[@]}"; do
    echo "🏃 Running: $test"
    python3 "$test"
    if [ $? -eq 0 ]; then
        echo "✅ Passed"
    else
        echo "❌ FAILED"
        exit 1
    fi
    echo "---------------------------------------"
done

echo "🎉 ALL LAYERS VERIFIED SUCCESSFULLY!"