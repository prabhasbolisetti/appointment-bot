import asyncio
import hashlib
import hmac
import json
import logging
from datetime import datetime, timezone
from typing import Optional

try:
    import razorpay
    RAZORPAY_AVAILABLE = True
except Exception:
    razorpay = None
    RAZORPAY_AVAILABLE = False

from app.core.config import get_settings
from app.core.database import get_db
from app.repositories import appointment_repo, patient_repo, slot_repo
from app.services import email_service, whatsapp_service

logger = logging.getLogger(__name__)


def get_razorpay_client():
    settings = get_settings()
    if not RAZORPAY_AVAILABLE:
        raise RuntimeError("razorpay package not installed")
    return razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))


def _amount_for_appointment(appointment: dict) -> float:
    clinic = appointment.get("clinics") or {}
    amount = clinic.get("consultation_fee") or 300
    return float(amount)


def _latest_payment_for_appointment(appointment_id: str) -> Optional[dict]:
    db = get_db()
    response = (
        db.table("payments")
        .select("*")
        .eq("appointment_id", appointment_id)
        .order("created_at", desc=True)
        .execute()
    )
    if not getattr(response, "data", None):
        return None
    return response.data[0] if isinstance(response.data, list) else response.data


def _payment_by_order_id(order_id: str) -> Optional[dict]:
    db = get_db()
    response = (
        db.table("payments")
        .select("*")
        .eq("razorpay_order_id", order_id)
        .execute()
    )
    if not getattr(response, "data", None):
        return None
    return response.data[0]


def _checkout_summary(appointment: dict, payment: dict = None) -> dict:
    amount = _amount_for_appointment(appointment)
    return {
        "appointment_id": appointment["id"],
        "status": appointment["status"],
        "payment_status": appointment["payment_status"],
        "amount": amount,
        "currency": "INR",
        "key_id": get_settings().RAZORPAY_KEY_ID,
        "order_id": payment.get("razorpay_order_id") if payment else None,
        "patient": appointment.get("patients") or {},
        "slot": appointment.get("slots") or {},
        "clinic": appointment.get("clinics") or {},
        "complaint_notes": appointment.get("complaint_notes"),
    }


def get_checkout_details(appointment_id: str) -> dict:
    appointment = appointment_repo.get_appointment_with_details(appointment_id)
    if not appointment:
        return {"success": False, "message": "Appointment not found"}

    payment = _latest_payment_for_appointment(appointment_id)
    return {"success": True, **_checkout_summary(appointment, payment)}


def _slot_hold_expired(appointment: dict) -> bool:
    slot = appointment.get("slots") or {}
    held_until = slot.get("held_until")
    if not held_until or appointment.get("status") != "pending":
        return False

    try:
        expiry = datetime.fromisoformat(str(held_until).replace("Z", "+00:00"))
    except ValueError:
        return False

    return expiry < datetime.now(timezone.utc)


