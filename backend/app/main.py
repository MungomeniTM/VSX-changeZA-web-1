# backend/app/main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routes import auth
from app.core.config import Base, engine, API_PREFIX

# Create all DB tables
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="VSXchangeZA API 🚀",
    description="Backend API for VSXchangeZA — Universal Authentication",
    version="2.0.0"
)

# Allow frontend origins
origins = [
    "http://127.0.0.1:5500",
    "http://localhost:5500"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routes
app.include_router(auth.router, prefix=API_PREFIX)

@app.get("/")
def root():
    return {"message": "VSXchangeZA API is running smoothly 🚀"}