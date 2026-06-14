import logging
import hmac
import hashlib
from typing import Optional

try:
    import razorpay
    RAZORPAY_AVAILABLE = True
except Exception:
    razorpay = None
    RAZORPAY_AVAILABLE = False

from app.core.config import get_settings
from app.core.database import get_db
from app.repositories import appointment_repo

logger = logging.getLogger(__name__)


def get_razorpay_client():
    settings = get_settings()
    if not RAZORPAY_AVAILABLE:
        raise RuntimeError("razorpay package not installed")
    return razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))


def create_payment_order(appointment_id: str, amount: float, description: str = "Clinic Appointment") -> dict:
    """Create a Razorpay order for payment"""
    settings = get_settings()

    if not settings.RAZORPAY_KEY_ID or not settings.RAZORPAY_KEY_SECRET:
        return {
            "success": False,
            "message": "Razorpay not configured"
        }

    if not RAZORPAY_AVAILABLE:
        logger.warning("Razorpay package not available")
        return {"success": False, "message": "Razorpay package not installed"}

    try:
        client = get_razorpay_client()

        # Create order
        order = client.order.create(data={
            "amount": int(amount * 100),  # Amount in paise
            "currency": "INR",
            "receipt": appointment_id,
            "description": description
        })

        db = get_db()

        # Store payment record
        db.table("payments").insert({
            "appointment_id": appointment_id,
            "razorpay_order_id": order["id"],
            "amount": amount,
            "status": "created"
        }).execute()

        logger.info(f"Order created: {order['id']} for appointment {appointment_id}")

        return {
            "success": True,
            "order_id": order["id"],
            "amount": amount,
            "currency": "INR",
            "key_id": settings.RAZORPAY_KEY_ID
        }
    except Exception as e:
        logger.error(f"Failed to create order: {e}")
        return {
            "success": False,
            "message": str(e)
        }


def verify_payment_signature(order_id: str, payment_id: str, signature: str) -> bool:
    """Verify Razorpay payment signature"""
    settings = get_settings()

    if not RAZORPAY_AVAILABLE:
        logger.warning("Razorpay package not available for signature verification")
        return False

    try:
        client = get_razorpay_client()
        client.utility.verify_payment_signature({
            'razorpay_order_id': order_id,
            'razorpay_payment_id': payment_id,
            'razorpay_signature': signature
        })
        logger.info(f"Payment signature verified: {payment_id}")
        return True
    except razorpay.errors.SignatureVerificationError:
        logger.error(f"Signature verification failed for payment {payment_id}")
        return False
    except Exception as e:
        logger.error(f"Signature verification error: {e}")
        return False


def confirm_payment(order_id: str, payment_id: str, signature: str) -> dict:
    """Confirm payment and update appointment"""
    # Verify signature first
    if not verify_payment_signature(order_id, payment_id, signature):
        return {
            "success": False,
            "message": "Payment verification failed"
        }

    db = get_db()

    try:
        # Get payment record
        payment_response = (
            db.table("payments")
            .select("*")
            .eq("razorpay_order_id", order_id)
            .single()
            .execute()
        )

        if not getattr(payment_response, 'data', None):
            return {
                "success": False,
                "message": "Payment record not found"
            }

        payment = payment_response.data
        appointment_id = payment["appointment_id"]

        # Check if already processed
        if payment.get("status") == "captured":
            return {
                "success": True,
                "message": "Payment already processed",
                "appointment_id": appointment_id
            }

        # Update payment status
        db.table("payments").update({
            "status": "captured",
            "razorpay_payment_id": payment_id
        }).eq("id", payment["id"]).execute()

        # Update appointment - confirm and mark as paid
        appointment_repo.update_appointment_status(appointment_id, "confirmed")
        appointment_repo.update_appointment_payment_status(appointment_id, "paid")

        logger.info(f"Payment confirmed for appointment {appointment_id}")

        return {
            "success": True,
            "message": "Payment confirmed successfully",
            "appointment_id": appointment_id
        }
    except Exception as e:
        logger.error(f"Failed to confirm payment: {e}")
        return {
            "success": False,
            "message": str(e)
        }


