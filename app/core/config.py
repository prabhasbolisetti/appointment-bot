from pydantic_settings import BaseSettings
from functools import lru_cache
from typing import List


class Settings(BaseSettings):
    # Supabase
    SUPABASE_URL: str
    SUPABASE_SERVICE_KEY: str

    # Razorpay
    RAZORPAY_KEY_ID: str = ""
    RAZORPAY_KEY_SECRET: str = ""
    RAZORPAY_WEBHOOK_SECRET: str = ""

    # WhatsApp
    WHATSAPP_TOKEN: str = ""
    WHATSAPP_PHONE_NUMBER_ID: str = ""
    WEBHOOK_VERIFY_TOKEN: str

    # SendGrid
    SENDGRID_API_KEY: str = ""
    SENDER_EMAIL: str = "noreply@example.com"
    DEVELOPER_EMAIL: str = ""
    CLINIC_EMAIL: str = ""
    CLINIC_PHONE: str = ""

    # Single clinic
    CLINIC_ID: str = ""

    # Frontend
    FRONTEND_BASE_URL: str = "http://localhost:5173"
    CORS_ORIGINS: str = "http://localhost:5173,http://localhost:3000"

    # Auth
    JWT_SECRET: str = ""

    # App
    APP_ENV: str = "development"

    @property
    def cors_origins_list(self) -> List[str]:
        return [
            origin.strip()
            for origin in self.CORS_ORIGINS.split(",")
            if origin.strip()
        ]

    @property
    def jwt_secret(self) -> str:
        return self.JWT_SECRET or self.WEBHOOK_VERIFY_TOKEN

    def validate_startup(self) -> None:
        required = [
            "SUPABASE_URL",
            "SUPABASE_SERVICE_KEY",
            "WEBHOOK_VERIFY_TOKEN",
            "CLINIC_ID",
        ]

        if self.APP_ENV == "production":
            required.extend([
                "RAZORPAY_KEY_ID",
                "RAZORPAY_KEY_SECRET",
                "RAZORPAY_WEBHOOK_SECRET",
                "SENDGRID_API_KEY",
                "DEVELOPER_EMAIL",
                "CLINIC_EMAIL",
                "CLINIC_PHONE",
                "WHATSAPP_TOKEN",
                "WHATSAPP_PHONE_NUMBER_ID",
            ])

        missing = [name for name in required if not getattr(self, name, "")]
        if missing:
            joined = ", ".join(missing)
            raise ValueError(f"Missing required environment variables: {joined}")

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


@lru_cache()
def get_settings() -> Settings:
    return Settings()
