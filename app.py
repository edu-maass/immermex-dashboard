"""
Vercel entry point for Immermex Dashboard Backend
"""
import sys
import os

# Add backend directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

# Import the FastAPI app
from simple_upload import app

# Export the app for Vercel
__all__ = ['app']
