-- Adapt the field_mappings table to the ReceptivIQ-Platform agency layout
ALTER TABLE field_mappings
  ADD COLUMN IF NOT EXISTS agency_id UUID REFERENCES agencies(id) ON DELETE CASCADE,
  ADD COLUMN IF NOT EXISTS platform VARCHAR(50),
  ALTER COLUMN tenant_id DROP NOT NULL;

CREATE INDEX IF NOT EXISTS idx_field_mappings_agency_id ON field_mappings(agency_id);
