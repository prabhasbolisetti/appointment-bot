from app.core.database import get_db
from datetime import datetime, timezone, timedelta
from uuid import UUID
from typing import Optional


def get_available_slots(clinic_id: str, slot_date: str) -> list:
    db = get_db()
    response = (
        db.table("slots")
        .select("id, clinic_id, slot_date, start_time, status")
        .eq("clinic_id", clinic_id)
        .eq("slot_date", slot_date)
        .eq("status", "available")
        .order("start_time")
        .execute()
    )
    return response.data


def atomic_hold_slot(slot_id: str, patient_id: str) -> bool:
    """
    Atomic update — only succeeds if status is still 'available'.
    If two users try simultaneously, only one UPDATE wins.
    The other gets 0 rows updated → returns False.
    """
    db = get_db()
    held_until = datetime.now(timezone.utc) + timedelta(minutes=5)

    response = (
        db.table("slots")
        .update({
            "status": "held",
            "held_by": patient_id,
            "held_until": held_until.isoformat()
        })
        .eq("id", slot_id)
        .eq("status", "available")  # ← this is the race condition guard
        .execute()
    )
    return len(response.data) > 0


def confirm_slot(slot_id: str) -> bool:
    db = get_db()
    response = (
        db.table("slots")
        .update({"status": "booked", "held_by": None, "held_until": None})
        .eq("id", slot_id)
        .execute()
    )
    return len(response.data) > 0


def release_slot(slot_id: str) -> bool:
    db = get_db()
    response = (
        db.table("slots")
        .update({"status": "available", "held_by": None, "held_until": None})
        .eq("id", slot_id)
        .execute()
    )
    return len(response.data) > 0


def release_expired_holds() -> int:
    """
    Called by background worker every 60 seconds.
    Returns count of slots released.
    """
    db = get_db()
    now = datetime.now(timezone.utc).isoformat()
    response = (
        db.table("slots")
        .update({"status": "available", "held_by": None, "held_until": None})
        .eq("status", "held")
        .lt("held_until", now)
        .execute()
    )
    return len(response.data)