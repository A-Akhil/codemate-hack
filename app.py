#!/usr/bin/env python3
"""
Render.com entry point for the web terminal application.
This file imports the Flask app from backend/main.py for gunicorn compatibility.
"""

import sys
import os

# Add backend directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

# Import the Flask app from main.py
from main import app

# Make the app available for gunicorn
if __name__ == '__main__':
    app.run()