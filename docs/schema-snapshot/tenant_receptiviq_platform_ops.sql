--
-- PostgreSQL database dump
--

\restrict istd84JfrBwHHhjZjj7Fx2iOLaf7KU8FpIoQ3Fsu1ANy0HaX4e8Gc9bDhpgpNKZ

-- Dumped from database version 18.1
-- Dumped by pg_dump version 18.1 (Homebrew)

SET statement_timeout = 0;
SET lock_timeout = 0;
SET idle_in_transaction_session_timeout = 0;
SET transaction_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SELECT pg_catalog.set_config('search_path', '', false);
SET check_function_bodies = false;
SET xmloption = content;
SET client_min_messages = warning;
SET row_security = off;

--
-- Name: agency_plan; Type: TYPE; Schema: public; Owner: -
--

CREATE TYPE public.agency_plan AS ENUM (
    'starter',
    'growth',
    'enterprise'
);


--
-- Name: agency_status; Type: TYPE; Schema: public; Owner: -
--

CREATE TYPE public.agency_status AS ENUM (
    'active',
    'suspended',
    'trial'
);


--
-- Name: auth_type; Type: TYPE; Schema: public; Owner: -
--

CREATE TYPE public.auth_type AS ENUM (
    'oauth',
    'api_key',
    'service_account'
);


--
-- Name: client_status; Type: TYPE; Schema: public; Owner: -
--

CREATE TYPE public.client_status AS ENUM (
    'active',
    'inactive'
);


--
-- Name: consent_purpose; Type: TYPE; Schema: public; Owner: -
--

CREATE TYPE public.consent_purpose AS ENUM (
    'analytics',
    'marketing',
    'cross_device',
    'data_sharing',
    'ai_processing'
);


--
-- Name: credential_status; Type: TYPE; Schema: public; Owner: -
--

CREATE TYPE public.credential_status AS ENUM (
    'valid',
    'expired',
    'error',
    'revoked'
);


--
-- Name: credential_type; Type: TYPE; Schema: public; Owner: -
--

CREATE TYPE public.credential_type AS ENUM (
    'oauth',
    'api_key',
    'service_account'
);


--
-- Name: dsar_status; Type: TYPE; Schema: public; Owner: -
--

CREATE TYPE public.dsar_status AS ENUM (
    'pending',
    'in_progress',
    'completed',
    'rejected',
    'appealed'
);


--
-- Name: dsar_type; Type: TYPE; Schema: public; Owner: -
--

CREATE TYPE public.dsar_type AS ENUM (
    'access',
    'delete',
    'export',
    'rectify',
    'restrict',
    'portability'
);


--
-- Name: generationstatus; Type: TYPE; Schema: public; Owner: -
--

CREATE TYPE public.generationstatus AS ENUM (
    'PENDING',
    'PROCESSING',
    'COMPLETED',
    'FAILED'
);


--
-- Name: integration_platform; Type: TYPE; Schema: public; Owner: -
--

CREATE TYPE public.integration_platform AS ENUM (
    'ga4',
    'meta_ads',
    'hubspot',
    'tiktok_ads',
    'dv360',
    'stackadapt',
    'leadrx',
    'liveramp',
    'quorum',
    'canva',
    'adobe_firefly',
    'icon_app'
);


--
-- Name: integration_status; Type: TYPE; Schema: public; Owner: -
--

CREATE TYPE public.integration_status AS ENUM (
    'disconnected',
    'connected',
    'expired',
    'error'
);


--
-- Name: platform; Type: TYPE; Schema: public; Owner: -
--

CREATE TYPE public.platform AS ENUM (
    'INSTAGRAM',
    'FACEBOOK',
    'TIKTOK',
    'TWITTER'
);


--
-- Name: regulation; Type: TYPE; Schema: public; Owner: -
--

CREATE TYPE public.regulation AS ENUM (
    'gdpr',
    'ccpa',
    'hipaa'
);


--
-- Name: resultstatus; Type: TYPE; Schema: public; Owner: -
--

CREATE TYPE public.resultstatus AS ENUM (
    'PENDING',
    'PROCESSING',
    'COMPLETED',
    'FAILED'
);


--
-- Name: sync_status; Type: TYPE; Schema: public; Owner: -
--

CREATE TYPE public.sync_status AS ENUM (
    'pending',
    'running',
    'success',
    'failed',
    'cancelled'
);


