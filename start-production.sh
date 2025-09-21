#!/bin/bash

# Production startup script for Render.com
echo "Starting Web Terminal in production mode..."

# Set production environment
export FLASK_ENV=production

# Create sandbox directory if it doesn't exist
mkdir -p /app/sandbox

# Initialize sandbox with sample files if empty
if [ ! "$(ls -A /app/sandbox)" ]; then
    echo "Initializing sandbox with sample files..."
    echo "Welcome to the web terminal sandbox!" > /app/sandbox/readme.txt
    echo "This is a safe environment for file operations." >> /app/sandbox/readme.txt
    echo '{"name": "web-terminal", "version": "1.0.0"}' > /app/sandbox/config.json
    echo "Sample log entry" > /app/sandbox/sample.log
    echo "Hello world!" > /app/sandbox/file1.txt
    echo "test" > /app/sandbox/kek
fi

# Start the application
cd /app
python backend/main.py