-- Agency-tier schema template — Per-Agency physical Postgres database.
-- Provisioner replays this file inside a freshly-created database.
-- All Agency-owned tables live in `public` schema of the per-Agency DB.
-- Cross-DB FK constraints to the platform DB (public.agencies, public.users,
-- public.tenants) are intentionally absent — referential integrity is
-- enforced at the application layer.
-- RLS policies at the bottom enforce client_id row isolation
-- (see infra/migrations/023_client_rls.sql for the platform-DB equivalent).

-- ── Enum types (must exist before tables that reference them) ─────────────

CREATE TYPE public.agency_plan AS ENUM (
    'starter',
    'growth',
    'enterprise'
);

CREATE TYPE public.agency_status AS ENUM (
    'active',
    'suspended',
    'trial'
);

CREATE TYPE public.auth_type AS ENUM (
    'oauth',
    'api_key',
    'service_account'
);

CREATE TYPE public.client_status AS ENUM (
    'active',
    'inactive'
);

CREATE TYPE public.consent_purpose AS ENUM (
    'analytics',
    'marketing',
    'cross_device',
    'data_sharing',
    'ai_processing'
);

CREATE TYPE public.credential_status AS ENUM (
    'valid',
    'expired',
    'error',
    'revoked'
);

CREATE TYPE public.credential_type AS ENUM (
    'oauth',
    'api_key',
    'service_account'
);

CREATE TYPE public.dsar_status AS ENUM (
    'pending',
    'in_progress',
    'completed',
    'rejected',
    'appealed'
);

CREATE TYPE public.dsar_type AS ENUM (
    'access',
    'delete',
    'export',
    'rectify',
    'restrict',
    'portability'
);

CREATE TYPE public.generationstatus AS ENUM (
    'PENDING',
    'PROCESSING',
    'COMPLETED',
    'FAILED'
);

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

CREATE TYPE public.integration_status AS ENUM (
    'disconnected',
    'connected',
    'expired',
    'error'
);

CREATE TYPE public.platform AS ENUM (
    'INSTAGRAM',
    'FACEBOOK',
    'TIKTOK',
    'TWITTER'
);

CREATE TYPE public.regulation AS ENUM (
    'gdpr',
    'ccpa',
    'hipaa'
);

CREATE TYPE public.resultstatus AS ENUM (
    'PENDING',
    'PROCESSING',
    'COMPLETED',
    'FAILED'
);

CREATE TYPE public.sync_status AS ENUM (
    'pending',
    'running',
    'success',
    'failed',
    'cancelled'
);

CREATE TYPE public.syncstatus AS ENUM (
    'SUCCESS',
    'FAILED'
);

CREATE TYPE public.user_role AS ENUM (
    'agency_admin',
    'agency_ops',
    'client_viewer',
    'platform_super_admin',
    'platform_admin'
);



--
-- PostgreSQL database dump
--




--
-- Name: public; Type: SCHEMA; Schema: -; Owner: -
--





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
-- Data for Name: attribution_reports; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.attribution_reports (id, agency_id, client_id, user_id, title, report_type, date_range_start, date_range_end, channels, model_config, results, insights, model_used, status, created_at, updated_at) FROM stdin;


--
-- Data for Name: audience_exports; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.audience_exports (id, agency_id, persona_id, platform, external_audience_id, targeting_spec, status, error_message, retry_count, created_at, completed_at) FROM stdin;


--
-- Data for Name: brands; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.brands (id, user_id, tenant_id, name, logo_url, slogan, primary_color, product_description, industry, target_audience, brand_tone, is_active, created_at, updated_at) FROM stdin;


--
-- Data for Name: campaign_budget_configs; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.campaign_budget_configs (id, agency_id, client_id, platform, external_campaign_id, campaign_name, daily_budget, total_budget, pacing_alert_threshold, alert_enabled, created_at, updated_at) FROM stdin;


--
-- Data for Name: client_accounts; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.client_accounts (id, tenant_id, name, vertical, daily_spend, is_active, created_at) FROM stdin;


--
-- Data for Name: clients; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.clients (id, agency_id, name, slug, status, verticals, brand_config, created_at, updated_at) FROM stdin;


--
-- Data for Name: consent_records; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.consent_records (id, agency_id, client_id, subject_hash, purpose, granted, do_not_sell, consent_text, consent_version, ip_address, user_agent, source, granted_at, withdrawn_at, expires_at) FROM stdin;


