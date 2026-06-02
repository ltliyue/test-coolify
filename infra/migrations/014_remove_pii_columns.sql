-- C-03: data minimization — drop plaintext PII columns from consent_records
-- subject_email is superseded by subject_hash; plaintext is no longer needed
ALTER TABLE consent_records DROP COLUMN IF EXISTS subject_email;

-- DSAR's subject_email already holds a hash (C-3 fix); rename column for clarity
ALTER TABLE dsar_requests RENAME COLUMN subject_email TO subject_email_hash;