--
-- Name: syncstatus; Type: TYPE; Schema: public; Owner: -
--

CREATE TYPE public.syncstatus AS ENUM (
    'SUCCESS',
    'FAILED'
);


--
-- Name: user_role; Type: TYPE; Schema: public; Owner: -
--

CREATE TYPE public.user_role AS ENUM (
    'agency_admin',
    'agency_ops',
    'client_viewer',
    'platform_super_admin',
    'platform_admin'
);


SET default_tablespace = '';

SET default_table_access_method = heap;

--
-- Name: attribution_reports; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.attribution_reports (
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    agency_id uuid NOT NULL,
    client_id uuid,
    user_id uuid NOT NULL,
    title character varying(255) NOT NULL,
    report_type character varying(50) DEFAULT 'multi_touch'::character varying NOT NULL,
    date_range_start date,
    date_range_end date,
    channels jsonb DEFAULT '[]'::jsonb,
    model_config jsonb DEFAULT '{}'::jsonb,
    results jsonb DEFAULT '{}'::jsonb,
    insights text,
    model_used character varying(100),
    status character varying(50) DEFAULT 'completed'::character varying NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL
);


--
-- Name: audience_exports; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.audience_exports (
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    agency_id uuid NOT NULL,
    persona_id uuid NOT NULL,
    platform character varying(50) NOT NULL,
    external_audience_id character varying(255),
    targeting_spec jsonb,
    status character varying(20) DEFAULT 'pending'::character varying NOT NULL,
    error_message text,
    retry_count integer DEFAULT 0 NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    completed_at timestamp with time zone
);


--
-- Name: brands; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.brands (
    id uuid NOT NULL,
    user_id uuid NOT NULL,
    tenant_id uuid NOT NULL,
    name character varying(255) NOT NULL,
    logo_url character varying(500),
    slogan character varying(500),
    primary_color character varying(7),
    product_description text,
    industry character varying(100),
    target_audience character varying(500),
    brand_tone character varying(255),
    is_active boolean NOT NULL,
    created_at timestamp with time zone NOT NULL,
    updated_at timestamp with time zone NOT NULL
);


--
-- Name: campaign_budget_configs; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.campaign_budget_configs (
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    agency_id uuid NOT NULL,
    client_id uuid,
    platform character varying(50) NOT NULL,
    external_campaign_id character varying(255) NOT NULL,
    campaign_name character varying(500),
    daily_budget numeric(12,2),
    total_budget numeric(12,2),
    pacing_alert_threshold double precision DEFAULT 0.15 NOT NULL,
    alert_enabled boolean DEFAULT true NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now()
);


--
-- Name: client_accounts; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.client_accounts (
    id uuid NOT NULL,
    tenant_id uuid NOT NULL,
    name character varying(255) NOT NULL,
    vertical character varying(100),
    daily_spend numeric(12,2) NOT NULL,
    is_active boolean NOT NULL,
    created_at timestamp with time zone NOT NULL
);


--
-- Name: clients; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.clients (
    id uuid NOT NULL,
    agency_id uuid NOT NULL,
    name character varying NOT NULL,
    slug character varying NOT NULL,
    status public.client_status NOT NULL,
    verticals text[] NOT NULL,
    brand_config jsonb,
    created_at timestamp with time zone NOT NULL,
    updated_at timestamp with time zone NOT NULL
);


--
-- Name: consent_records; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.consent_records (
    id uuid NOT NULL,
    agency_id uuid NOT NULL,
    client_id uuid,
    subject_hash character varying NOT NULL,
    purpose public.consent_purpose NOT NULL,
    granted boolean NOT NULL,
    do_not_sell boolean NOT NULL,
    consent_text text,
    consent_version character varying,
    ip_address inet,
    user_agent text,
    source character varying,
    granted_at timestamp with time zone,
    withdrawn_at timestamp with time zone,
    expires_at timestamp with time zone
);


--
-- Name: credentials; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.credentials (
    id uuid NOT NULL,
    agency_id uuid NOT NULL,
    client_id uuid,
    platform text NOT NULL,
    credential_type public.credential_type NOT NULL,
    status public.credential_status NOT NULL,
    encrypted_data text NOT NULL,
    scopes text[],
    expires_at timestamp with time zone,
    last_refreshed_at timestamp with time zone,
    error_message text,
    created_by uuid,
    created_at timestamp with time zone NOT NULL,
    updated_at timestamp with time zone NOT NULL
);


