import html
import logging

try:
    from sendgrid import SendGridAPIClient
    from sendgrid.helpers.mail import Mail
    SENDGRID_AVAILABLE = True
except Exception:
    SENDGRID_AVAILABLE = False

from app.core.config import get_settings

logger = logging.getLogger(__name__)


def _send_email(from_email: str, to_email: str, subject: str, html_content: str) -> bool:
    settings = get_settings()

    if not to_email:
        logger.info("Email skipped because recipient is empty")
        return False
    if not settings.SENDGRID_API_KEY:
        logger.warning("SendGrid API key not configured")
        return False
    if not SENDGRID_AVAILABLE:
        logger.warning("sendgrid package not installed; email disabled")
        return False

    try:
        message = Mail(
            from_email=from_email or settings.SENDER_EMAIL,
            to_emails=to_email,
            subject=subject,
            html_content=html_content,
        )
        response = SendGridAPIClient(settings.SENDGRID_API_KEY).send(message)
        return response.status_code == 202
    except Exception as exc:
        logger.error("Failed to send email to %s: %s", to_email, exc)
        return False


def _appointment_parts(appointment: dict) -> tuple[dict, dict, dict]:
    patient = appointment.get("patients") or {}
    slot = appointment.get("slots") or {}
    clinic = appointment.get("clinics") or {}
    return patient, slot, clinic


def send_patient_booking_email(appointment: dict) -> bool:
    settings = get_settings()
    patient, slot, clinic = _appointment_parts(appointment)
    patient_email = patient.get("email")
    patient_name = patient.get("name") or "Patient"
    clinic_name = clinic.get("name") or "Clinic"
    clinic_phone = settings.CLINIC_PHONE or "the clinic"

    subject = f"Appointment Confirmed - {clinic_name}"
    body = f"""
    <h2>Appointment Confirmed</h2>
    <p>Hello {html.escape(patient_name)},</p>
    <p>Your appointment at <strong>{html.escape(clinic_name)}</strong> is confirmed.</p>
    <div style="background:#f6f8fa;padding:16px;border-radius:6px">
      <p><strong>Date:</strong> {html.escape(str(slot.get("slot_date", "")))}</p>
      <p><strong>Time:</strong> {html.escape(str(slot.get("start_time", ""))[:5])}</p>
      <p><strong>Clinic:</strong> {html.escape(clinic_name)}</p>
      <p><strong>Contact:</strong> {html.escape(clinic_phone)}</p>
    </div>
    <p>Please arrive 10 minutes early.</p>
    <p>Regards,<br>{html.escape(clinic_name)}</p>
    """

    sent = _send_email(
        from_email=settings.CLINIC_EMAIL or settings.SENDER_EMAIL,
        to_email=patient_email,
        subject=subject,
        html_content=body,
    )
    if sent:
        logger.info("Patient booking email sent to %s", patient_email)
    return sent


def send_admin_booking_notification(appointment: dict) -> bool:
    settings = get_settings()
    patient, slot, clinic = _appointment_parts(appointment)
    clinic_name = clinic.get("name") or "Clinic"

    subject = f"[{clinic_name}] New paid appointment"
    body = f"""
    <h2>New Paid Appointment</h2>
    <div style="background:#f6f8fa;padding:16px;border-radius:6px">
      <p><strong>Patient:</strong> {html.escape(patient.get("name") or "N/A")}</p>
      <p><strong>Age:</strong> {html.escape(str(patient.get("age") or "N/A"))}</p>
      <p><strong>Phone:</strong> {html.escape(patient.get("whatsapp_number") or "N/A")}</p>
      <p><strong>Email:</strong> {html.escape(patient.get("email") or "N/A")}</p>
      <p><strong>Date:</strong> {html.escape(str(slot.get("slot_date", "")))}</p>
      <p><strong>Time:</strong> {html.escape(str(slot.get("start_time", ""))[:5])}</p>
      <p><strong>Complaint/Notes:</strong> {html.escape(appointment.get("complaint_notes") or "N/A")}</p>
    </div>
    """

    sent = _send_email(
        from_email=settings.SENDER_EMAIL,
        to_email=settings.DEVELOPER_EMAIL,
        subject=subject,
        html_content=body,
    )
    if sent:
        logger.info("Admin booking notification sent to %s", settings.DEVELOPER_EMAIL)
    return sent


def send_appointment_reminder_email(appointment: dict) -> bool:
    settings = get_settings()
    patient, slot, clinic = _appointment_parts(appointment)
    patient_email = patient.get("email")
    patient_name = patient.get("name") or "Patient"
    clinic_name = clinic.get("name") or "Clinic"

    subject = f"Appointment Reminder - {clinic_name}"
    body = f"""
    <h2>Appointment Reminder</h2>
    <p>Hello {html.escape(patient_name)},</p>
    <p>This is a reminder for your appointment at <strong>{html.escape(clinic_name)}</strong>.</p>
    <div style="background:#f6f8fa;padding:16px;border-radius:6px">
      <p><strong>Date:</strong> {html.escape(str(slot.get("slot_date", "")))}</p>
      <p><strong>Time:</strong> {html.escape(str(slot.get("start_time", ""))[:5])}</p>
      <p><strong>Contact:</strong> {html.escape(settings.CLINIC_PHONE or "")}</p>
    </div>
    <p>Regards,<br>{html.escape(clinic_name)}</p>
    """

    sent = _send_email(
        from_email=settings.CLINIC_EMAIL or settings.SENDER_EMAIL,
        to_email=patient_email,
        subject=subject,
        html_content=body,
    )
    if sent:
        logger.info("Reminder email sent to %s", patient_email)
    return sent


def send_cancellation_email(
    patient_email: str,
    patient_name: str,
    clinic_name: str,
    slot_date: str,
    slot_time: str,
) -> bool:
    settings = get_settings()
    body = f"""
    <h2>Appointment Cancelled</h2>
    <p>Hello {html.escape(patient_name or "Patient")},</p>
    <p>Your appointment at <strong>{html.escape(clinic_name)}</strong> has been cancelled.</p>
    <p><strong>Date:</strong> {html.escape(slot_date)}</p>
    <p><strong>Time:</strong> {html.escape(slot_time[:5])}</p>
    """
    return _send_email(
        from_email=settings.CLINIC_EMAIL or settings.SENDER_EMAIL,
        to_email=patient_email,
        subject=f"Appointment Cancelled - {clinic_name}",
        html_content=body,
    )


def send_refund_email(patient_email: str, patient_name: str, clinic_name: str, amount: float) -> bool:
    settings = get_settings()
    body = f"""
    <h2>Refund Processed</h2>
    <p>Hello {html.escape(patient_name or "Patient")},</p>
    <p>Your refund for <strong>Rs. {amount:.2f}</strong> has been processed.</p>
    """
    return _send_email(
        from_email=settings.CLINIC_EMAIL or settings.SENDER_EMAIL,
        to_email=patient_email,
        subject=f"Refund Processed - {clinic_name}",
        html_content=body,
    )
