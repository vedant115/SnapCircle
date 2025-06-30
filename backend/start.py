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
        alembic_dir = Path(__file__).parent
        os.chdir(alembic_dir)
        ini = alembic_dir / "alembic.ini"
        if ini.exists():
            result = subprocess.run(
                ["alembic", "-c", str(ini), "upgrade", "head"],
                env={**os.environ},
                capture_output=True, text=True
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
    print("🔄 Ensuring database tables exist...")
    try:
        # your connection module must read DATABASE_URL from os.environ
        from database.connection import engine, Base
        Base.metadata.create_all(bind=engine)
        print("✅ Database tables verified")
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