--
-- Name: dsar_requests; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.dsar_requests (
    id uuid NOT NULL,
    agency_id uuid NOT NULL,
    request_type public.dsar_type NOT NULL,
    regulation public.regulation NOT NULL,
    subject_email_hash character varying CONSTRAINT dsar_requests_subject_email_not_null NOT NULL,
    subject_name character varying,
    verification_token character varying,
    verified_at timestamp with time zone,
    status public.dsar_status NOT NULL,
    due_date timestamp with time zone,
    extended_due_date timestamp with time zone,
    assigned_to uuid,
    response_path character varying,
    rejection_reason text,
    notes text,
    created_at timestamp with time zone NOT NULL,
    completed_at timestamp with time zone,
    updated_at timestamp with time zone NOT NULL
);


--
-- Name: field_mapping_versions; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.field_mapping_versions (
    id uuid NOT NULL,
    field_mapping_id uuid NOT NULL,
    version integer NOT NULL,
    mapping_config json NOT NULL,
    changed_by uuid NOT NULL,
    change_summary character varying(500),
    created_at timestamp with time zone NOT NULL
);


--
-- Name: field_mappings; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.field_mappings (
    id uuid NOT NULL,
    tenant_id uuid,
    user_id uuid NOT NULL,
    integration_id uuid,
    name character varying(255) NOT NULL,
    mapping_config json NOT NULL,
    current_version integer NOT NULL,
    is_active boolean NOT NULL,
    created_at timestamp with time zone NOT NULL,
    updated_at timestamp with time zone NOT NULL,
    agency_id uuid,
    platform character varying(50)
);


--
-- Name: generation_results; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.generation_results (
    id uuid NOT NULL,
    generation_id uuid NOT NULL,
    platform public.platform NOT NULL,
    copy_text text,
    image_url character varying(500),
    status public.resultstatus NOT NULL,
    error_message text,
    created_at timestamp with time zone NOT NULL,
    updated_at timestamp with time zone NOT NULL
);


--
-- Name: generations; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.generations (
    id uuid NOT NULL,
    brand_id uuid,
    user_id uuid NOT NULL,
    tenant_id uuid,
    status public.generationstatus NOT NULL,
    prompt text NOT NULL,
    error_message text,
    created_at timestamp with time zone NOT NULL,
    updated_at timestamp with time zone NOT NULL,
    agency_id uuid,
    agent_type character varying(50) DEFAULT 'creative'::character varying,
    metadata jsonb DEFAULT '{}'::jsonb
);


--
-- Name: integrations; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.integrations (
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    agency_id uuid NOT NULL,
    client_id uuid,
    platform public.integration_platform NOT NULL,
    auth_type public.auth_type NOT NULL,
    status public.integration_status DEFAULT 'disconnected'::public.integration_status NOT NULL,
    credential_id uuid,
    sync_schedule jsonb,
    config jsonb,
    last_sync_at timestamp with time zone,
    current_task_id text,
    error_message text,
    connected_at timestamp with time zone,
    created_by uuid,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL
);


--
-- Name: marketing_data_points; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.marketing_data_points (
    id uuid NOT NULL,
    tenant_id uuid NOT NULL,
    integration_id uuid NOT NULL,
    date date NOT NULL,
    dimension_key character varying(64) NOT NULL,
    dimensions json NOT NULL,
    metrics json NOT NULL,
    raw_data json NOT NULL,
    synced_at timestamp with time zone NOT NULL
);


--
-- Name: notifications; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.notifications (
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    agency_id uuid NOT NULL,
    user_id uuid,
    title character varying(255) NOT NULL,
    message text,
    category character varying(50) DEFAULT 'system'::character varying NOT NULL,
    severity character varying(20) DEFAULT 'info'::character varying NOT NULL,
    is_read boolean DEFAULT false NOT NULL,
    metadata jsonb DEFAULT '{}'::jsonb,
    created_at timestamp with time zone DEFAULT now() NOT NULL
);


--
-- Name: personas; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.personas (
    id uuid NOT NULL,
    client_account_id uuid,
    name character varying(255) NOT NULL,
    description text,
    psychographics json,
    channel_preferences json,
    recommended_tone character varying(100),
    created_at timestamp with time zone NOT NULL,
    agency_id uuid,
    source character varying(50) DEFAULT 'manual'::character varying,
    model_used character varying(100),
    updated_at timestamp with time zone DEFAULT now(),
    is_active boolean DEFAULT true
);


