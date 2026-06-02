-- F-10: Persona Agent migration
-- Add agency_id to personas (keep client_account_id for compatibility)
ALTER TABLE personas ADD COLUMN IF NOT EXISTS agency_id UUID REFERENCES agencies(id) ON DELETE CASCADE;
ALTER TABLE personas ALTER COLUMN client_account_id DROP NOT NULL;
CREATE INDEX IF NOT EXISTS idx_personas_agency_id ON personas(agency_id);

-- Add agent-related columns
ALTER TABLE personas ADD COLUMN IF NOT EXISTS source VARCHAR(50) DEFAULT 'manual';
ALTER TABLE personas ADD COLUMN IF NOT EXISTS model_used VARCHAR(100);
ALTER TABLE personas ADD COLUMN IF NOT EXISTS updated_at TIMESTAMPTZ DEFAULT NOW();
ALTER TABLE personas ADD COLUMN IF NOT EXISTS is_active BOOLEAN DEFAULT TRUE;
