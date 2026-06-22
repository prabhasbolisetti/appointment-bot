import asyncio
import logging
from datetime import datetime, timedelta, timezone

from apscheduler.schedulers.background import BackgroundScheduler

from app.core.config import get_settings
from app.core.database import get_db
from app.repositories import appointment_repo
from app.services import email_service, whatsapp_service

logger = logging.getLogger(__name__)

scheduler = BackgroundScheduler()


def release_expired_holds_job() -> int:
    db = get_db()
    now = datetime.now(timezone.utc).isoformat()

    expired = (
        db.table("slots")
        .select("id")
        .eq("clinic_id", get_settings().CLINIC_ID)
        .eq("status", "held")
        .lt("held_until", now)
        .execute()
    )
    slots = expired.data or []
    slot_ids = [slot["id"] for slot in slots]
    if not slot_ids:
        return 0

    db.table("appointments").update({
        "status": "cancelled",
    }).in_("slot_id", slot_ids).eq("status", "pending").execute()

    db.table("slots").update({
        "status": "available",
        "held_by": None,
        "held_until": None,
    }).in_("id", slot_ids).execute()

    logger.info("Released %s expired held slots", len(slot_ids))
    return len(slot_ids)


def send_reminders_job() -> int:
    settings = get_settings()
    appointments = appointment_repo.get_confirmed_appointments_needing_reminder(settings.CLINIC_ID)
    now = datetime.now()
    reminder_until = now + timedelta(hours=1, minutes=5)
    sent_count = 0

    for appointment in appointments:
        slot = appointment.get("slots") or {}
        slot_date = slot.get("slot_date")
        start_time = str(slot.get("start_time") or "")[:8]
        if not slot_date or not start_time:
            continue

        try:
            appointment_at = datetime.fromisoformat(f"{slot_date}T{start_time}")
        except ValueError:
            logger.warning("Could not parse appointment time for %s", appointment.get("id"))
            continue

        if not now <= appointment_at <= reminder_until:
            continue

        email_service.send_appointment_reminder_email(appointment)
        _send_whatsapp_reminder(appointment)
        appointment_repo.mark_reminder_sent(appointment["id"])
        sent_count += 1

    if sent_count:
        logger.info("Sent %s appointment reminders", sent_count)
    return sent_count


def _send_whatsapp_reminder(appointment: dict) -> None:
    patient = appointment.get("patients") or {}
    slot = appointment.get("slots") or {}
    phone = patient.get("whatsapp_number")
    if not phone:
        return

    message = (
        "Appointment reminder.\n"
        f"Date: {slot.get('slot_date')}\n"
        f"Time: {str(slot.get('start_time', ''))[:5]}"
    )
    try:
        asyncio.run(whatsapp_service.send_text(phone, message))
    except Exception as exc:
        logger.warning("Failed to send WhatsApp reminder: %s", exc)


def start_background_jobs() -> BackgroundScheduler:
    if scheduler.running:
        return scheduler

    scheduler.add_job(
        release_expired_holds_job,
        "interval",
        seconds=60,
        id="release_expired_holds",
        replace_existing=True,
        max_instances=1,
    )
    scheduler.add_job(
        send_reminders_job,
        "interval",
        minutes=5,
        id="send_one_hour_reminders",
        replace_existing=True,
        max_instances=1,
    )
    scheduler.start()
    logger.info("Background jobs started")
    return scheduler


def stop_background_jobs() -> None:
    if scheduler.running:
        scheduler.shutdown(wait=False)
        logger.info("Background jobs stopped")
