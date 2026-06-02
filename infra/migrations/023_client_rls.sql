-- 023_client_rls.sql
-- PR 1: Enable row-level security for client_id-scoped tables.
-- Postgres GUCs (set per-transaction in app.core.tenant_db.get_tenant_db):
--   app.role       — caller role (platform_super_admin / platform_admin / agency_admin / ...)
--   app.client_id  — caller client_id ('' for non-client_viewer)
--   app.agency_id  — caller agency_id
-- The client_isolation policy passes through when:
--   * the row has no client_id (NULL — agency-shared data), OR
--   * the GUC is unset (e.g. background jobs, migrations), OR
--   * the row's client_id matches the GUC.

-- attribution_reports
ALTER TABLE public.attribution_reports ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.attribution_reports FORCE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS client_isolation ON public.attribution_reports;
CREATE POLICY client_isolation ON public.attribution_reports
  USING (
    client_id IS NULL
    OR current_setting('app.client_id', true) = ''
    OR client_id::text = current_setting('app.client_id', true)
  );

-- campaign_budget_configs
ALTER TABLE public.campaign_budget_configs ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.campaign_budget_configs FORCE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS client_isolation ON public.campaign_budget_configs;
CREATE POLICY client_isolation ON public.campaign_budget_configs
  USING (
    client_id IS NULL
    OR current_setting('app.client_id', true) = ''
    OR client_id::text = current_setting('app.client_id', true)
  );

-- consent_records
ALTER TABLE public.consent_records ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.consent_records FORCE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS client_isolation ON public.consent_records;
CREATE POLICY client_isolation ON public.consent_records
  USING (
    client_id IS NULL
    OR current_setting('app.client_id', true) = ''
    OR client_id::text = current_setting('app.client_id', true)
  );

-- credentials
ALTER TABLE public.credentials ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.credentials FORCE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS client_isolation ON public.credentials;
CREATE POLICY client_isolation ON public.credentials
  USING (
    client_id IS NULL
    OR current_setting('app.client_id', true) = ''
    OR client_id::text = current_setting('app.client_id', true)
  );

-- integrations
ALTER TABLE public.integrations ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.integrations FORCE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS client_isolation ON public.integrations;
CREATE POLICY client_isolation ON public.integrations
  USING (
    client_id IS NULL
    OR current_setting('app.client_id', true) = ''
    OR client_id::text = current_setting('app.client_id', true)
  );

-- report_schedules
ALTER TABLE public.report_schedules ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.report_schedules FORCE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS client_isolation ON public.report_schedules;
CREATE POLICY client_isolation ON public.report_schedules
  USING (
    client_id IS NULL
    OR current_setting('app.client_id', true) = ''
    OR client_id::text = current_setting('app.client_id', true)
  );

-- report_history
ALTER TABLE public.report_history ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.report_history FORCE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS client_isolation ON public.report_history;
CREATE POLICY client_isolation ON public.report_history
  USING (
    client_id IS NULL
    OR current_setting('app.client_id', true) = ''
    OR client_id::text = current_setting('app.client_id', true)
  );

-- token_usage
ALTER TABLE public.token_usage ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.token_usage FORCE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS client_isolation ON public.token_usage;
CREATE POLICY client_isolation ON public.token_usage
  USING (
    client_id IS NULL
    OR current_setting('app.client_id', true) = ''
    OR client_id::text = current_setting('app.client_id', true)
  );

-- audit_logs (client_isolation + agency_isolation)
ALTER TABLE public.audit_logs ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.audit_logs FORCE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS client_isolation ON public.audit_logs;
CREATE POLICY client_isolation ON public.audit_logs
  USING (
    client_id IS NULL
    OR current_setting('app.client_id', true) = ''
    OR client_id::text = current_setting('app.client_id', true)
  );

DROP POLICY IF EXISTS audit_logs_agency_isolation ON public.audit_logs;
CREATE POLICY audit_logs_agency_isolation ON public.audit_logs
  USING (
    current_setting('app.role', true) IN ('platform_super_admin', 'platform_admin')
    OR agency_id::text = current_setting('app.agency_id', true)
  );