def create_payment_order(appointment_id: str, amount: float = None, description: str = "Clinic Appointment") -> dict:
    settings = get_settings()

    if not settings.RAZORPAY_KEY_ID or not settings.RAZORPAY_KEY_SECRET:
        return {"success": False, "message": "Razorpay not configured"}
    if not RAZORPAY_AVAILABLE:
        return {"success": False, "message": "Razorpay package not installed"}

    appointment = appointment_repo.get_appointment_with_details(appointment_id)
    if not appointment:
        return {"success": False, "message": "Appointment not found"}
    if appointment["clinic_id"] != settings.CLINIC_ID:
        return {"success": False, "message": "Appointment is not for this clinic"}
    if appointment["payment_status"] == "paid":
        return {"success": False, "message": "Appointment is already paid"}
    if appointment["status"] != "pending":
        return {"success": False, "message": "Only pending appointments can be paid"}
    if _slot_hold_expired(appointment):
        slot_repo.release_slot(appointment["slot_id"])
        appointment_repo.update_appointment_status(appointment_id, "cancelled")
        return {"success": False, "message": "Slot hold expired. Please book again."}

    existing_payment = _latest_payment_for_appointment(appointment_id)
    if existing_payment and existing_payment.get("status") == "created":
        return {"success": True, **_checkout_summary(appointment, existing_payment)}

    order_amount = _amount_for_appointment(appointment)

    try:
        order = get_razorpay_client().order.create(data={
            "amount": int(order_amount * 100),
            "currency": "INR",
            "receipt": appointment_id,
            "notes": {"appointment_id": appointment_id},
        })

        payment = (
            get_db().table("payments")
            .insert({
                "appointment_id": appointment_id,
                "razorpay_order_id": order["id"],
                "amount": order_amount,
                "status": "created",
            })
            .execute()
        ).data[0]

        logger.info("Razorpay order created: %s for appointment %s", order["id"], appointment_id)
        return {"success": True, **_checkout_summary(appointment, payment)}
    except Exception as exc:
        logger.error("Failed to create Razorpay order for appointment %s: %s", appointment_id, exc)
        return {"success": False, "message": "Failed to create payment order"}


def verify_payment_signature(order_id: str, payment_id: str, signature: str) -> bool:
    if not RAZORPAY_AVAILABLE:
        return False

    try:
        get_razorpay_client().utility.verify_payment_signature({
            "razorpay_order_id": order_id,
            "razorpay_payment_id": payment_id,
            "razorpay_signature": signature,
        })
        return True
    except Exception as exc:
        logger.warning("Checkout signature verification failed for %s: %s", payment_id, exc)
        return False


def confirm_payment(order_id: str, payment_id: str, signature: str) -> dict:
    if not verify_payment_signature(order_id, payment_id, signature):
        return {"success": False, "message": "Payment verification failed"}

    return _finalize_successful_payment(
        order_id=order_id,
        payment_id=payment_id,
        raw_webhook=None,
        webhook_event_id=None,
    )


def verify_webhook(raw_body: bytes, signature: str) -> bool:
    settings = get_settings()
    if not settings.RAZORPAY_WEBHOOK_SECRET:
        logger.error("RAZORPAY_WEBHOOK_SECRET is not configured")
        return False

    expected = hmac.new(
        settings.RAZORPAY_WEBHOOK_SECRET.encode("utf-8"),
        raw_body,
        hashlib.sha256,
    ).hexdigest()
    return hmac.compare_digest(expected, signature or "")


def _payment_entity(payload: dict) -> dict:
    payment = (payload.get("payload") or {}).get("payment") or {}
    return payment.get("entity") or payment


def _order_entity(payload: dict) -> dict:
    order = (payload.get("payload") or {}).get("order") or {}
    return order.get("entity") or order


def _webhook_event_id(payload: dict, payment: dict, order: dict) -> str:
    event = payload.get("event") or "unknown"
    created_at = payload.get("created_at") or ""
    payment_id = payment.get("id") or ""
    order_id = payment.get("order_id") or order.get("id") or ""
    return payload.get("id") or payload.get("event_id") or f"{event}:{order_id}:{payment_id}:{created_at}"


def _get_webhook_event(event_id: str) -> Optional[dict]:
    response = (
        get_db().table("payment_webhooks")
        .select("*")
        .eq("event_id", event_id)
        .execute()
    )
    if not getattr(response, "data", None):
        return None
    return response.data[0]


def _insert_webhook_event(event_id: str, event_type: str, payload: dict, signature: str) -> bool:
    try:
        get_db().table("payment_webhooks").insert({
            "event_id": event_id,
            "event_type": event_type,
            "signature": signature,
            "raw_payload": payload,
            "status": "received",
        }).execute()
        return True
    except Exception as exc:
        logger.info("Webhook event already recorded or failed to insert: %s", exc)
        return False