def get_payment_status(appointment_id: str) -> dict:
    """Get payment status for appointment"""
    db = get_db()

    response = (
        db.table("payments")
        .select("*")
        .eq("appointment_id", appointment_id)
        .single()
        .execute()
    )

    if not getattr(response, 'data', None):
        return {
            "status": "not_found",
            "message": "No payment record found"
        }

    payment = response.data
    return {
        "appointment_id": appointment_id,
        "order_id": payment.get("razorpay_order_id"),
        "payment_id": payment.get("razorpay_payment_id"),
        "amount": payment.get("amount"),
        "status": payment.get("status")
    }


def refund_payment(appointment_id: str, amount: float = None) -> dict:
    """Refund a payment"""
    settings = get_settings()

    if not settings.RAZORPAY_KEY_ID or not settings.RAZORPAY_KEY_SECRET:
        return {
            "success": False,
            "message": "Razorpay not configured"
        }

    if not RAZORPAY_AVAILABLE:
        logger.warning("Razorpay package not available for refund")
        return {"success": False, "message": "Razorpay package not installed"}

    db = get_db()

    try:
        # Get payment
        payment_response = (
            db.table("payments")
            .select("*")
            .eq("appointment_id", appointment_id)
            .single()
            .execute()
        )

        if not getattr(payment_response, 'data', None):
            return {
                "success": False,
                "message": "Payment not found"
            }

        payment = payment_response.data

        if not payment.get("razorpay_payment_id"):
            return {
                "success": False,
                "message": "No payment ID found for refund"
            }

        # Create refund
        client = get_razorpay_client()
        refund = client.payment.refund(payment["razorpay_payment_id"], {
            "amount": int((amount or payment["amount"]) * 100)
        })

        # Update payment status
        db.table("payments").update({
            "status": "refunded"
        }).eq("id", payment["id"]).execute()

        logger.info(f"Refund created for payment {payment['razorpay_payment_id']}")

        return {
            "success": True,
            "message": "Refund processed successfully",
            "refund_id": refund.get("id")
        }
    except Exception as e:
        logger.error(f"Failed to refund payment: {e}")
        return {
            "success": False,
            "message": str(e)
        }
import razorpay
from app.core.config import get_settings
from app.core.database import get_db
from app.repositories import appointment_repo
import logging
import hmac
import hashlib

logger = logging.getLogger(__name__)


def get_razorpay_client():
    settings = get_settings()
    return razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))


def create_payment_order(appointment_id: str, amount: float, description: str = "Clinic Appointment") -> dict:
    """Create a Razorpay order for payment"""
    settings = get_settings()
    
    if not settings.RAZORPAY_KEY_ID or not settings.RAZORPAY_KEY_SECRET:
        return {
            "success": False,
            "message": "Razorpay not configured"
        }
    
    try:
        client = get_razorpay_client()
        
        # Create order
        order = client.order.create(data={
            "amount": int(amount * 100),  # Amount in paise
            "currency": "INR",
            "receipt": appointment_id,
            "description": description
        })
        
        db = get_db()
        
        # Store payment record
        payment = db.table("payments").insert({
            "appointment_id": appointment_id,
            "razorpay_order_id": order["id"],
            "amount": amount,
            "status": "created"
        }).execute()
        
        logger.info(f"Order created: {order['id']} for appointment {appointment_id}")
        
        return {
            "success": True,
            "order_id": order["id"],
            "amount": amount,
            "currency": "INR",
            "key_id": settings.RAZORPAY_KEY_ID
        }
    except Exception as e:
        logger.error(f"Failed to create order: {e}")
        return {
            "success": False,
            "message": str(e)
        }


