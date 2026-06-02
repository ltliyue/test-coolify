-- 022_audit_immutability.sql
-- audit_logs must be INSERT-only forever (GDPR Art.30 + SOC2 CC7).
CREATE OR REPLACE FUNCTION audit_logs_block_modify()
RETURNS trigger LANGUAGE plpgsql AS $$
BEGIN
  RAISE EXCEPTION 'audit_logs is INSERT-only; UPDATE/DELETE rejected';
END;
$$;

DROP TRIGGER IF EXISTS audit_logs_no_update ON public.audit_logs;
CREATE TRIGGER audit_logs_no_update
  BEFORE UPDATE ON public.audit_logs
  FOR EACH ROW EXECUTE FUNCTION audit_logs_block_modify();

DROP TRIGGER IF EXISTS audit_logs_no_delete ON public.audit_logs;
CREATE TRIGGER audit_logs_no_delete
  BEFORE DELETE ON public.audit_logs
  FOR EACH ROW EXECUTE FUNCTION audit_logs_block_modify();
