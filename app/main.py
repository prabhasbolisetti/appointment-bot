from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import logging

from app.core.config import get_settings
from app.core.database import get_db

from app.api import (
    bookings,
    whatsapp,
    admin_auth,
    clinic,
    appointments,
    patients,
    slots,
)


def configure_logging():
    settings = get_settings()

    level = (
        logging.DEBUG
        if settings.APP_ENV == "development"
        else logging.INFO
    )

    logging.basicConfig(
        level=level,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )


@asynccontextmanager
async def lifespan(app: FastAPI):
    configure_logging()

    settings = get_settings()
    get_db()

    logger = logging.getLogger("appointment")

    logger.info(f"🚀 App starting in {settings.APP_ENV} mode")
    logger.info(f"✅ Supabase connected: {settings.SUPABASE_URL}")

    yield

    logger.info("🛑 App shutting down")


app = FastAPI(
    title="Appointment Booking Bot",
    description="WhatsApp-based clinic appointment booking system",
    version="0.1.0",
    lifespan=lifespan,
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://localhost:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routers
app.include_router(bookings.router)
app.include_router(whatsapp.router)
app.include_router(admin_auth.router)
app.include_router(clinic.router)
app.include_router(appointments.router)
app.include_router(patients.router)
app.include_router(slots.router)


@app.get("/")
def root():
    return {
        "message": "Appointment Booking Bot API",
        "docs": "/docs",
    }


@app.get("/health")
def health_check():
    return {
        "status": "ok",
        "app": "appointment-bot",
        "env": get_settings().APP_ENV,
    }