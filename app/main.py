from fastapi import FastAPI
from contextlib import asynccontextmanager
from app.core.config import get_settings
from app.core.database import get_db
from app.api import bookings, whatsapp
import logging


# Configure basic logging for the application. This ensures our module loggers
# (appointment.whatsapp) and other libraries emit to stdout when running.
def _configure_logging():
    settings = get_settings()
    level = logging.DEBUG if settings.APP_ENV == "development" else logging.INFO
    logging.basicConfig(
        level=level,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )


@asynccontextmanager
async def lifespan(app: FastAPI):
    _configure_logging()
    settings = get_settings()
    db = get_db()
    logging.getLogger("appointment.whatsapp").info(f"🚀 App starting in {settings.APP_ENV} mode")
    logging.getLogger("appointment.whatsapp").info(f"✅ Supabase connected: {settings.SUPABASE_URL}")
    yield
    logging.getLogger("appointment.whatsapp").info("🛑 App shutting down")


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