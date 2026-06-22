from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
import logging

from app.core.config import get_settings
from app.core.database import get_db
from app.workers.background_jobs import start_background_jobs, stop_background_jobs

from app.api import (
    auth,
    bookings,
    whatsapp,
    clinic,
    appointments,
    patients,
    slots,
    payments,
)


def configure_logging():
    settings = get_settings()

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )
    logging.getLogger("appointment").setLevel(
        logging.DEBUG if settings.APP_ENV == "development" else logging.INFO
    )
    for logger_name in ("httpcore", "httpx", "hpack", "postgrest", "supabase"):
        logging.getLogger(logger_name).setLevel(logging.WARNING)


@asynccontextmanager
async def lifespan(app: FastAPI):
    configure_logging()

    settings = get_settings()
    settings.validate_startup()
    get_db()

    logger = logging.getLogger("appointment")

    logger.info("App starting in %s mode", settings.APP_ENV)
    logger.info("Supabase configured: %s", settings.SUPABASE_URL)
    start_background_jobs()

    yield

    stop_background_jobs()
    logger.info("App shutting down")


app = FastAPI(
    title="Appointment Booking Bot",
    description="WhatsApp-based clinic appointment booking system",
    version="0.1.0",
    lifespan=lifespan,
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=get_settings().cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routers
app.include_router(auth.router)
app.include_router(bookings.router)
app.include_router(whatsapp.router)
app.include_router(clinic.router)
app.include_router(appointments.router)
app.include_router(patients.router)
app.include_router(slots.router)
app.include_router(payments.router)


@app.middleware("http")
async def error_handling_middleware(request: Request, call_next):
    try:
        return await call_next(request)
    except Exception:
        logging.getLogger("appointment").exception(
            "Unhandled error while processing %s %s",
            request.method,
            request.url.path,
        )
        return JSONResponse(
            status_code=500,
            content={"detail": "Internal server error"},
        )


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
