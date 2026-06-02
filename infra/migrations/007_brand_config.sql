-- F-13: Brand Configuration
-- brand_config is stored as JSONB on agencies/clients; this migration guarantees the columns exist

-- Add brand_config column to agencies (if not present)
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'agencies' AND column_name = 'brand_config'
    ) THEN
        ALTER TABLE agencies ADD COLUMN brand_config JSONB DEFAULT '{}';
    END IF;
END $$;

-- Add brand_config column to clients (for white-label overrides)
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'clients' AND column_name = 'brand_config'
    ) THEN
        ALTER TABLE clients ADD COLUMN brand_config JSONB DEFAULT '{}';
    END IF;
END $$;

COMMENT ON COLUMN agencies.brand_config IS 'Agency-level brand config (colors, fonts, logo URL, etc.)';
COMMENT ON COLUMN clients.brand_config IS 'Client-level brand overrides (white-label; takes precedence over agency config)';
