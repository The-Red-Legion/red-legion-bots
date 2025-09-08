#!/bin/bash

# Red Legion Mining System - Test Data Helper
# Quick script to set up and tear down test data for mining bot testing

echo "🔬 Red Legion Mining Test Data Helper"
echo "===================================="

# Check if we're in the right directory
if [ ! -f "quick_test_data.py" ]; then
    echo "❌ Error: quick_test_data.py not found. Run this script from the red-legion-bots directory."
    exit 1
fi

# Check if Python and psycopg2 are available
python3 -c "import psycopg2" 2>/dev/null
if [ $? -ne 0 ]; then
    echo "⚠️  psycopg2 not found. Installing..."
    pip3 install psycopg2-binary
fi

echo ""
echo "Available actions:"
echo "1. 🚀 Create test data and run interactive menu"
echo "2. 🧹 Quick cleanup (remove all test data)"
echo "3. 📊 Show current test data status"
echo ""

read -p "Select action (1-3): " choice

case $choice in
    1)
        echo "🚀 Starting interactive test data manager..."
        python3 quick_test_data.py
        ;;
    2)
        echo "🧹 Quick cleanup mode..."
        python3 -c "
from quick_test_data import QuickTestData
t = QuickTestData()
if t.connect():
    t.cleanup()
    t.close()
    print('✅ Cleanup complete!')
"
        ;;
    3)
        echo "📊 Showing test data status..."
        python3 -c "
from quick_test_data import QuickTestData
t = QuickTestData()
if t.connect():
    t.show_summary()
    t.close()
"
        ;;
    *)
        echo "❌ Invalid choice"
        exit 1
        ;;
esac

echo ""
echo "Done! 🎉"
