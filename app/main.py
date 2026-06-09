from fastapi import FastAPI
from contextlib import asynccontextmanager
from app.core.config import get_settings
from app.core.database import get_db
from app.api import bookings, whatsapp


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = get_settings()
    db = get_db()
    print(f"🚀 App starting in {settings.APP_ENV} mode")
    print(f"✅ Supabase connected: {settings.SUPABASE_URL}")
    yield
    print("🛑 App shutting down")


app = FastAPI(
    title="Appointment Booking Bot",
    description="WhatsApp-based clinic appointment booking system",
    version="0.1.0",
    lifespan=lifespan
)

app.include_router(bookings.router)
app.include_router(whatsapp.router)


@app.get("/health")
def health_check():
    return {
        "status": "ok",
        "app": "appointment-bot",
        "env": get_settings().APP_ENV
    }