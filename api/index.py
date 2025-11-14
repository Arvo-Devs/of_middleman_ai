"""
Vercel serverless function entry point for Flask app
"""
import sys
import os

# Add parent directory to path to import app
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, parent_dir)

from app import app

# Export the Flask app as the handler for Vercel
# Vercel will automatically detect this
handler = app

