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


def get_slot(slot_id: str) -> dict:
    db = get_db()
    response = (
        db.table("slots")
        .select("*")
        .eq("id", slot_id)
        .single()
        .execute()
    )
    return response.data if response.data else None


def get_slots_by_clinic(clinic_id: str, slot_date: str = None, status: str = None) -> list:
    db = get_db()
    query = (
        db.table("slots")
        .select("*")
        .eq("clinic_id", clinic_id)
        .order("slot_date")
        .order("start_time")
    )
    
    if slot_date:
        query = query.eq("slot_date", slot_date)
    if status:
        query = query.eq("status", status)
    
    response = query.execute()
    return response.data


def bulk_create_slots(
    clinic_id: str,
    start_date,
    end_date,
    open_time,
    close_time,
    slot_duration_minutes: int
) -> int:
    db = get_db()
    from datetime import timedelta
    
    slots_to_insert = []
    current_date = start_date
    
    while current_date <= end_date:
        # Skip Sundays (weekday 6 = Sunday)
        if current_date.weekday() != 6:
            current_time = open_time
            while current_time < close_time:
                slots_to_insert.append({
                    "clinic_id": clinic_id,
                    "slot_date": current_date.isoformat(),
                    "start_time": current_time.isoformat(),
                    "status": "available"
                })
                # Add slot_duration_minutes to current_time
                from datetime import datetime, timedelta
                dt = datetime.combine(current_date, current_time)
                dt += timedelta(minutes=slot_duration_minutes)
                current_time = dt.time()
        
        current_date += timedelta(days=1)
    
    if not slots_to_insert:
        return 0

    if not slots_to_insert:
        return 0

    # To avoid duplicate-key errors, fetch existing slots in the date range
    # and filter them out before inserting.
    start_iso = start_date.isoformat()
    end_iso = end_date.isoformat()

    existing_resp = (
        db.table("slots")
        .select("slot_date,start_time")
        .eq("clinic_id", clinic_id)
        .gte("slot_date", start_iso)
        .lte("slot_date", end_iso)
        .execute()
    )

    existing = set()
    if existing_resp and existing_resp.data:
        for r in existing_resp.data:
            existing.add((str(r.get("slot_date")), str(r.get("start_time"))))

    to_insert_filtered = []
    for s in slots_to_insert:
        key = (s["slot_date"], s["start_time"])
        if key not in existing:
            to_insert_filtered.append(s)

    if not to_insert_filtered:
        return 0

    response = db.table("slots").insert(to_insert_filtered).execute()
    return len(response.data) if response.data else 0


def delete_slot(slot_id: str) -> bool:
    db = get_db()
    response = (
        db.table("slots")
        .delete()
        .eq("id", slot_id)
        .execute()
    )
    return len(response.data) > 0