--
-- Name: report_history; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.report_history (
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    agency_id uuid NOT NULL,
    schedule_id uuid,
    client_id uuid,
    report_type character varying(50) DEFAULT 'campaign_performance'::character varying NOT NULL,
    file_path character varying(500),
    file_size_bytes integer,
    recipients_count integer DEFAULT 0 NOT NULL,
    status character varying(20) DEFAULT 'pending'::character varying NOT NULL,
    error_message text,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    completed_at timestamp with time zone
);


--
-- Name: report_schedules; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.report_schedules (
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    agency_id uuid NOT NULL,
    client_id uuid,
    schedule_name character varying(255) NOT NULL,
    frequency character varying(20) NOT NULL,
    recipients_encrypted text,
    metrics_config jsonb,
    brand_config_override jsonb,
    is_active boolean DEFAULT true NOT NULL,
    last_sent_at timestamp with time zone,
    next_run_at timestamp with time zone,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now()
);


--
-- Name: sync_logs; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.sync_logs (
    id bigint NOT NULL,
    integration_id uuid NOT NULL,
    agency_id uuid NOT NULL,
    task_id text,
    status public.sync_status DEFAULT 'pending'::public.sync_status NOT NULL,
    triggered_by text,
    records_fetched integer,
    records_written integer,
    error_message text,
    extra_data jsonb,
    started_at timestamp with time zone,
    finished_at timestamp with time zone
);


--
-- Name: sync_logs_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.sync_logs_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: sync_logs_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.sync_logs_id_seq OWNED BY public.sync_logs.id;


--
-- Name: token_usage; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.token_usage (
    id bigint NOT NULL,
    agency_id uuid NOT NULL,
    client_id uuid,
    user_id uuid,
    request_id text,
    agent_name text,
    agent_type text,
    model text NOT NULL,
    prompt_tokens integer DEFAULT 0 NOT NULL,
    completion_tokens integer DEFAULT 0 NOT NULL,
    total_tokens integer DEFAULT 0 NOT NULL,
    estimated_cost_usd numeric(10,6),
    cost_usd numeric(10,6),
    created_at timestamp with time zone DEFAULT now() NOT NULL
);


--
-- Name: token_usage_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.token_usage_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: token_usage_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.token_usage_id_seq OWNED BY public.token_usage.id;


--
-- Name: sync_logs id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.sync_logs ALTER COLUMN id SET DEFAULT nextval('public.sync_logs_id_seq'::regclass);


--
-- Name: token_usage id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.token_usage ALTER COLUMN id SET DEFAULT nextval('public.token_usage_id_seq'::regclass);


--
-- Name: attribution_reports attribution_reports_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.attribution_reports
    ADD CONSTRAINT attribution_reports_pkey PRIMARY KEY (id);


--
-- Name: audience_exports audience_exports_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.audience_exports
    ADD CONSTRAINT audience_exports_pkey PRIMARY KEY (id);


--
-- Name: brands brands_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.brands
    ADD CONSTRAINT brands_pkey PRIMARY KEY (id);


--
-- Name: campaign_budget_configs campaign_budget_configs_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.campaign_budget_configs
    ADD CONSTRAINT campaign_budget_configs_pkey PRIMARY KEY (id);


--
-- Name: client_accounts client_accounts_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.client_accounts
    ADD CONSTRAINT client_accounts_pkey PRIMARY KEY (id);


--
-- Name: clients clients_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.clients
    ADD CONSTRAINT clients_pkey PRIMARY KEY (id);


--
-- Name: consent_records consent_records_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.consent_records
    ADD CONSTRAINT consent_records_pkey PRIMARY KEY (id);


--
-- Name: credentials credentials_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.credentials
    ADD CONSTRAINT credentials_pkey PRIMARY KEY (id);


--
-- Name: dsar_requests dsar_requests_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.dsar_requests
    ADD CONSTRAINT dsar_requests_pkey PRIMARY KEY (id);


--
-- Name: field_mapping_versions field_mapping_versions_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.field_mapping_versions
    ADD CONSTRAINT field_mapping_versions_pkey PRIMARY KEY (id);


