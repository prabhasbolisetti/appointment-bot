from fastapi import FastAPI
from contextlib import asynccontextmanager
from app.core.config import get_settings
from app.core.database import get_db


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    settings = get_settings()
    db = get_db()
    print(f"🚀 App starting in {settings.APP_ENV} mode")
    print(f"✅ Supabase connected: {settings.SUPABASE_URL}")
    yield
    # Shutdown
    print("🛑 App shutting down")


app = FastAPI(
    title="Appointment Booking Bot",
    description="WhatsApp-based clinic appointment booking system",
    version="0.1.0",
    lifespan=lifespan
)


@app.get("/health")
def health_check():
    return {
        "status": "ok",
        "app": "appointment-bot",
        "env": get_settings().APP_ENV
    }

