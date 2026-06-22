import logging
from typing import Optional

from fastapi import APIRouter, Depends, Header, HTTPException, Request
from pydantic import BaseModel

from app.api.dependencies import get_current_admin
from app.services import payment_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/payments", tags=["payments"])


class CreateOrderRequest(BaseModel):
    appointment_id: str
    amount: Optional[float] = None


class VerifyPaymentRequest(BaseModel):
    order_id: str
    payment_id: str
    signature: str


@router.get("/checkout/{appointment_id}")
def get_checkout_details(appointment_id: str):
    result = payment_service.get_checkout_details(appointment_id)
    if not result["success"]:
        raise HTTPException(status_code=404, detail=result["message"])
    return result


@router.post("/create-order")
def create_payment_order(request: CreateOrderRequest):
    result = payment_service.create_payment_order(
        appointment_id=request.appointment_id,
        amount=request.amount,
    )
    if not result["success"]:
        raise HTTPException(status_code=400, detail=result["message"])
    return result


@router.post("/verify")
def verify_payment(request: VerifyPaymentRequest):
    result = payment_service.confirm_payment(
        order_id=request.order_id,
        payment_id=request.payment_id,
        signature=request.signature,
    )
    if not result["success"]:
        raise HTTPException(status_code=400, detail=result["message"])
    return result


@router.post("/webhook")
async def razorpay_webhook(
    request: Request,
    x_razorpay_signature: str = Header(None),
):
    raw_body = await request.body()
    result = payment_service.process_webhook(raw_body, x_razorpay_signature)
    if not result["success"]:
        logger.warning("Razorpay webhook rejected: %s", result["message"])
        raise HTTPException(status_code=400, detail=result["message"])
    return {"status": "ok", **result}


@router.get("/status/{appointment_id}")
def get_payment_status(appointment_id: str):
    return payment_service.get_payment_status(appointment_id)


@router.post("/refund/{appointment_id}")
def refund_payment(
    appointment_id: str,
    current_admin: dict = Depends(get_current_admin),
):
    result = payment_service.refund_payment(appointment_id)
    if not result["success"]:
        raise HTTPException(status_code=400, detail=result["message"])
    return result