--
-- Name: field_mappings field_mappings_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.field_mappings
    ADD CONSTRAINT field_mappings_pkey PRIMARY KEY (id);


--
-- Name: generation_results generation_results_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.generation_results
    ADD CONSTRAINT generation_results_pkey PRIMARY KEY (id);


--
-- Name: generations generations_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.generations
    ADD CONSTRAINT generations_pkey PRIMARY KEY (id);


--
-- Name: integrations integrations_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.integrations
    ADD CONSTRAINT integrations_pkey PRIMARY KEY (id);


--
-- Name: marketing_data_points marketing_data_points_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.marketing_data_points
    ADD CONSTRAINT marketing_data_points_pkey PRIMARY KEY (id);


--
-- Name: notifications notifications_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.notifications
    ADD CONSTRAINT notifications_pkey PRIMARY KEY (id);


--
-- Name: personas personas_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.personas
    ADD CONSTRAINT personas_pkey PRIMARY KEY (id);


--
-- Name: report_history report_history_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.report_history
    ADD CONSTRAINT report_history_pkey PRIMARY KEY (id);


--
-- Name: report_schedules report_schedules_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.report_schedules
    ADD CONSTRAINT report_schedules_pkey PRIMARY KEY (id);


--
-- Name: sync_logs sync_logs_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.sync_logs
    ADD CONSTRAINT sync_logs_pkey PRIMARY KEY (id);


--
-- Name: token_usage token_usage_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.token_usage
    ADD CONSTRAINT token_usage_pkey PRIMARY KEY (id);


--
-- Name: campaign_budget_configs uq_budget_config; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.campaign_budget_configs
    ADD CONSTRAINT uq_budget_config UNIQUE (agency_id, platform, external_campaign_id);


--
-- Name: field_mapping_versions uq_fmv_mapping_version; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.field_mapping_versions
    ADD CONSTRAINT uq_fmv_mapping_version UNIQUE (field_mapping_id, version);


--
-- Name: marketing_data_points uq_mdp_tenant_integration_date_dim; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.marketing_data_points
    ADD CONSTRAINT uq_mdp_tenant_integration_date_dim UNIQUE (tenant_id, integration_id, date, dimension_key);


--
-- Name: idx_attribution_reports_agency; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_attribution_reports_agency ON public.attribution_reports USING btree (agency_id);


--
-- Name: idx_attribution_reports_created; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_attribution_reports_created ON public.attribution_reports USING btree (created_at DESC);


--
-- Name: idx_audience_export_agency; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_audience_export_agency ON public.audience_exports USING btree (agency_id);


--
-- Name: idx_audience_export_persona; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_audience_export_persona ON public.audience_exports USING btree (persona_id);


--
-- Name: idx_budget_config_agency; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_budget_config_agency ON public.campaign_budget_configs USING btree (agency_id);


--
-- Name: idx_budget_config_alert; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_budget_config_alert ON public.campaign_budget_configs USING btree (alert_enabled) WHERE (alert_enabled = true);


--
-- Name: idx_field_mappings_agency_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_field_mappings_agency_id ON public.field_mappings USING btree (agency_id);


--
-- Name: idx_generations_agency_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_generations_agency_id ON public.generations USING btree (agency_id);


--
-- Name: idx_notifications_agency; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_notifications_agency ON public.notifications USING btree (agency_id, created_at DESC);


--
-- Name: idx_notifications_user; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_notifications_user ON public.notifications USING btree (user_id, is_read, created_at DESC);


--
-- Name: idx_personas_agency_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_personas_agency_id ON public.personas USING btree (agency_id);


--
-- Name: idx_report_history_agency; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_report_history_agency ON public.report_history USING btree (agency_id);


--
-- Name: idx_report_schedule_agency; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_report_schedule_agency ON public.report_schedules USING btree (agency_id);


--
-- Name: idx_token_usage_agency_created; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_token_usage_agency_created ON public.token_usage USING btree (agency_id, created_at);


--
-- Name: idx_token_usage_client; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_token_usage_client ON public.token_usage USING btree (client_id, created_at);


--
-- Name: ix_field_mapping_versions_field_mapping_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_field_mapping_versions_field_mapping_id ON public.field_mapping_versions USING btree (field_mapping_id);


--
-- Name: ix_field_mappings_tenant_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_field_mappings_tenant_id ON public.field_mappings USING btree (tenant_id);


