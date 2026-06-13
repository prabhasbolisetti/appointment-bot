from fastapi import APIRouter, HTTPException, Depends, Header, Query
from app.core.security import verify_access_token
from app.services import appointment_service
from app.models.appointment import AppointmentResponse

router = APIRouter(
    prefix="/admin/appointments",
    tags=["admin-appointments"]
)


def get_current_admin(authorization: str = Header(None)):
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=401,
            detail="Missing or invalid token"
        )

    token = authorization.split(" ")[1]
    payload = verify_access_token(token)

    if not payload:
        raise HTTPException(
            status_code=401,
            detail="Invalid or expired token"
        )

    return payload


@router.get("/", response_model=list[AppointmentResponse])
def list_appointments(
    status: str = Query(None),
    current_admin: dict = Depends(get_current_admin)
):
    clinic_id = current_admin["clinic_id"]

    appointments = appointment_service.get_appointments_by_clinic(
        clinic_id,
        status
    )

    return appointments


@router.get("/{appointment_id}", response_model=AppointmentResponse)
def get_appointment(
    appointment_id: str,
    current_admin: dict = Depends(get_current_admin)
):
    appointment = appointment_service.get_appointment(appointment_id)

    if not appointment:
        raise HTTPException(
            status_code=404,
            detail="Appointment not found"
        )

    if appointment["clinic_id"] != current_admin["clinic_id"]:
        raise HTTPException(
            status_code=403,
            detail="Not authorized"
        )

    return appointment


@router.put("/{appointment_id}/cancel")
def cancel_appointment(
    appointment_id: str,
    current_admin: dict = Depends(get_current_admin)
):
    appointment = appointment_service.get_appointment(appointment_id)

    if not appointment:
        raise HTTPException(
            status_code=404,
            detail="Appointment not found"
        )

    if appointment["clinic_id"] != current_admin["clinic_id"]:
        raise HTTPException(
            status_code=403,
            detail="Not authorized"
        )

    appointment_service.cancel_appointment(appointment_id)

    return {
        "status": "cancelled"
    }


@router.put("/{appointment_id}/complete")
def complete_appointment(
    appointment_id: str,
    current_admin: dict = Depends(get_current_admin)
):
    appointment = appointment_service.get_appointment(appointment_id)

    if not appointment:
        raise HTTPException(
            status_code=404,
            detail="Appointment not found"
        )

    if appointment["clinic_id"] != current_admin["clinic_id"]:
        raise HTTPException(
            status_code=403,
            detail="Not authorized"
        )

    appointment_service.complete_appointment(appointment_id)

    return {
        "status": "confirmed"
    }