from fastapi import APIRouter, Depends, HTTPException, Query

from app.api.dependencies import get_current_admin
from app.services import appointment_service

router = APIRouter(prefix="/admin/appointments", tags=["admin-appointments"])


@router.get("/stats/overview")
def get_stats(current_admin: dict = Depends(get_current_admin)):
    return appointment_service.get_appointment_stats(current_admin["clinic_id"])


@router.get("/")
def list_appointments(
    status: str = Query(None),
    current_admin: dict = Depends(get_current_admin),
):
    return appointment_service.get_appointments_by_clinic(
        current_admin["clinic_id"],
        status,
    )


@router.get("/{appointment_id}")
def get_appointment(appointment_id: str, current_admin: dict = Depends(get_current_admin)):
    appointment = appointment_service.get_appointment(appointment_id)
    if not appointment:
        raise HTTPException(status_code=404, detail="Appointment not found")

    if appointment["clinic_id"] != current_admin["clinic_id"]:
        raise HTTPException(status_code=403, detail="Not authorized")

    return appointment


@router.put("/{appointment_id}/cancel")
def cancel_appointment(appointment_id: str, current_admin: dict = Depends(get_current_admin)):
    appointment = appointment_service.get_appointment(appointment_id)
    if not appointment:
        raise HTTPException(status_code=404, detail="Appointment not found")

    if appointment["clinic_id"] != current_admin["clinic_id"]:
        raise HTTPException(status_code=403, detail="Not authorized")

    result = appointment_service.cancel_appointment(appointment_id)
    if not result["success"]:
        raise HTTPException(status_code=400, detail=result["message"])

    return result


@router.put("/{appointment_id}/complete")
def complete_appointment(appointment_id: str, current_admin: dict = Depends(get_current_admin)):
    appointment = appointment_service.get_appointment(appointment_id)
    if not appointment:
        raise HTTPException(status_code=404, detail="Appointment not found")

    if appointment["clinic_id"] != current_admin["clinic_id"]:
        raise HTTPException(status_code=403, detail="Not authorized")

    result = appointment_service.complete_appointment(appointment_id)
    if not result["success"]:
        raise HTTPException(status_code=400, detail=result["message"])

    return result


@router.post("/{appointment_id}/refund")
def request_refund(appointment_id: str, current_admin: dict = Depends(get_current_admin)):
    appointment = appointment_service.get_appointment(appointment_id)
    if not appointment:
        raise HTTPException(status_code=404, detail="Appointment not found")

    if appointment["clinic_id"] != current_admin["clinic_id"]:
        raise HTTPException(status_code=403, detail="Not authorized")

    result = appointment_service.request_refund(appointment_id)
    if not result["success"]:
        raise HTTPException(status_code=400, detail=result["message"])

    return result