--
-- Data for Name: credentials; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.credentials (id, agency_id, client_id, platform, credential_type, status, encrypted_data, scopes, expires_at, last_refreshed_at, error_message, created_by, created_at, updated_at) FROM stdin;


--
-- Data for Name: dsar_requests; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.dsar_requests (id, agency_id, request_type, regulation, subject_email_hash, subject_name, verification_token, verified_at, status, due_date, extended_due_date, assigned_to, response_path, rejection_reason, notes, created_at, completed_at, updated_at) FROM stdin;


--
-- Data for Name: field_mapping_versions; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.field_mapping_versions (id, field_mapping_id, version, mapping_config, changed_by, change_summary, created_at) FROM stdin;


--
-- Data for Name: field_mappings; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.field_mappings (id, tenant_id, user_id, integration_id, name, mapping_config, current_version, is_active, created_at, updated_at, agency_id, platform) FROM stdin;


--
-- Data for Name: generation_results; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.generation_results (id, generation_id, platform, copy_text, image_url, status, error_message, created_at, updated_at) FROM stdin;


--
-- Data for Name: generations; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.generations (id, brand_id, user_id, tenant_id, status, prompt, error_message, created_at, updated_at, agency_id, agent_type, metadata) FROM stdin;


--
-- Data for Name: integrations; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.integrations (id, agency_id, client_id, platform, auth_type, status, credential_id, sync_schedule, config, last_sync_at, current_task_id, error_message, connected_at, created_by, created_at, updated_at) FROM stdin;


--
-- Data for Name: marketing_data_points; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.marketing_data_points (id, tenant_id, integration_id, date, dimension_key, dimensions, metrics, raw_data, synced_at) FROM stdin;


--
-- Data for Name: notifications; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.notifications (id, agency_id, user_id, title, message, category, severity, is_read, metadata, created_at) FROM stdin;


--
-- Data for Name: personas; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.personas (id, client_account_id, name, description, psychographics, channel_preferences, recommended_tone, created_at, agency_id, source, model_used, updated_at, is_active) FROM stdin;


--
-- Data for Name: report_history; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.report_history (id, agency_id, schedule_id, client_id, report_type, file_path, file_size_bytes, recipients_count, status, error_message, created_at, completed_at) FROM stdin;


--
-- Data for Name: report_schedules; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.report_schedules (id, agency_id, client_id, schedule_name, frequency, recipients_encrypted, metrics_config, brand_config_override, is_active, last_sent_at, next_run_at, created_at, updated_at) FROM stdin;


--
-- Data for Name: sync_logs; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.sync_logs (id, integration_id, agency_id, task_id, status, triggered_by, records_fetched, records_written, error_message, extra_data, started_at, finished_at) FROM stdin;


--
-- Data for Name: token_usage; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.token_usage (id, agency_id, client_id, user_id, request_id, agent_name, agent_type, model, prompt_tokens, completion_tokens, total_tokens, estimated_cost_usd, cost_usd, created_at) FROM stdin;


--
-- Name: sync_logs_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.sync_logs_id_seq', 1, false);


--
-- Name: token_usage_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.token_usage_id_seq', 1, false);


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
-- Name: attribution_reports attribution_reports_agency_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--



--
-- Name: attribution_reports attribution_reports_client_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.attribution_reports
    ADD CONSTRAINT attribution_reports_client_id_fkey FOREIGN KEY (client_id) REFERENCES public.clients(id) ON DELETE SET NULL;


--
-- Name: attribution_reports attribution_reports_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--



--
-- Name: audience_exports audience_exports_agency_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--



--
-- Name: audience_exports audience_exports_persona_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.audience_exports
    ADD CONSTRAINT audience_exports_persona_id_fkey FOREIGN KEY (persona_id) REFERENCES public.personas(id) ON DELETE CASCADE;


--
-- Name: brands brands_tenant_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--



--
-- Name: campaign_budget_configs campaign_budget_configs_agency_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--



--
-- Name: campaign_budget_configs campaign_budget_configs_client_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.campaign_budget_configs
    ADD CONSTRAINT campaign_budget_configs_client_id_fkey FOREIGN KEY (client_id) REFERENCES public.clients(id) ON DELETE SET NULL;


--
-- Name: client_accounts client_accounts_tenant_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--



--
-- Name: clients clients_agency_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--



--
-- Name: consent_records consent_records_agency_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--



--
-- Name: consent_records consent_records_client_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.consent_records
    ADD CONSTRAINT consent_records_client_id_fkey FOREIGN KEY (client_id) REFERENCES public.clients(id) ON DELETE SET NULL;