--
-- Name: ix_field_mappings_user_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_field_mappings_user_id ON public.field_mappings USING btree (user_id);


--
-- Name: ix_marketing_data_points_date; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_marketing_data_points_date ON public.marketing_data_points USING btree (date);


--
-- Name: ix_marketing_data_points_integration_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_marketing_data_points_integration_id ON public.marketing_data_points USING btree (integration_id);


--
-- Name: ix_marketing_data_points_tenant_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_marketing_data_points_tenant_id ON public.marketing_data_points USING btree (tenant_id);


--
-- Name: attribution_reports attribution_reports_client_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.attribution_reports
    ADD CONSTRAINT attribution_reports_client_id_fkey FOREIGN KEY (client_id) REFERENCES public.clients(id) ON DELETE SET NULL;


--
-- Name: audience_exports audience_exports_persona_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.audience_exports
    ADD CONSTRAINT audience_exports_persona_id_fkey FOREIGN KEY (persona_id) REFERENCES public.personas(id) ON DELETE CASCADE;


--
-- Name: campaign_budget_configs campaign_budget_configs_client_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.campaign_budget_configs
    ADD CONSTRAINT campaign_budget_configs_client_id_fkey FOREIGN KEY (client_id) REFERENCES public.clients(id) ON DELETE SET NULL;


--
-- Name: consent_records consent_records_client_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.consent_records
    ADD CONSTRAINT consent_records_client_id_fkey FOREIGN KEY (client_id) REFERENCES public.clients(id) ON DELETE SET NULL;


--
-- Name: credentials credentials_client_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.credentials
    ADD CONSTRAINT credentials_client_id_fkey FOREIGN KEY (client_id) REFERENCES public.clients(id) ON DELETE SET NULL;


--
-- Name: field_mapping_versions field_mapping_versions_field_mapping_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.field_mapping_versions
    ADD CONSTRAINT field_mapping_versions_field_mapping_id_fkey FOREIGN KEY (field_mapping_id) REFERENCES public.field_mappings(id);


--
-- Name: generation_results generation_results_generation_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.generation_results
    ADD CONSTRAINT generation_results_generation_id_fkey FOREIGN KEY (generation_id) REFERENCES public.generations(id);


--
-- Name: generations generations_brand_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.generations
    ADD CONSTRAINT generations_brand_id_fkey FOREIGN KEY (brand_id) REFERENCES public.brands(id);


--
-- Name: integrations integrations_client_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.integrations
    ADD CONSTRAINT integrations_client_id_fkey FOREIGN KEY (client_id) REFERENCES public.clients(id) ON DELETE CASCADE;


--
-- Name: integrations integrations_credential_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.integrations
    ADD CONSTRAINT integrations_credential_id_fkey FOREIGN KEY (credential_id) REFERENCES public.credentials(id) ON DELETE SET NULL;


--
-- Name: personas personas_client_account_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.personas
    ADD CONSTRAINT personas_client_account_id_fkey FOREIGN KEY (client_account_id) REFERENCES public.client_accounts(id);


--
-- Name: report_history report_history_client_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.report_history
    ADD CONSTRAINT report_history_client_id_fkey FOREIGN KEY (client_id) REFERENCES public.clients(id) ON DELETE SET NULL;


--
-- Name: report_history report_history_schedule_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.report_history
    ADD CONSTRAINT report_history_schedule_id_fkey FOREIGN KEY (schedule_id) REFERENCES public.report_schedules(id) ON DELETE SET NULL;


--
-- Name: report_schedules report_schedules_client_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.report_schedules
    ADD CONSTRAINT report_schedules_client_id_fkey FOREIGN KEY (client_id) REFERENCES public.clients(id) ON DELETE SET NULL;


--
-- Name: sync_logs sync_logs_integration_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.sync_logs
    ADD CONSTRAINT sync_logs_integration_id_fkey FOREIGN KEY (integration_id) REFERENCES public.integrations(id) ON DELETE CASCADE;


--
-- Name: token_usage token_usage_client_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.token_usage
    ADD CONSTRAINT token_usage_client_id_fkey FOREIGN KEY (client_id) REFERENCES public.clients(id) ON DELETE SET NULL;


--
-- PostgreSQL database dump complete
--

\unrestrict istd84JfrBwHHhjZjj7Fx2iOLaf7KU8FpIoQ3Fsu1ANy0HaX4e8Gc9bDhpgpNKZ

