#!/usr/bin/env python3
"""
Production startup script for SnapCircle backend on Render.
Handles database migrations and starts the FastAPI server.
"""

import os, sys, subprocess
from pathlib import Path

def run_migrations():
    print("🔄 Running database migrations...")
    try:
        # Make alembic commands more visible in logs
        print("=" * 50)
        print("RUNNING ALEMBIC MIGRATIONS")
        print("=" * 50)
        
        # Run migrations with verbose output
        result = subprocess.run(
            ["alembic", "upgrade", "head", "--verbose"],
            capture_output=True,
            text=True,
            check=True
        )
        
        # Print migration output for debugging
        print(f"STDOUT: {result.stdout}")
        if result.stderr:
            print(f"STDERR: {result.stderr}")
            
        print("✅ Database migrations completed")
    except subprocess.CalledProcessError as e:
        print(f"❌ Database migration failed: {e}")
        print(f"STDOUT: {e.stdout}")
        print(f"STDERR: {e.stderr}")
        
        # Fall back to create_tables if migrations fail
        print("⚠️ Falling back to direct table creation...")
        create_tables()

def create_tables():
    print("🔄 Ensuring database tables exist...")
    try:
        # Import all models to ensure they're registered with Base
        from models.user import User
        from models.event import Event
        from models.photo import Photo
        from models.photo_face import PhotoFace
        # Import any other models here
        
        # Create all tables
        from database.connection import engine, Base
        Base.metadata.create_all(bind=engine)
        print("✅ Database tables created successfully")
    except Exception as e:
        print(f"❌ Database table creation failed: {e}")
        sys.exit(1)

def start_server():
    print("🚀 Starting SnapCircle backend server...")
    port = os.getenv("PORT", "8000")
    os.execvp("uvicorn", [
        "uvicorn", "main:app",
        "--host", "0.0.0.0",
        "--port", port,
        "--workers", "1",
        "--timeout-keep-alive", "65",
        "--access-log"
    ])

if __name__ == "__main__":
    print("🎯 SnapCircle Backend - Production Startup")
    print("=" * 50)
    run_migrations()
    create_tables()
    start_server()


