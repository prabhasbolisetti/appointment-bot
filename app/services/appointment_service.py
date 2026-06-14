from app.core.database import get_db
from app.repositories import appointment_repo, slot_repo
from datetime import datetime, timezone


def get_appointments_by_clinic(clinic_id: str, status: str = None):
    return appointment_repo.get_appointments_with_details(clinic_id, status)


def get_appointment(appointment_id: str):
    return appointment_repo.get_appointment_with_details(appointment_id)


def cancel_appointment(appointment_id: str) -> dict:
    """Cancel appointment and release slot"""
    appointment = appointment_repo.get_appointment_with_details(appointment_id)
    if not appointment:
        return {"success": False, "message": "Appointment not found"}
    
    # Update appointment status
    appointment_repo.update_appointment_status(appointment_id, "cancelled")
    
    # Release the slot
    slot_repo.release_slot(appointment["slot_id"])
    
    return {
        "success": True,
        "message": "Appointment cancelled and slot released"
    }


def complete_appointment(appointment_id: str) -> dict:
    """Mark appointment as completed"""
    appointment = appointment_repo.get_appointment_with_details(appointment_id)
    if not appointment:
        return {"success": False, "message": "Appointment not found"}
    
    appointment_repo.update_appointment_status(appointment_id, "completed")
    
    return {
        "success": True,
        "message": "Appointment marked as completed"
    }


def request_refund(appointment_id: str) -> dict:
    """Request refund for appointment (requires Razorpay integration)"""
    appointment = appointment_repo.get_appointment_with_details(appointment_id)
    if not appointment:
        return {"success": False, "message": "Appointment not found"}
    
    if appointment["payment_status"] != "paid":
        return {"success": False, "message": "Only paid appointments can be refunded"}
    
    # Get payment details
    payment = appointment_repo.get_appointment_payment(appointment_id)
    if not payment:
        return {"success": False, "message": "Payment record not found"}
    
    # TODO: Call Razorpay refund API in Phase 5.7
    # For now, just mark as refunded
    appointment_repo.update_appointment_payment_status(appointment_id, "refunded")
    appointment_repo.update_appointment_status(appointment_id, "cancelled")
    
    return {
        "success": True,
        "message": "Refund processed",
        "razorpay_order_id": payment.get("razorpay_order_id")
    }


def get_appointment_stats(clinic_id: str) -> dict:
    """Get appointment statistics for clinic"""
    db = get_db()
    
    # Total appointments
    total = db.table("appointments").select("id").eq("clinic_id", clinic_id).execute()
    total_count = len(total.data) if total.data else 0
    
    # Confirmed
    confirmed = db.table("appointments").select("id").eq("clinic_id", clinic_id).eq("status", "confirmed").execute()
    confirmed_count = len(confirmed.data) if confirmed.data else 0
    
    # Completed
    completed = db.table("appointments").select("id").eq("clinic_id", clinic_id).eq("status", "completed").execute()
    completed_count = len(completed.data) if completed.data else 0
    
    # Cancelled
    cancelled = db.table("appointments").select("id").eq("clinic_id", clinic_id).eq("status", "cancelled").execute()
    cancelled_count = len(cancelled.data) if cancelled.data else 0
    
    # Paid
    paid = db.table("appointments").select("id").eq("clinic_id", clinic_id).eq("payment_status", "paid").execute()
    paid_count = len(paid.data) if paid.data else 0
    
    return {
        "total": total_count,
        "confirmed": confirmed_count,
        "completed": completed_count,
        "cancelled": cancelled_count,
        "paid": paid_count,
        "completion_rate": round((completed_count / total_count * 100) if total_count > 0 else 0, 2)
    }