--
-- Name: credentials credentials_agency_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--



--
-- Name: credentials credentials_client_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.credentials
    ADD CONSTRAINT credentials_client_id_fkey FOREIGN KEY (client_id) REFERENCES public.clients(id) ON DELETE SET NULL;


--
-- Name: dsar_requests dsar_requests_agency_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--



--
-- Name: field_mapping_versions field_mapping_versions_field_mapping_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.field_mapping_versions
    ADD CONSTRAINT field_mapping_versions_field_mapping_id_fkey FOREIGN KEY (field_mapping_id) REFERENCES public.field_mappings(id);


--
-- Name: field_mappings field_mappings_agency_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--



--
-- Name: field_mappings field_mappings_tenant_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--



--
-- Name: generation_results generation_results_generation_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.generation_results
    ADD CONSTRAINT generation_results_generation_id_fkey FOREIGN KEY (generation_id) REFERENCES public.generations(id);


--
-- Name: generations generations_agency_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--



--
-- Name: generations generations_brand_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.generations
    ADD CONSTRAINT generations_brand_id_fkey FOREIGN KEY (brand_id) REFERENCES public.brands(id);


--
-- Name: generations generations_tenant_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--



--
-- Name: integrations integrations_agency_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--



--
-- Name: integrations integrations_client_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.integrations
    ADD CONSTRAINT integrations_client_id_fkey FOREIGN KEY (client_id) REFERENCES public.clients(id) ON DELETE CASCADE;


--
-- Name: integrations integrations_created_by_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--



--
-- Name: integrations integrations_credential_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.integrations
    ADD CONSTRAINT integrations_credential_id_fkey FOREIGN KEY (credential_id) REFERENCES public.credentials(id) ON DELETE SET NULL;


--
-- Name: marketing_data_points marketing_data_points_tenant_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--



--
-- Name: notifications notifications_agency_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--



--
-- Name: notifications notifications_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--



--
-- Name: personas personas_agency_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--



--
-- Name: personas personas_client_account_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.personas
    ADD CONSTRAINT personas_client_account_id_fkey FOREIGN KEY (client_account_id) REFERENCES public.client_accounts(id);


--
-- Name: report_history report_history_agency_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--



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
-- Name: report_schedules report_schedules_agency_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--



--
-- Name: report_schedules report_schedules_client_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.report_schedules
    ADD CONSTRAINT report_schedules_client_id_fkey FOREIGN KEY (client_id) REFERENCES public.clients(id) ON DELETE SET NULL;


--
-- Name: sync_logs sync_logs_agency_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--



--
-- Name: sync_logs sync_logs_integration_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.sync_logs
    ADD CONSTRAINT sync_logs_integration_id_fkey FOREIGN KEY (integration_id) REFERENCES public.integrations(id) ON DELETE CASCADE;


--
-- Name: token_usage token_usage_agency_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--



--
-- Name: token_usage token_usage_client_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.token_usage
    ADD CONSTRAINT token_usage_client_id_fkey FOREIGN KEY (client_id) REFERENCES public.clients(id) ON DELETE SET NULL;


--
-- Name: token_usage token_usage_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--



--
-- PostgreSQL database dump complete
--



-- ── Row-Level Security policies for per-Agency DB (client_id isolation) ─────
-- Mirrors infra/migrations/023_client_rls.sql which targets the platform DB.
-- GUCs app.client_id / app.role / app.agency_id are set by
-- backend/app/core/tenant_db.py:set_tenant_gucs() on every request.

DO $$
DECLARE
  t text;
BEGIN
  FOR t IN SELECT unnest(ARRAY[
    'attribution_reports',
    'campaign_budget_configs',
    'consent_records',
    'credentials',
    'integrations',
    'report_schedules',
    'report_history',
    'token_usage'
  ]) LOOP
    EXECUTE format('ALTER TABLE public.%I ENABLE ROW LEVEL SECURITY', t);
    EXECUTE format('ALTER TABLE public.%I FORCE ROW LEVEL SECURITY', t);
    EXECUTE format('DROP POLICY IF EXISTS client_isolation ON public.%I', t);
    EXECUTE format($p$
      CREATE POLICY client_isolation ON public.%I
        USING (
          client_id IS NULL
          OR current_setting('app.client_id', true) = ''
          OR client_id::text = current_setting('app.client_id', true)
        )
    $p$, t);
  END LOOP;
END $$;
