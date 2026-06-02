-- ─────────────────────────────────────────────────────────────────────────────
-- Migration 001: multi-tenant core schema
-- Agency → Client two-tier tenancy
-- RLS enabled from the first migration; tenant data never mixes
-- Source: ReceptivIQ/data/migrations/001_init_multi_tenant.sql
-- ─────────────────────────────────────────────────────────────────────────────

CREATE EXTENSION IF NOT EXISTS "pgcrypto";
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgvector";    -- AI embedding support

-- ── Enum types ──────────────────────────────────────────────────────────────────
CREATE TYPE tenant_status AS ENUM ('active', 'suspended', 'pending_setup');
CREATE TYPE agency_plan   AS ENUM ('pilot', 'growth', 'enterprise');
CREATE TYPE user_role     AS ENUM ('agency_admin', 'agency_ops', 'client_viewer');

-- ── Agency (top-level tenant) ─────────────────────────────────────────────────────
CREATE TABLE agencies (
    id              UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
    name            TEXT        NOT NULL,
    slug            TEXT        NOT NULL UNIQUE,
    status          tenant_status NOT NULL DEFAULT 'pending_setup',
    plan            agency_plan  NOT NULL DEFAULT 'pilot',

    -- brand config (colors, logo, fonts)
    brand           JSONB       NOT NULL DEFAULT '{"primaryColor":"#2563EB","logo":null}',

    -- rate limits
    monthly_token_budget INTEGER NOT NULL DEFAULT 0,  -- 0 = unlimited

    created_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- ── Client (second-level tenant) ─────────────────────────────────────────────────────
CREATE TABLE clients (
    id              UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
    agency_id       UUID        NOT NULL REFERENCES agencies(id) ON DELETE CASCADE,
    name            TEXT        NOT NULL,
    slug            TEXT        NOT NULL,
    status          tenant_status NOT NULL DEFAULT 'pending_setup',
    verticals       TEXT[]      NOT NULL DEFAULT '{}',

    -- client brand config (overrides agency defaults)
    brand           JSONB       NOT NULL DEFAULT '{"primaryColor":"#2563EB","logo":null}',

    created_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT now(),

    UNIQUE(agency_id, slug)
);

-- ── indexes ──────────────────────────────────────────────────────────────────────
CREATE INDEX idx_agencies_slug      ON agencies(slug);
CREATE INDEX idx_clients_agency_id  ON clients(agency_id);
CREATE INDEX idx_clients_slug       ON clients(agency_id, slug);

-- ── updated_at auto-trigger ──────────────────────────────────────────────────────
CREATE OR REPLACE FUNCTION set_updated_at()
RETURNS TRIGGER LANGUAGE plpgsql AS $$
BEGIN
    NEW.updated_at = now();
    RETURN NEW;
END;
$$;

CREATE TRIGGER agencies_updated_at
    BEFORE UPDATE ON agencies
    FOR EACH ROW EXECUTE FUNCTION set_updated_at();

CREATE TRIGGER clients_updated_at
    BEFORE UPDATE ON clients
    FOR EACH ROW EXECUTE FUNCTION set_updated_at();
