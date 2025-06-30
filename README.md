# SnapCircle - Event Photo Sharing App

A comprehensive web application for sharing and managing photos at events. Users can create events, invite guests via QR codes or links, upload photos, and manage their event galleries with role-based access control.

## 🚀 Quick Start

1. **Clone the repository**

   ```bash
   git clone <repository-url>
   cd SnapCircleV1
   ```

2. **Set up the backend**

   ```bash
   cd backend
   python -m venv venv
   source venv/bin/activate  # Windows: venv\Scripts\activate
   pip install -r requirements.txt
   cp .env.example .env  # Configure your database and settings
   uvicorn main:app --reload
   ```

3. **Set up the frontend**

   ```bash
   cd frontend
   npm install
   npm run dev
   ```
