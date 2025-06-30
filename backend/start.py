#!/usr/bin/env python3
"""
Production startup script for SnapCircle backend on Render.
Handles database migrations and starts the FastAPI server.
"""

import os
import sys
import subprocess
from pathlib import Path

def run_migrations():
    """Run database migrations if needed."""
    print("🔄 Running database migrations...")
    try:
        # Check if alembic is configured
        if Path("alembic.ini").exists():
            result = subprocess.run(
                ["alembic", "upgrade", "head"],
                capture_output=True,
                text=True
            )
            if result.returncode == 0:
                print("✅ Database migrations completed successfully")
            else:
                print(f"⚠️ Migration warning: {result.stderr}")
        else:
            print("⚠️ No alembic.ini found, skipping migrations")
    except Exception as e:
        print(f"⚠️ Migration error (continuing anyway): {e}")

def create_tables():
    """Create tables if they don't exist."""
    print("🔄 Ensuring database tables exist...")
    try:
        from database.connection import engine, Base
        Base.metadata.create_all(bind=engine)
        print("✅ Database tables verified")
    except Exception as e:
        print(f"❌ Database table creation failed: {e}")
        sys.exit(1)

def start_server():
    """Start the FastAPI server."""
    print("🚀 Starting SnapCircle backend server...")
    port = os.getenv("PORT", "8000")

    # Use uvicorn directly for production - optimized for Render free tier
    os.execvp("uvicorn", [
        "uvicorn",
        "main:app",
        "--host", "0.0.0.0",
        "--port", port,
        "--workers", "1",  # Single worker for free tier (512MB RAM limit)
        "--timeout-keep-alive", "65",  # Handle Render's load balancer
        "--access-log"  # Enable access logs for debugging
    ])

if __name__ == "__main__":
    print("🎯 SnapCircle Backend - Production Startup")
    print("=" * 50)
    
    # Run migrations and create tables
    run_migrations()
    create_tables()
    
    # Start the server
    start_server()
