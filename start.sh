#!/bin/bash

# Web Terminal Startup Script
# This script sets up and runs the web terminal application

set -e

echo "🚀 Web Terminal Startup Script"
echo "==============================="

# Check if we're in the correct directory
if [ ! -f "project.md" ]; then
    echo "❌ Please run this script from the project root directory"
    exit 1
fi

# Check if .env file exists
if [ ! -f ".env" ]; then
    echo "❌ .env file not found. Please create it with your API keys:"
    echo "   SUPABASE_URL=your_supabase_url"
    echo "   SUPABASE_API_KEY=your_supabase_api_key"
    echo "   GEMINI_API_KEY=your_gemini_api_key"
    exit 1
fi

# Check if Python 3 is installed
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is not installed. Please install Python 3.8 or higher."
    exit 1
fi

echo "✅ Python 3 found: $(python3 --version)"

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
echo "🔧 Activating virtual environment..."
source venv/bin/activate

# Install dependencies
echo "📚 Installing dependencies..."
pip install --upgrade pip
pip install -r requirements.txt

# Check if all backend modules exist
echo "🔍 Checking backend modules..."
required_files=(
    "backend/main.py"
    "backend/command_parser.py"
    "backend/command_executor.py"
    "backend/system_monitor.py"
    "backend/database.py"
    "backend/ai_interpreter.py"
    "backend/security.py"
)

for file in "${required_files[@]}"; do
    if [ ! -f "$file" ]; then
        echo "❌ Missing required file: $file"
        exit 1
    fi
done

echo "✅ All backend modules found"

# Check if frontend files exist
echo "🔍 Checking frontend files..."
required_frontend=(
    "frontend/index.html"
    "frontend/static/style.css"
    "frontend/static/terminal.js"
)

for file in "${required_frontend[@]}"; do
    if [ ! -f "$file" ]; then
        echo "❌ Missing required file: $file"
        exit 1
    fi
done

echo "✅ All frontend files found"

# Display configuration info
echo ""
echo "🔧 Configuration:"
echo "   - Backend: Flask + SocketIO"
echo "   - Frontend: HTML5 + CSS3 + JavaScript"
echo "   - Database: Supabase PostgreSQL"
echo "   - AI: Google Gemini"
echo "   - Security: Rate limiting + Input validation"
echo ""

# Start the application
echo "🎬 Starting Web Terminal..."
echo "   - Server will start on http://localhost:5000"
echo "   - Press Ctrl+C to stop the server"
echo ""

cd backend
export FLASK_ENV=development
export FLASK_DEBUG=1
python main.py