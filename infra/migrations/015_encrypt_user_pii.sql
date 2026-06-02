-- M-02/M-03: encrypt user PII — add email_hash lookup column
-- email and full_name will be Fernet-encrypted at app layer; email_hash is used for lookup and uniqueness

-- 1. Add email_hash column
ALTER TABLE users ADD COLUMN IF NOT EXISTS email_hash VARCHAR;

-- 2. Backfill SHA-256(email) for existing rows (app layer will re-run on startup)
UPDATE users SET email_hash = encode(sha256(email::bytea), 'hex') WHERE email_hash IS NULL;

-- 3. Add UNIQUE constraint on email_hash
ALTER TABLE users ALTER COLUMN email_hash SET NOT NULL;
CREATE UNIQUE INDEX IF NOT EXISTS uq_users_email_hash ON users(email_hash);

-- 4. Drop UNIQUE constraint on email (ciphertext varies, original constraint is meaningless)
-- Find the constraint name first, then drop it
DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'users_email_key') THEN
        ALTER TABLE users DROP CONSTRAINT users_email_key;
    END IF;
END $$;
