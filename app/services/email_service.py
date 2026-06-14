try:
    from sendgrid import SendGridAPIClient
    from sendgrid.helpers.mail import Mail, Email, To
    SENDGRID_AVAILABLE = True
except Exception:
    SENDGRID_AVAILABLE = False

from app.core.config import get_settings
import logging

logger = logging.getLogger(__name__)


def send_booking_confirmation_email(patient_email: str, patient_name: str, clinic_name: str, slot_date: str, slot_time: str) -> bool:
    """Send booking confirmation email"""
    settings = get_settings()
    
    if not settings.SENDGRID_API_KEY:
        logger.warning("SendGrid API key not configured")
        return False
    if not SENDGRID_AVAILABLE:
        logger.warning("sendgrid package not installed; email disabled")
        return False
    
    try:
        message = Mail(
            from_email=settings.SENDER_EMAIL,
            to_emails=patient_email,
            subject=f"Appointment Confirmed - {clinic_name}",
            html_content=f"""
            <h2>Appointment Confirmed!</h2>
            <p>Hello {patient_name},</p>
            <p>Your appointment has been confirmed at <strong>{clinic_name}</strong>.</p>
            
            <div style="background-color: #f0f0f0; padding: 20px; border-radius: 5px;">
                <p><strong>Date:</strong> {slot_date}</p>
                <p><strong>Time:</strong> {slot_time}</p>
                <p><strong>Clinic:</strong> {clinic_name}</p>
            </div>
            
            <p>Please arrive 10 minutes early. If you need to cancel or reschedule, reply to this email or contact us on WhatsApp.</p>
            
            <p>Thank you,<br>{clinic_name}</p>
            """
        )
        
        sg = SendGridAPIClient(settings.SENDGRID_API_KEY)
        response = sg.send(message)
        
        logger.info(f"Booking confirmation email sent to {patient_email}")
        return response.status_code == 202
    except Exception as e:
        logger.error(f"Failed to send booking confirmation email: {e}")
        return False


def send_appointment_reminder_email(patient_email: str, patient_name: str, clinic_name: str, slot_date: str, slot_time: str) -> bool:
    """Send appointment reminder email"""
    settings = get_settings()
    
    if not settings.SENDGRID_API_KEY:
        logger.warning("SendGrid API key not configured")
        return False
    if not SENDGRID_AVAILABLE:
        logger.warning("sendgrid package not installed; email disabled")
        return False
    
    try:
        message = Mail(
            from_email=settings.SENDER_EMAIL,
            to_emails=patient_email,
            subject=f"Appointment Reminder - {clinic_name}",
            html_content=f"""
            <h2>Appointment Reminder</h2>
            <p>Hello {patient_name},</p>
            <p>This is a reminder that you have an appointment coming up at <strong>{clinic_name}</strong>.</p>
            
            <div style="background-color: #f0f0f0; padding: 20px; border-radius: 5px;">
                <p><strong>Date:</strong> {slot_date}</p>
                <p><strong>Time:</strong> {slot_time}</p>
                <p><strong>Clinic:</strong> {clinic_name}</p>
            </div>
            
            <p>Please confirm your attendance or let us know if you need to reschedule.</p>
            
            <p>Thank you,<br>{clinic_name}</p>
            """
        )
        
        sg = SendGridAPIClient(settings.SENDGRID_API_KEY)
        response = sg.send(message)
        
        logger.info(f"Reminder email sent to {patient_email}")
        return response.status_code == 202
    except Exception as e:
        logger.error(f"Failed to send reminder email: {e}")
        return False


def send_cancellation_email(patient_email: str, patient_name: str, clinic_name: str, slot_date: str, slot_time: str) -> bool:
    """Send appointment cancellation email"""
    settings = get_settings()
    
    if not settings.SENDGRID_API_KEY:
        logger.warning("SendGrid API key not configured")
        return False
    if not SENDGRID_AVAILABLE:
        logger.warning("sendgrid package not installed; email disabled")
        return False
    
    try:
        message = Mail(
            from_email=settings.SENDER_EMAIL,
            to_emails=patient_email,
            subject=f"Appointment Cancelled - {clinic_name}",
            html_content=f"""
            <h2>Appointment Cancelled</h2>
            <p>Hello {patient_name},</p>
            <p>Your appointment at <strong>{clinic_name}</strong> has been cancelled.</p>
            
            <div style="background-color: #f0f0f0; padding: 20px; border-radius: 5px;">
                <p><strong>Date:</strong> {slot_date}</p>
                <p><strong>Time:</strong> {slot_time}</p>
                <p><strong>Clinic:</strong> {clinic_name}</p>
            </div>
            
            <p>If this was unexpected, please contact us to rebook your appointment.</p>
            
            <p>Thank you,<br>{clinic_name}</p>
            """
        )
        
        sg = SendGridAPIClient(settings.SENDGRID_API_KEY)
        response = sg.send(message)
        
        logger.info(f"Cancellation email sent to {patient_email}")
        return response.status_code == 202
    except Exception as e:
        logger.error(f"Failed to send cancellation email: {e}")
        return False


def send_refund_email(patient_email: str, patient_name: str, clinic_name: str, amount: float) -> bool:
    """Send refund notification email"""
    settings = get_settings()
    
    if not settings.SENDGRID_API_KEY:
        logger.warning("SendGrid API key not configured")
        return False
    if not SENDGRID_AVAILABLE:
        logger.warning("sendgrid package not installed; email disabled")
        return False
    
    try:
        message = Mail(
            from_email=settings.SENDER_EMAIL,
            to_emails=patient_email,
            subject=f"Refund Processed - {clinic_name}",
            html_content=f"""
            <h2>Refund Processed</h2>
            <p>Hello {patient_name},</p>
            <p>We have processed a refund for your appointment at <strong>{clinic_name}</strong>.</p>
            
            <div style="background-color: #f0f0f0; padding: 20px; border-radius: 5px;">
                <p><strong>Refund Amount:</strong> ₹{amount:.2f}</p>
                <p>The refund will be credited to your original payment method within 3-5 business days.</p>
            </div>
            
            <p>If you have any questions, please contact us.</p>
            
            <p>Thank you,<br>{clinic_name}</p>
            """
        )
        
        sg = SendGridAPIClient(settings.SENDGRID_API_KEY)
        response = sg.send(message)
        
        logger.info(f"Refund email sent to {patient_email}")
        return response.status_code == 202
    except Exception as e:
        logger.error(f"Failed to send refund email: {e}")
        return False


def send_admin_notification(admin_email: str, clinic_name: str, subject: str, message: str) -> bool:
    """Send notification to admin"""
    settings = get_settings()
    
    if not settings.SENDGRID_API_KEY:
        logger.warning("SendGrid API key not configured")
        return False
    if not SENDGRID_AVAILABLE:
        logger.warning("sendgrid package not installed; email disabled")
        return False
    
    try:
        email = Mail(
            from_email=settings.SENDER_EMAIL,
            to_emails=admin_email,
            subject=f"[{clinic_name}] {subject}",
            html_content=f"<p>{message}</p>"
        )
        
        sg = SendGridAPIClient(settings.SENDGRID_API_KEY)
        response = sg.send(email)
        
        logger.info(f"Admin notification sent to {admin_email}")
        return response.status_code == 202
    except Exception as e:
        logger.error(f"Failed to send admin notification: {e}")
        return False