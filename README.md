# Appointment Bot Backend

Single-clinic WhatsApp appointment booking backend using FastAPI, Supabase,
Razorpay, SendGrid, and APScheduler.

## Setup

1. Copy `.env.example` to `.env` and fill the production values.
2. Run the SQL migrations in `migrations/` against Supabase, including
   `008_single_service_production.sql`.
3. Create the clinic admin manually in `admin_users` with:
   - `username`
   - `password_hash` generated with `app.core.security.hash_password`
   - `clinic_id` matching `CLINIC_ID`
4. Start locally:

```bash
uvicorn app.main:app --reload
```

## Payments

Set Razorpay webhook URL to:

```text
https://YOUR_API_DOMAIN/payments/webhook
```

Enable at least `payment.captured`, `payment.failed`, and `order.paid`.

## Docker

```bash
docker compose up --build
```
