-- PR 2 — DB-per-Agency split.
-- Run AFTER backend/scripts/migrate_all_existing_agencies.py has filled
-- agencies.db_dsn for every existing row. After this migration applies,
-- a row without db_dsn is a hard error.

ALTER TABLE agencies ADD COLUMN IF NOT EXISTS db_dsn_previous TEXT;
ALTER TABLE agencies ALTER COLUMN db_dsn SET NOT NULL;