def _mark_webhook_event(event_id: str, status: str, error: str = None) -> None:
    payload = {
        "status": status,
        "processed_at": datetime.now(timezone.utc).isoformat(),
    }
    if error:
        payload["error"] = error
    get_db().table("payment_webhooks").update(payload).eq("event_id", event_id).execute()


def process_webhook(raw_body: bytes, signature: str) -> dict:
    if not verify_webhook(raw_body, signature):
        return {"success": False, "message": "Invalid webhook signature"}

    try:
        payload = json.loads(raw_body.decode("utf-8"))
    except json.JSONDecodeError:
        return {"success": False, "message": "Invalid webhook payload"}

    payment = _payment_entity(payload)
    order = _order_entity(payload)
    event_type = payload.get("event") or "unknown"
    event_id = _webhook_event_id(payload, payment, order)

    existing = _get_webhook_event(event_id)
    if existing and existing.get("status") == "processed":
        return {"success": True, "message": "Webhook already processed", "event_id": event_id}

    if not existing:
        _insert_webhook_event(event_id, event_type, payload, signature)

    try:
        if event_type in {"payment.captured", "order.paid"}:
            order_id = payment.get("order_id") or order.get("id")
            payment_id = payment.get("id")
            if not payment_id:
                _mark_webhook_event(event_id, "ignored")
                return {
                    "success": True,
                    "message": "Ignored order event without payment id; waiting for payment.captured",
                    "event_id": event_id,
                }
            result = _finalize_successful_payment(order_id, payment_id, payload, event_id)
            _mark_webhook_event(event_id, "processed" if result["success"] else "failed", result.get("message"))
            return {**result, "event_id": event_id}

        if event_type == "payment.authorized" and payment.get("captured") is True:
            result = _finalize_successful_payment(payment.get("order_id"), payment.get("id"), payload, event_id)
            _mark_webhook_event(event_id, "processed" if result["success"] else "failed", result.get("message"))
            return {**result, "event_id": event_id}

        if event_type == "payment.failed":
            result = _mark_failed_payment(payment.get("order_id"), payment.get("id"), payload, event_id)
            _mark_webhook_event(event_id, "processed" if result["success"] else "failed", result.get("message"))
            return {**result, "event_id": event_id}

        _mark_webhook_event(event_id, "ignored")
        return {"success": True, "message": f"Ignored webhook event {event_type}", "event_id": event_id}
    except Exception as exc:
        logger.exception("Webhook processing failed for event %s", event_id)
        _mark_webhook_event(event_id, "failed", str(exc))
        return {"success": False, "message": "Webhook processing failed", "event_id": event_id}


def _finalize_successful_payment(
    order_id: str,
    payment_id: str,
    raw_webhook: dict = None,
    webhook_event_id: str = None,
) -> dict:
    if not order_id or not payment_id:
        return {"success": False, "message": "Missing order or payment id"}

    payment = _payment_by_order_id(order_id)
    if not payment:
        return {"success": False, "message": "Payment record not found"}

    appointment_id = payment["appointment_id"]
    if payment.get("status") == "captured":
        return {
            "success": True,
            "message": "Payment already processed",
            "appointment_id": appointment_id,
        }

    update_payload = {
        "status": "captured",
        "razorpay_payment_id": payment_id,
        "razorpay_event_id": webhook_event_id,
    }
    if raw_webhook is not None:
        update_payload["raw_webhook"] = raw_webhook
    if webhook_event_id:
        update_payload["webhook_processed_at"] = datetime.now(timezone.utc).isoformat()

    updated = (
        get_db().table("payments")
        .update(update_payload)
        .eq("id", payment["id"])
        .eq("status", "created")
        .execute()
    )
    if not getattr(updated, "data", None):
        latest = _payment_by_order_id(order_id)
        if latest and latest.get("status") == "captured":
            return {
                "success": True,
                "message": "Payment already processed",
                "appointment_id": appointment_id,
            }
        return {"success": False, "message": "Payment is not in a payable state"}

    appointment_repo.update_appointment_status(appointment_id, "confirmed")
    appointment_repo.update_appointment_payment_status(appointment_id, "paid")

    appointment = appointment_repo.get_appointment_with_details(appointment_id)
    if appointment:
        slot_repo.confirm_slot(appointment["slot_id"])
        patient_repo.update_conversation_state(appointment["patient_id"], "IDLE", {})
        _send_confirmation_side_effects(appointment)

    logger.info("Payment confirmed for appointment %s", appointment_id)
    return {
        "success": True,
        "message": "Payment confirmed successfully",
        "appointment_id": appointment_id,
    }


