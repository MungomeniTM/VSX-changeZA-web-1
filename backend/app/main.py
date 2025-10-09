from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routes import auth
from app.core.config import Base, engine

# ---------------------------
# Initialize database tables
# ---------------------------
print("🔧 Initializing database schema...")
Base.metadata.create_all(bind=engine)
print("✅ Database ready.")

# ---------------------------
# FastAPI App Config
# ---------------------------
app = FastAPI(
    title="VSXchangeZA API 🚀",
    description="Backend API for VSXchangeZA — Secure authentication and user services",
    version="2.0.0"
)

# ---------------------------
# CORS Setup (Extended for Frontend + Production)
# ---------------------------
origins = [
    "http://127.0.0.1:5500",      # Localhost via VS Code Live Server
    "http://localhost:5500",
    "http://localhost:3000",      # for React/NextJS dev
    "http://127.0.0.1:3000",
    "http://localhost",           # general localhost catch
    "https://vsxchangeza.net",    # your future production domain
    "https://www.vsxchangeza.net"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],  # allow GET, POST, PUT, DELETE, etc.
    allow_headers=["*"],
)

# ---------------------------
# Include your routes (Auth, Posts, etc.)
# ---------------------------
app.include_router(auth.router, prefix="/auth", tags=["Authentication"])

# ---------------------------
# Root Endpoint
# ---------------------------
@app.get("/")
def root():
    return {
        "message": "VSXchangeZA API is running smoothly 🚀",
        "status": "active",
        "routes": ["/auth/register", "/auth/login"]
    }

# ---------------------------
# Health Check Endpoint
# ---------------------------
@app.get("/health")
def health_check():
    return {"status": "ok", "uptime": "stable"}