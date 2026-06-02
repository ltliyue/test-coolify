-- F-11: Creative Agent migration
-- Add agency_id to generations table
ALTER TABLE generations ADD COLUMN IF NOT EXISTS agency_id UUID REFERENCES agencies(id) ON DELETE CASCADE;
ALTER TABLE generations ALTER COLUMN tenant_id DROP NOT NULL;
ALTER TABLE generations ALTER COLUMN brand_id DROP NOT NULL;
CREATE INDEX IF NOT EXISTS idx_generations_agency_id ON generations(agency_id);

-- Add agent_type column (identifies which agent generated it)
ALTER TABLE generations ADD COLUMN IF NOT EXISTS agent_type VARCHAR(50) DEFAULT 'creative';
-- Add structured metadata
ALTER TABLE generations ADD COLUMN IF NOT EXISTS metadata JSONB DEFAULT '{}';
