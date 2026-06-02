-- Migration 019: user invitations table for team management.
-- Stores pending invitations issued by agency admins. Email is encrypted at rest
-- (Fernet), email_hash (SHA-256) is used for duplicate detection, and the
-- invitation token is stored as SHA-256 hash (raw token is delivered to admin once).

CREATE TABLE user_invitations (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  agency_id UUID NOT NULL REFERENCES agencies(id) ON DELETE CASCADE,
  client_id UUID NULL REFERENCES clients(id) ON DELETE SET NULL,
  email_hash TEXT NOT NULL,
  email_encrypted TEXT NOT NULL,
  role user_role NOT NULL,
  token_hash TEXT NOT NULL UNIQUE,
  invited_by UUID NOT NULL REFERENCES users(id),
  expires_at TIMESTAMPTZ NOT NULL,
  accepted_at TIMESTAMPTZ NULL,
  revoked_at TIMESTAMPTZ NULL,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_invitations_agency ON user_invitations(agency_id);
CREATE INDEX idx_invitations_email_hash ON user_invitations(email_hash);