def verify_payment_signature(order_id: str, payment_id: str, signature: str) -> bool:
    """Verify Razorpay payment signature"""
    settings = get_settings()
    
    try:
        client = get_razorpay_client()
        client.utility.verify_payment_signature({
            'razorpay_order_id': order_id,
            'razorpay_payment_id': payment_id,
            'razorpay_signature': signature
        })
        logger.info(f"Payment signature verified: {payment_id}")
        return True
    except razorpay.errors.SignatureVerificationError:
        logger.error(f"Signature verification failed for payment {payment_id}")
        return False
    except Exception as e:
        logger.error(f"Signature verification error: {e}")
        return False


def confirm_payment(order_id: str, payment_id: str, signature: str) -> dict:
    """Confirm payment and update appointment"""
    # Verify signature first
    if not verify_payment_signature(order_id, payment_id, signature):
        return {
            "success": False,
            "message": "Payment verification failed"
        }
    
    db = get_db()
    
    try:
        # Get payment record
        payment_response = (
            db.table("payments")
            .select("*")
            .eq("razorpay_order_id", order_id)
            .single()
            .execute()
        )
        
        if not payment_response.data:
            return {
                "success": False,
                "message": "Payment record not found"
            }
        
        payment = payment_response.data
        appointment_id = payment["appointment_id"]
        
        # Check if already processed
        if payment["status"] == "captured":
            return {
                "success": True,
                "message": "Payment already processed",
                "appointment_id": appointment_id
            }
        
        # Update payment status
        db.table("payments").update({
            "status": "captured",
            "razorpay_payment_id": payment_id
        }).eq("id", payment["id"]).execute()
        
        # Update appointment - confirm and mark as paid
        appointment_repo.update_appointment_status(appointment_id, "confirmed")
        appointment_repo.update_appointment_payment_status(appointment_id, "paid")
        
        logger.info(f"Payment confirmed for appointment {appointment_id}")
        
        return {
            "success": True,
            "message": "Payment confirmed successfully",
            "appointment_id": appointment_id
        }
    except Exception as e:
        logger.error(f"Failed to confirm payment: {e}")
        return {
            "success": False,
            "message": str(e)
        }


def get_payment_status(appointment_id: str) -> dict:
    """Get payment status for appointment"""
    db = get_db()
    
    response = (
        db.table("payments")
        .select("*")
        .eq("appointment_id", appointment_id)
        .single()
        .execute()
    )
    
    if not response.data:
        return {
            "status": "not_found",
            "message": "No payment record found"
        }
    
    payment = response.data
    return {
        "appointment_id": appointment_id,
        "order_id": payment.get("razorpay_order_id"),
        "payment_id": payment.get("razorpay_payment_id"),
        "amount": payment.get("amount"),
        "status": payment.get("status")
    }


def refund_payment(appointment_id: str, amount: float = None) -> dict:
    """Refund a payment"""
    settings = get_settings()
    
    if not settings.RAZORPAY_KEY_ID or not settings.RAZORPAY_KEY_SECRET:
        return {
            "success": False,
            "message": "Razorpay not configured"
        }
    
    db = get_db()
    
    try:
        # Get payment
        payment_response = (
            db.table("payments")
            .select("*")
            .eq("appointment_id", appointment_id)
            .single()
            .execute()
        )
        
        if not payment_response.data:
            return {
                "success": False,
                "message": "Payment not found"
            }
        
        payment = payment_response.data
        
        if not payment.get("razorpay_payment_id"):
            return {
                "success": False,
                "message": "No payment ID found for refund"
            }
        
        # Create refund
        client = get_razorpay_client()
        refund = client.payment.refund(payment["razorpay_payment_id"], {
            "amount": int((amount or payment["amount"]) * 100)
        })
        
        # Update payment status
        db.table("payments").update({
            "status": "refunded"
        }).eq("id", payment["id"]).execute()
        
        logger.info(f"Refund created for payment {payment['razorpay_payment_id']}")
        
        return {
            "success": True,
            "message": "Refund processed successfully",
            "refund_id": refund.get("id")
        }
    except Exception as e:
        logger.error(f"Failed to refund payment: {e}")
        return {
            "success": False,
            "message": str(e)
        }