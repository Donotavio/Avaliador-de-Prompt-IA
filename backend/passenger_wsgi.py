#!/usr/bin/env python3
"""
Passenger WSGI entry point for Hostinger deployment.
This file enables your FastAPI application to run on Hostinger's Python hosting.
"""
import sys
import os

# Add the backend directory to Python path
BACKEND_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BACKEND_DIR)

# Configure environment variables
os.environ["ENV"] = "production"

# Load variables from .env.production file
from dotenv import load_dotenv
dotenv_path = os.path.join(BACKEND_DIR, '.env.production')
load_dotenv(dotenv_path)

# Import the FastAPI application
from main import app

# Configure for WSGI with Passenger
from fastapi.middleware.wsgi import WSGIMiddleware

# Create a WSGI application from the FastAPI app
application = WSGIMiddleware(app)