def _mark_failed_payment(order_id: str, payment_id: str, raw_webhook: dict, webhook_event_id: str) -> dict:
    if not order_id:
        return {"success": False, "message": "Missing order id"}

    payment = _payment_by_order_id(order_id)
    if not payment:
        return {"success": False, "message": "Payment record not found"}

    get_db().table("payments").update({
        "status": "failed",
        "razorpay_payment_id": payment_id,
        "raw_webhook": raw_webhook,
        "razorpay_event_id": webhook_event_id,
        "webhook_processed_at": datetime.now(timezone.utc).isoformat(),
    }).eq("id", payment["id"]).execute()

    logger.warning("Payment failed for order %s", order_id)
    return {
        "success": True,
        "message": "Failed payment recorded",
        "appointment_id": payment["appointment_id"],
    }


def _send_confirmation_side_effects(appointment: dict) -> None:
    email_service.send_patient_booking_email(appointment)
    email_service.send_admin_booking_notification(appointment)

    patient = appointment.get("patients") or {}
    slot = appointment.get("slots") or {}
    phone = patient.get("whatsapp_number")
    if not phone:
        return

    message = (
        "Appointment confirmed.\n"
        f"Date: {slot.get('slot_date')}\n"
        f"Time: {str(slot.get('start_time', ''))[:5]}"
    )

    try:
        loop = asyncio.get_running_loop()
        loop.create_task(whatsapp_service.send_text(phone, message))
    except RuntimeError:
        try:
            asyncio.run(whatsapp_service.send_text(phone, message))
        except Exception as exc:
            logger.warning("Failed to send WhatsApp confirmation: %s", exc)


def get_payment_status(appointment_id: str) -> dict:
    payment = _latest_payment_for_appointment(appointment_id)
    if not payment:
        return {"status": "not_found", "message": "No payment record found"}

    return {
        "appointment_id": appointment_id,
        "order_id": payment.get("razorpay_order_id"),
        "payment_id": payment.get("razorpay_payment_id"),
        "amount": payment.get("amount"),
        "status": payment.get("status"),
    }


def refund_payment(appointment_id: str, amount: float = None) -> dict:
    settings = get_settings()
    if not settings.RAZORPAY_KEY_ID or not settings.RAZORPAY_KEY_SECRET:
        return {"success": False, "message": "Razorpay not configured"}
    if not RAZORPAY_AVAILABLE:
        return {"success": False, "message": "Razorpay package not installed"}

    payment = _latest_payment_for_appointment(appointment_id)
    if not payment or not payment.get("razorpay_payment_id"):
        return {"success": False, "message": "Payment not found"}

    try:
        refund = get_razorpay_client().payment.refund(payment["razorpay_payment_id"], {
            "amount": int(float(amount or payment["amount"]) * 100),
        })

        get_db().table("payments").update({"status": "refunded"}).eq("id", payment["id"]).execute()
        appointment_repo.update_appointment_payment_status(appointment_id, "refunded")
        return {
            "success": True,
            "message": "Refund processed successfully",
            "refund_id": refund.get("id"),
        }
    except Exception as exc:
        logger.error("Failed to refund payment for appointment %s: %s", appointment_id, exc)
        return {"success": False, "message": "Failed to refund payment"}
