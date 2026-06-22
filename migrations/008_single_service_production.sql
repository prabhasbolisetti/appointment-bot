ALTER TABLE patients
ADD COLUMN IF NOT EXISTS email TEXT;

ALTER TABLE patients
ADD COLUMN IF NOT EXISTS age INTEGER;

ALTER TABLE appointments
ADD COLUMN IF NOT EXISTS complaint_notes TEXT;

ALTER TABLE appointments
ADD COLUMN IF NOT EXISTS clinic_id UUID REFERENCES clinics(id);

DO $$
BEGIN
    IF EXISTS (
        SELECT 1
        FROM pg_constraint
        WHERE conname = 'appointments_status_check'
    ) THEN
        ALTER TABLE appointments DROP CONSTRAINT appointments_status_check;
    END IF;

    ALTER TABLE appointments
    ADD CONSTRAINT appointments_status_check
    CHECK (status IN ('pending', 'confirmed', 'completed', 'cancelled'));
END $$;

CREATE TABLE IF NOT EXISTS admin_users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    clinic_id UUID NOT NULL REFERENCES clinics(id) ON DELETE CASCADE,
    email TEXT,
    username TEXT,
    password_hash TEXT NOT NULL,
    full_name TEXT NOT NULL,
    is_active BOOLEAN NOT NULL DEFAULT true,
    last_login TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

ALTER TABLE admin_users
ADD COLUMN IF NOT EXISTS username TEXT;

UPDATE admin_users
SET username = COALESCE(username, 'admin_' || SUBSTRING(id::TEXT FROM 1 FOR 8))
WHERE username IS NULL OR username = '';

ALTER TABLE admin_users
ALTER COLUMN username SET NOT NULL;

CREATE UNIQUE INDEX IF NOT EXISTS idx_admin_users_username
ON admin_users (username);

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1
        FROM pg_trigger
        WHERE tgname = 'trg_admin_users_updated_at'
    ) THEN
        CREATE TRIGGER trg_admin_users_updated_at
        BEFORE UPDATE ON admin_users
        FOR EACH ROW EXECUTE FUNCTION update_updated_at();
    END IF;
END $$;

ALTER TABLE payments
ADD COLUMN IF NOT EXISTS razorpay_event_id TEXT;

ALTER TABLE payments
ADD COLUMN IF NOT EXISTS webhook_processed_at TIMESTAMPTZ;

CREATE UNIQUE INDEX IF NOT EXISTS idx_payments_razorpay_event_id
ON payments (razorpay_event_id)
WHERE razorpay_event_id IS NOT NULL;

CREATE TABLE IF NOT EXISTS payment_webhooks (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    event_id TEXT UNIQUE NOT NULL,
    event_type TEXT NOT NULL,
    signature TEXT,
    raw_payload JSONB NOT NULL,
    status TEXT NOT NULL DEFAULT 'received'
        CHECK (status IN ('received', 'processed', 'ignored', 'failed')),
    error TEXT,
    received_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    processed_at TIMESTAMPTZ
);
