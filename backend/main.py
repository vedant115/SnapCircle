from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

app = FastAPI(
    title="SnapCircle API",
    description="Event Photo Sharing Application API",
    version="1.0.0"
)

# CORS middleware - Production ready
frontend_url = os.getenv("FRONTEND_URL", "http://localhost:3000")
allowed_origins = [
    "http://localhost:3000",  # Local development
    "http://localhost:5173",  # Vite dev server
    frontend_url,  # Production frontend
]

# Remove any None or empty values
allowed_origins = [origin for origin in allowed_origins if origin]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

# Static files for uploads
upload_dir = os.getenv("UPLOAD_DIR", "../uploads")
if not os.path.exists(upload_dir):
    os.makedirs(upload_dir)

app.mount("/uploads", StaticFiles(directory=upload_dir), name="uploads")

@app.get("/")
async def root():
    return {"message": "SnapCircle API is running!"}

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

# Import and include routers
from routers import auth, events, photos
app.include_router(auth.router, prefix="/api/auth", tags=["authentication"])
app.include_router(events.router, prefix="/api/events", tags=["events"])
app.include_router(photos.router, prefix="/api/photos", tags=["photos"])

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
