from fastapi import APIRouter, HTTPException, Depends, Header, Request
from pydantic import BaseModel
from app.core.security import verify_access_token
from app.services import payment_service
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/payments", tags=["payments"])


class CreateOrderRequest(BaseModel):
    appointment_id: str
    amount: float


class VerifyPaymentRequest(BaseModel):
    order_id: str
    payment_id: str
    signature: str


def get_current_admin(authorization: str = Header(None)):
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing or invalid token")

    token = authorization.split(" ")[1]
    payload = verify_access_token(token)

    if not payload:
        raise HTTPException(status_code=401, detail="Invalid or expired token")

    return payload


@router.post("/create-order")
def create_payment_order(
    request: CreateOrderRequest,
    current_admin: dict = Depends(get_current_admin)
):
    """Create payment order for appointment"""
    result = payment_service.create_payment_order(
        appointment_id=request.appointment_id,
        amount=request.amount
    )

    if not result["success"]:
        raise HTTPException(status_code=400, detail=result["message"])

    return result


@router.post("/verify")
def verify_payment(request: VerifyPaymentRequest):
    """Verify payment and confirm appointment"""
    result = payment_service.confirm_payment(
        order_id=request.order_id,
        payment_id=request.payment_id,
        signature=request.signature
    )

    if not result["success"]:
        raise HTTPException(status_code=400, detail=result["message"])

    return result


@router.get("/status/{appointment_id}")
def get_payment_status(
    appointment_id: str,
    current_admin: dict = Depends(get_current_admin)
):
    """Get payment status for appointment"""
    return payment_service.get_payment_status(appointment_id)


@router.post("/refund/{appointment_id}")
def refund_payment(
    appointment_id: str,
    current_admin: dict = Depends(get_current_admin)
):
    """Refund a payment"""
    result = payment_service.refund_payment(appointment_id)

    if not result["success"]:
        raise HTTPException(status_code=400, detail=result["message"])

    return result


@router.post("/webhook")
async def razorpay_webhook(request: Request):
    """Razorpay webhook for payment updates"""
    try:
        body = await request.json()

        event_type = body.get("event")
        payload = body.get("payload", {})

        if event_type == "payment.authorized":
            payment = payload.get("payment", {})
            order_id = payment.get("order_id")
            payment_id = payment.get("id")

            logger.info(f"Payment authorized: {payment_id}")
            # Update payment status in DB

        elif event_type == "payment.failed":
            payment = payload.get("payment", {})
            order_id = payment.get("order_id")

            logger.warning(f"Payment failed for order {order_id}")

        return {"status": "ok"}
    except Exception as e:
        logger.error(f"Webhook error: {e}")
        return {"status": "error"}
from fastapi import APIRouter, HTTPException, Depends, Header, Request
from pydantic import BaseModel
from app.core.security import verify_access_token
from app.services import payment_service
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/payments", tags=["payments"])


class CreateOrderRequest(BaseModel):
    appointment_id: str
    amount: float


class VerifyPaymentRequest(BaseModel):
    order_id: str
    payment_id: str
    signature: str


def get_current_admin(authorization: str = Header(None)):
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing or invalid token")
    
    token = authorization.split(" ")[1]
    payload = verify_access_token(token)
    
    if not payload:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    
    return payload


@router.post("/create-order")
def create_payment_order(
    request: CreateOrderRequest,
    current_admin: dict = Depends(get_current_admin)
):
    """Create payment order for appointment"""
    result = payment_service.create_payment_order(
        appointment_id=request.appointment_id,
        amount=request.amount
    )
    
    if not result["success"]:
        raise HTTPException(status_code=400, detail=result["message"])
    
    return result


@router.post("/verify")
def verify_payment(request: VerifyPaymentRequest):
    """Verify payment and confirm appointment"""
    result = payment_service.confirm_payment(
        order_id=request.order_id,
        payment_id=request.payment_id,
        signature=request.signature
    )
    
    if not result["success"]:
        raise HTTPException(status_code=400, detail=result["message"])
    
    return result


@router.get("/status/{appointment_id}")
def get_payment_status(
    appointment_id: str,
    current_admin: dict = Depends(get_current_admin)
):
    """Get payment status for appointment"""
    return payment_service.get_payment_status(appointment_id)


@router.post("/refund/{appointment_id}")
def refund_payment(
    appointment_id: str,
    current_admin: dict = Depends(get_current_admin)
):
    """Refund a payment"""
    result = payment_service.refund_payment(appointment_id)
    
    if not result["success"]:
        raise HTTPException(status_code=400, detail=result["message"])
    
    return result


@router.post("/webhook")
async def razorpay_webhook(request: Request):
    """Razorpay webhook for payment updates"""
    try:
        body = await request.json()
        
        event_type = body.get("event")
        payload = body.get("payload", {})
        
        if event_type == "payment.authorized":
            payment = payload.get("payment", {})
            order_id = payment.get("order_id")
            payment_id = payment.get("id")
            
            logger.info(f"Payment authorized: {payment_id}")
            # Update payment status in DB
        
        elif event_type == "payment.failed":
            payment = payload.get("payment", {})
            order_id = payment.get("order_id")
            
            logger.warning(f"Payment failed for order {order_id}")
        
        return {"status": "ok"}
    except Exception as e:
        logger.error(f"Webhook error: {e}")
        return {"status": "error"}