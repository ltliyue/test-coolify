# ReceptivIQ Platform · Database Schema (English Reference)

_Last updated: **2026-05-26**_

> Reference doc for client-facing engineering, security review, and onboarding.
> Covers two databases: **Platform metadata DB** (`receptiviq`, 32 objects) and one **Per-Agency Tenant DB** (`tenant_fy`, 21 tables). All other tenant DBs share the same shape as `tenant_fy`.
>
> Each table section starts with a **Purpose** line explaining what the table is for in plain language, followed by a column-by-column reference.

---

## 1. Architecture overview

```
┌────────────────────────────────────────────────────────────────┐
│  Platform DB (receptiviq)                                       │
│  ─────────────────────────                                      │
│  Cross-tenant metadata + RBAC + Audit + Compliance              │
│  • Agencies / Users / Tenants                                   │
│  • Roles / Permissions / Role-Permissions                       │
│  • Audit logs (immutable, 6-year retention)                     │
│  • DSAR requests / Consent records                              │
│  • Token usage analytics                                        │
└────────────────────────────────────────────────────────────────┘
                            │
                            │ each agency.db_dsn (Fernet-encrypted)
                            │ routes to a separate physical database
                            ▼
        ┌───────────────────────────────────────────┐
        │  Tenant DB (e.g. tenant_fy)                │
        │  ─────────────────────────                 │
        │  Business data for ONE agency only         │
        │  21 tables · RLS enforced by client_id    │
        │  • Clients / Brands / Personas             │
        │  • Integrations / Credentials / Sync logs  │
        │  • Generations / Attribution / Reports     │
        │  • Audience exports / Notifications        │
        │  • Consent + DSAR (per-agency copies)      │
        └───────────────────────────────────────────┘
```

### Isolation model (two-layer)

| Layer                                | Mechanism                                                       | Enforced by                                                        |
| ------------------------------------ | --------------------------------------------------------------- | ------------------------------------------------------------------ |
| **Between agencies**                 | Physical separation — each Agency has its own Postgres database | `TenantSessionRouter` reads `agencies.db_dsn`                      |
| **Within an agency, across clients** | Row-Level Security on every table containing `client_id`        | Postgres RLS policy + `set_config('app.client_id', …)` per session |

---

## 2. Platform DB (`receptiviq`) · 32 objects

### 2.1 Identity & Tenancy

#### `agencies` — top-level tenant (one row per Agency)

**Purpose**: The platform's top-level tenant unit. Every paying customer (an Agency / brand house) gets exactly one row here. Stores the Fernet-encrypted DSN that routes all of this Agency's business data to its own physical database, plus pricing plan, white-label theme, suspension state, and the monthly LLM token cap.

| Column                              | Type        | Null | Default | Notes                                                             |
| ----------------------------------- | ----------- | ---- | ------- | ----------------------------------------------------------------- |
| `id`                                | uuid        | NO   |         | PK                                                                |
| `name`                              | varchar     | NO   |         |                                                                   |
| `slug`                              | varchar     | NO   |         | URL-safe identifier                                               |
| `status`                            | enum        | NO   |         | active / suspended / archived                                     |
| `plan`                              | enum        | NO   |         | pricing tier                                                      |
| `brand_config`                      | jsonb       | YES  |         | white-label theme                                                 |
| `monthly_token_budget`              | integer     | NO   |         | LLM cost cap                                                      |
| `is_suspended`                      | boolean     | NO   | `false` |                                                                   |
| `suspended_at` / `suspended_reason` | tstz / text | YES  |         |                                                                   |
| `db_schema`                         | text        | NO   |         | legacy (pre per-DB era)                                           |
| **`db_dsn`**                        | text        | NO   |         | **Fernet-encrypted** connection string to this Agency's tenant DB |
| `db_dsn_previous`                   | text        | YES  |         | rotation backup                                                   |
| `created_at` / `updated_at`         | tstz        | NO   |         |                                                                   |

#### `users` — platform-wide user identity

**Purpose**: Single sign-on table for everyone who can log in — platform super-admins, Agency staff, and Client viewers. Holds Fernet-encrypted email/name plus a SHA-256 `email_hash` for lookup. The `role` column drives RBAC; `agency_id`/`client_id` define which tenant this user belongs to.

| Column                                        | Type    | Null | Notes                                                   |
| --------------------------------------------- | ------- | ---- | ------------------------------------------------------- |
| `id`                                          | uuid    | NO   | PK                                                      |
| `agency_id`                                   | uuid    | YES  | FK → agencies; null for platform_super_admin            |
| `client_id`                                   | uuid    | YES  | FK → clients (in tenant DB); set for client_viewer role |
| `email`                                       | varchar | NO   | Fernet-encrypted at rest (via TypeDecorator)            |
| `email_hash`                                  | varchar | NO   | SHA-256(email + salt), indexed for lookup               |
| `hashed_password`                             | varchar | YES  | bcrypt                                                  |
| `google_id`                                   | varchar | YES  | OAuth                                                   |
| `full_name`                                   | varchar | NO   | Fernet-encrypted                                        |
| `role`                                        | text    | NO   | role code (FK semantics → roles.code)                   |
| `is_active`                                   | boolean | NO   | `true`                                                  |
| `last_login_at` / `created_at` / `updated_at` | tstz    |      |                                                         |

#### `tenants` — legacy tenant table (pre-Agency era; retained for migration)

**Purpose**: Carries the white-label settings (logo, primary color, custom domain, theme config) from the original single-tenant design. Kept for backward-compat joins; new white-label config now lives in `agencies.brand_config`. Will be archived in a future cleanup PR.

| Column                                         | Type           | Notes       |
| ---------------------------------------------- | -------------- | ----------- |
| `id` / `name` / `slug`                         | uuid / varchar |             |
| `logo_url` / `primary_color` / `custom_domain` | varchar        | white-label |
| `theme_config`                                 | json           |             |
| `created_at`                                   | tstz           |             |

#### `client_accounts` — sub-tenant inside an agency (one row per agency client account)

**Purpose**: Older sub-tenant table from when "client" was modeled at the platform layer. Carries finer-grained ad-account spend tracking (`daily_spend`, `vertical`). Today the canonical client-of-Agency record lives in the tenant DB's `clients` table; this row exists for legacy reads.

| Column              | Type    | Notes |
| ------------------- | ------- | ----- |
| `id` / `tenant_id`  | uuid    |       |
| `name` / `vertical` | varchar |       |
| `daily_spend`       | numeric |       |
| `is_active`         | boolean |       |

#### `user_invitations` — pending invites with PII protection

**Purpose**: Holds outstanding "join my Agency / Client workspace" invites. Email is split into a SHA-256 `email_hash` (for "did you already invite me?" lookup) plus a Fernet `email_encrypted` blob. The one-time `token_hash` is matched on the invitee's signup link, and `expires_at` enforces a short lifetime.

| Column                                      | Type | Notes                          |
| ------------------------------------------- | ---- | ------------------------------ |
| `id`                                        | uuid | PK                             |
| `agency_id` / `client_id`                   | uuid | scope of invite                |
| `email_hash`                                | text | SHA-256 lookup key             |
| `email_encrypted`                           | text | Fernet ciphertext              |
| `role`                                      | text | granted role                   |
| `token_hash`                                | text | one-time invite token (hashed) |
| `invited_by`                                | uuid | FK → users                     |
| `expires_at` / `accepted_at` / `revoked_at` | tstz | lifecycle                      |

---

### 2.2 RBAC (configurable permission system)

#### `roles` — role catalog (system + custom)

**Purpose**: Master list of every role that can be assigned to a user. The 5 built-in roles (`platform_super_admin`, `platform_admin`, `agency_admin`, `agency_ops`, `client_viewer`) live alongside any **custom roles** created by platform admins (global) or Agency admins (scoped to that Agency only). `rank` enforces hierarchy when one role tries to manage another.

| Column        | Type    | Notes                                                     |
| ------------- | ------- | --------------------------------------------------------- |
| `code`        | text    | PK — short identifier (e.g. `agency_admin`, `custom_ops`) |
| `label`       | text    | human-readable name                                       |
| `tier`        | text    | `platform` / `agency` / `client`                          |
| `agency_id`   | uuid    | non-null for agency-custom roles                          |
| `is_system`   | boolean | `true` for the 5 built-ins (cannot be deleted)            |
| `description` | text    |                                                           |
| `rank`        | integer | hierarchy weight (higher = more privileged)               |
| `created_by`  | uuid    | who created it                                            |
| `created_at`  | tstz    |                                                           |

#### `permissions` — permission code registry (~60 codes)

**Purpose**: The fixed catalog of every action that can be permission-controlled in the app (e.g. `personas.write`, `reports.export`, `platform.agency.suspend`). Routes in FastAPI use `require_permission(code)`; the matrix UI in Settings reads this list to render checkboxes. `category` groups codes for display.

| Column                  | Type | Notes                                                      |
| ----------------------- | ---- | ---------------------------------------------------------- |
| `code`                  | text | PK — e.g. `personas.write`, `platform.agency.create`       |
| `label` / `description` | text |                                                            |
| `category`              | text | UI grouping (Personas / Reports / Settings / Platform / …) |

#### `role_permissions` — default mapping (role × permission → granted)

**Purpose**: The platform-wide **default** answer to "does role X have permission Y?". Seeded at install time to reproduce the original hard-coded behavior; tunable globally by `platform_super_admin` via the Permissions matrix. Any Agency can override individual cells via `agency_role_permissions`.

| Column            | Type                    | Notes                 |
| ----------------- | ----------------------- | --------------------- |
| `role`            | text                    | FK → roles.code       |
| `permission_code` | text                    | FK → permissions.code |
| `granted`         | boolean                 | `false` by default    |
| PK                | (role, permission_code) |                       |

#### `agency_role_permissions` — per-Agency override on top of defaults

**Purpose**: Lets each Agency admin (via Settings → Permissions) flip individual permission cells **without affecting other Agencies**. The `PermissionResolver` checks this table first; if no row exists for the (agency, role, code) combo, it falls back to `role_permissions`. 5-minute TTL cache + write-through invalidation.

| Column            | Type                               | Notes                                                        |
| ----------------- | ---------------------------------- | ------------------------------------------------------------ |
| `agency_id`       | uuid                               |                                                              |
| `role`            | text                               |                                                              |
| `permission_code` | text                               |                                                              |
| `granted`         | boolean                            | NULL semantics: row absent ⇒ fall back to `role_permissions` |
| PK                | (agency_id, role, permission_code) |                                                              |

> **Resolver order**: `agency_role_permissions[agency, role, code]` → if missing, `role_permissions[role, code]`.

---

### 2.3 Audit & Compliance

#### `audit_logs` — immutable, INSERT-only, 6-year retention

**Purpose**: The single source of truth for "who did what, when, from where, and with what outcome." Every state-changing API call, every RBAC denial (shadow + enforce), every DSN rotation, every DSAR step writes one row. UPDATE/DELETE are blocked by triggers — the table is **append-only forever**, satisfying HIPAA 6-year retention and GDPR Article 30.

| Column                                           | Type         | Notes                                                    |
| ------------------------------------------------ | ------------ | -------------------------------------------------------- |
| `id`                                             | bigint       | PK (sequence)                                            |
| `agency_id` / `client_id` / `user_id`            | uuid         | actor context                                            |
| `action`                                         | varchar      | e.g. `persona.create`, `rbac.permission.denied_enforce`  |
| `resource_type` / `resource_id`                  | varchar      | what was acted on                                        |
| `ip_address`                                     | varchar      |                                                          |
| `user_agent` / `request_path` / `request_method` | text/varchar |                                                          |
| `status_code`                                    | integer      | HTTP outcome                                             |
| `success`                                        | boolean      |                                                          |
| `error_message`                                  | text         |                                                          |
| `contains_phi`                                   | boolean      | HIPAA flag                                               |
| `data_level`                                     | varchar      | L0 / L1 / L2 / L3                                        |
| `extra_data`                                     | jsonb        | structured payload (before/after, dsn_fingerprint, etc.) |
| `created_at`                                     | tstz         |                                                          |

> BEFORE UPDATE / BEFORE DELETE triggers raise exceptions — rows cannot be modified or deleted.

#### `dsar_requests` — Data Subject Access Requests (GDPR / CCPA / HIPAA)

**Purpose**: One row per data-subject request (access / delete / export / rectify / restrict). Tracks identity verification, SLA timer (30/45/30 days by regulation), the case owner, and the eventual response artifact's S3/MinIO path. The DSAR worker fans out across the platform DB + every relevant tenant DB to fulfill it, then closes the row.

| Column                                       | Type           | Notes                                                   |
| -------------------------------------------- | -------------- | ------------------------------------------------------- |
| `id` / `agency_id`                           | uuid           |                                                         |
| `request_type`                               | enum           | access / delete / export / rectify / restrict           |
| `regulation`                                 | enum           | gdpr / ccpa / hipaa                                     |
| `subject_email_hash`                         | varchar        | SHA-256 lookup                                          |
| `subject_name`                               | varchar        | Fernet-encrypted (optional)                             |
| `verification_token` / `verified_at`         | varchar / tstz | identity proof                                          |
| `status`                                     | enum           | pending → verified → in_progress → completed / rejected |
| `due_date` / `extended_due_date`             | tstz           | SLA: GDPR 30d / CCPA 45d / HIPAA 30d                    |
| `assigned_to`                                | uuid           | FK → users                                              |
| `response_path`                              | varchar        | S3/MinIO path to export bundle                          |
| `rejection_reason` / `notes`                 | text           |                                                         |
| `created_at` / `completed_at` / `updated_at` | tstz           |                                                         |

#### `consent_records` — granular consent ledger

**Purpose**: Per-subject, per-purpose record of "did this person say yes / no to being processed for marketing / analytics / personalization?". Captures the exact consent text shown, version, source page, IP, and timestamps for grant / withdraw / expire. Required evidence for GDPR Article 7 and CCPA "Do Not Sell".

| Column                                       | Type           | Notes                                       |
| -------------------------------------------- | -------------- | ------------------------------------------- |
| `id` / `agency_id` / `client_id`             | uuid           |                                             |
| `subject_hash`                               | varchar        | SHA-256(email) lookup                       |
| `purpose`                                    | enum           | marketing / analytics / personalization / … |
| `granted`                                    | boolean        |                                             |
| `do_not_sell`                                | boolean        | CCPA opt-out                                |
| `consent_text` / `consent_version`           | text / varchar | snapshot of what was shown                  |
| `ip_address`                                 | inet           |                                             |
| `user_agent` / `source`                      | text / varchar |                                             |
| `granted_at` / `withdrawn_at` / `expires_at` | tstz           |                                             |

---

### 2.4 Observability

#### `token_usage` — per-call LLM cost tracking

**Purpose**: One row per LLM call made by any AI Agent (Persona / Creative / Attribution). Records prompt + completion token counts, model, estimated and actual USD cost, plus the requesting `request_id` for trace correlation. Drives the monthly budget enforcement on `agencies.monthly_token_budget` and feeds the v_token_usage_monthly view.

| Column                                                 | Type    | Notes                                     |
| ------------------------------------------------------ | ------- | ----------------------------------------- |
| `id`                                                   | bigint  | PK                                        |
| `agency_id` / `client_id` / `user_id`                  | uuid    |                                           |
| `request_id`                                           | text    | trace correlation                         |
| `agent_name` / `agent_type`                            | text    | e.g. `persona`, `creative`, `attribution` |
| `model`                                                | text    | model identifier (e.g. `gpt-4o`)          |
| `prompt_tokens` / `completion_tokens` / `total_tokens` | integer |                                           |
| `estimated_cost_usd` / `cost_usd`                      | numeric |                                           |
| `created_at`                                           | tstz    |                                           |

#### `v_token_usage_monthly` — pre-aggregated view (agency × agent × model × month)

**Purpose**: Read-only Postgres view rolling up `token_usage` into one row per (agency, client, agent, model, month). Powers the cost dashboard, billing reconciliation, and budget-burn alerts without scanning the full raw table on every page load.

| Column                                                             | Type    | Notes  |
| ------------------------------------------------------------------ | ------- | ------ |
| `agency_id` / `client_id`                                          | uuid    |        |
| `agent_name` / `model`                                             | text    |        |
| `month`                                                            | tstz    | bucket |
| `total_prompt_tokens` / `total_completion_tokens` / `total_tokens` | bigint  |        |
| `total_cost_usd`                                                   | numeric |        |
| `request_count`                                                    | bigint  |        |

---

### 2.5 Mirrored business tables (platform super-admin view)

The platform DB **also contains the same 18 business tables** as a tenant DB (`personas`, `brands`, `integrations`, `credentials`, `sync_logs`, `marketing_data_points`, `generations`, `generation_results`, `attribution_reports`, `audience_exports`, `report_schedules`, `report_history`, `field_mappings`, `field_mapping_versions`, `campaign_budget_configs`, `notifications`, `consent_records`, `dsar_requests`).

**Why duplicated**: legacy schema-per-Agency residue + super-admin convenience views. After the per-Agency-DB migration, **all writes target tenant DBs**; platform-DB copies stay for backward read-compat only and will be archived in a future cleanup PR.

#### `alembic_version` — migration tracking

**Purpose**: One-row, one-column system table where Alembic stamps the latest migration revision applied. Used by `alembic upgrade head` to know whether the DB is current and which migrations remain.

Single-column `version_num` (varchar) holding current Alembic head.

---

## 3. Tenant DB (`tenant_fy` — representative for any Agency) · 21 tables

> Same DDL applied to every per-Agency database via `provision_tenant_database()`.
> Every table carrying `client_id` is RLS-enabled and respects `current_setting('app.client_id')`.

### 3.1 Tenant identity (mirrored from platform for joins)

#### `clients` — sub-tenants of this Agency

**Purpose**: The brands / advertisers that this Agency manages. Every business row in the tenant DB (personas, integrations, campaigns, …) ultimately belongs to one client, and RLS uses `client_id` to keep client_viewer users locked to their own data.

| Column                      | Type    | Notes                           |
| --------------------------- | ------- | ------------------------------- |
| `id`                        | uuid    | PK                              |
| `agency_id`                 | uuid    | always equals the owning Agency |
| `name` / `slug`             | varchar |                                 |
| `status`                    | enum    | active / paused / archived      |
| `verticals`                 | text[]  | industry tags                   |
| `brand_config`              | jsonb   | white-label override            |
| `created_at` / `updated_at` | tstz    |                                 |

#### `client_accounts` — finer-grained ad accounts within a client

**Purpose**: When one client runs multiple ad accounts (different verticals or business units), each gets a row here with its own daily spend tracker. Optional — small clients have just one implicit account.

| Column              | Type    | Notes |
| ------------------- | ------- | ----- |
| `id`                | uuid    | PK    |
| `tenant_id`         | uuid    |       |
| `name` / `vertical` | varchar |       |
| `daily_spend`       | numeric |       |
| `is_active`         | boolean |       |

#### `brands` — brand profiles owned by a client

**Purpose**: The brand identity passed to AI Agents: logo, slogan, primary color, product description, target audience, and tone-of-voice. Persona Agent and Creative Agent both read from this row to make their outputs feel "on-brand."

| Column                                        | Type    | Notes               |
| --------------------------------------------- | ------- | ------------------- |
| `id` / `user_id` / `tenant_id`                | uuid    |                     |
| `name`                                        | varchar |                     |
| `logo_url` / `slogan` / `primary_color`       | varchar |                     |
| `product_description`                         | text    |                     |
| `industry` / `target_audience` / `brand_tone` | varchar | feeds Persona Agent |
| `is_active`                                   | boolean |                     |
| `created_at` / `updated_at`                   | tstz    |                     |

---

### 3.2 Integrations & data sources

#### `credentials` — encrypted OAuth tokens / API keys

**Purpose**: The secret-storage table for every external integration. OAuth refresh tokens, API keys, mTLS bundles — all sit in `encrypted_data` as a Fernet blob. Decryption happens only inside ETL/adapter code, never in the API layer or logs.

| Column                             | Type   | Notes                                     |
| ---------------------------------- | ------ | ----------------------------------------- |
| `id` / `agency_id` / `client_id`   | uuid   |                                           |
| `platform`                         | text   | e.g. `hubspot`, `ga4`, `meta`, `experian` |
| `credential_type`                  | enum   | oauth / api_key / mtls / private_app      |
| `status`                           | enum   | active / expired / revoked / error        |
| `encrypted_data`                   | text   | **Fernet-encrypted** token blob           |
| `scopes`                           | text[] | granted OAuth scopes                      |
| `expires_at` / `last_refreshed_at` | tstz   | refresh lifecycle                         |
| `error_message`                    | text   | last failure                              |
| `created_by`                       | uuid   | FK → users                                |

#### `integrations` — per-platform integration instance

**Purpose**: The "Connect HubSpot / GA4 / Meta / Experian" button writes one row here. Tracks which platform is wired up, which credential row to use, the sync schedule, current sync task, last error, and what config the adapter expects. The Integrations page in the UI is a CRUD over this table.

| Column                    | Type  | Notes                                                                                                                                          |
| ------------------------- | ----- | ---------------------------------------------------------------------------------------------------------------------------------------------- |
| `id`                      | uuid  | PK                                                                                                                                             |
| `agency_id` / `client_id` | uuid  |                                                                                                                                                |
| `platform`                | enum  | hubspot / ga4 / meta / dv360 / stackadapt / ttd / tiktok / liveramp / leadrx / quorum / experian / transunion / nielsen / placer_iq / tresorit |
| `auth_type`               | enum  | mirror of credentials.credential_type                                                                                                          |
| `status`                  | enum  | connected / disconnected / syncing / error                                                                                                     |
| `credential_id`           | uuid  | FK → credentials                                                                                                                               |
| `sync_schedule`           | jsonb | cron + cursor config                                                                                                                           |
| `config`                  | jsonb | platform-specific options                                                                                                                      |
| `last_sync_at`            | tstz  |                                                                                                                                                |
| `current_task_id`         | text  | Celery task id when syncing                                                                                                                    |
| `error_message`           | text  | last failure                                                                                                                                   |
| `connected_at`            | tstz  | first successful connection                                                                                                                    |

#### `sync_logs` — every ETL run

**Purpose**: Append-only log of every ETL pull (whether scheduled, manually triggered, or webhook-fired). Captures rows fetched / written, errors, and Celery task IDs so support engineers can replay failures and AMs can confirm "yes, last night's HubSpot sync did run at 02:14 UTC."

| Column                                | Type    | Notes                                |
| ------------------------------------- | ------- | ------------------------------------ |
| `id`                                  | bigint  | PK                                   |
| `integration_id` / `agency_id`        | uuid    |                                      |
| `task_id`                             | text    | Celery                               |
| `status`                              | enum    | pending / running / success / failed |
| `triggered_by`                        | text    | manual / cron / webhook              |
| `records_fetched` / `records_written` | integer |                                      |
| `error_message`                       | text    |                                      |
| `extra_data`                          | jsonb   | platform-specific diagnostic payload |
| `started_at` / `finished_at`          | tstz    |                                      |

#### `marketing_data_points` — normalized warehouse rows

**Purpose**: The Processed-Lake equivalent inside Postgres for normalized campaign metrics — one row per (integration, date, dimension_key) holding impressions / clicks / spend / conversions in `metrics` JSON. Powers dashboards and feeds the Attribution Agent. Legacy `raw_data` column is being phased out per data-minimization.

| Column                                | Type    | Notes                                                              |
| ------------------------------------- | ------- | ------------------------------------------------------------------ |
| `id` / `tenant_id` / `integration_id` | uuid    |                                                                    |
| `date`                                | date    | natural partition key                                              |
| `dimension_key`                       | varchar | dedup key                                                          |
| `dimensions`                          | json    | grouping fields (campaign / ad / source)                           |
| `metrics`                             | json    | impressions / clicks / spend / conversions                         |
| `raw_data`                            | json    | **NB**: legacy — new adapters must omit this per data-minimization |
| `synced_at`                           | tstz    |                                                                    |

#### `field_mappings` & `field_mapping_versions` — column-mapping config history

**Purpose**: When a client uploads a CSV or wires a new integration, the user maps source columns (e.g. "Email Address" → `email`, "Campaign Spend" → `spend_usd`) in the Field Mapping wizard. `field_mappings` stores the current active mapping; `field_mapping_versions` keeps every historical version so we can roll back or audit a re-import.

| `field_mappings`          | Type    | Notes         |
| ------------------------- | ------- | ------------- |
| `id`                      | uuid    | PK            |
| `tenant_id` / `agency_id` | uuid    |               |
| `user_id`                 | uuid    | owner         |
| `integration_id`          | uuid    | optional FK   |
| `name` / `platform`       | varchar |               |
| `mapping_config`          | json    | active config |
| `current_version`         | integer |               |
| `is_active`               | boolean |               |

| `field_mapping_versions`  | Type    | Notes                     |
| ------------------------- | ------- | ------------------------- |
| `id` / `field_mapping_id` | uuid    |                           |
| `version`                 | integer | monotonically increasing  |
| `mapping_config`          | json    | full snapshot per version |
| `changed_by`              | uuid    |                           |
| `change_summary`          | varchar |                           |
| `created_at`              | tstz    |                           |

---

### 3.3 AI agent outputs

#### `personas` — ICP definitions

**Purpose**: The Ideal Customer Profile output by the Persona Agent (or manually defined by an AM). Holds demographics, psychographics, preferred channels, and recommended tone-of-voice. Downstream the Creative Agent uses persona to flavor copy, and Audience Build uses it as the SQL predicate for picking ad-targets.

| Column                            | Type    | Notes                                  |
| --------------------------------- | ------- | -------------------------------------- |
| `id`                              | uuid    | PK                                     |
| `agency_id` / `client_account_id` | uuid    |                                        |
| `name`                            | varchar |                                        |
| `description`                     | text    |                                        |
| `psychographics`                  | json    | attitudes / values                     |
| `channel_preferences`             | json    | preferred touchpoints                  |
| `recommended_tone`                | varchar | feeds Creative Agent                   |
| `source`                          | varchar | `manual` / `ai_generated` / `imported` |
| `model_used`                      | varchar | LLM if AI-generated                    |
| `is_active`                       | boolean |                                        |
| `created_at` / `updated_at`       | tstz    |                                        |

#### `generations` — Creative Agent / Persona Agent job header

**Purpose**: One row per AI-generation job (regardless of which Agent). Carries the prompt, status, requesting user, target brand, and metadata. Long-running jobs (image generation, multi-platform copy variants) update their status here; the UI polls this row for progress.

| Column                                 | Type    | Notes                                                       |
| -------------------------------------- | ------- | ----------------------------------------------------------- |
| `id`                                   | uuid    | PK                                                          |
| `agency_id` / `brand_id` / `tenant_id` | uuid    |                                                             |
| `user_id`                              | uuid    | requester                                                   |
| `agent_type`                           | varchar | `creative` / `persona` / `attribution` (default `creative`) |
| `status`                               | enum    | pending / running / succeeded / failed                      |
| `prompt`                               | text    | input prompt                                                |
| `metadata`                             | jsonb   | model params, seeds, etc.                                   |
| `error_message`                        | text    |                                                             |
| `created_at` / `updated_at`            | tstz    |                                                             |

#### `generation_results` — per-platform output variants

**Purpose**: Each parent `generations` row fans out into N child results, one per ad platform (Meta 1080x1080, DV360 728x90, TikTok 9:16, …). Holds the actual copy text + rendered creative URL that gets pushed downstream to the activation step.

| Column                      | Type    | Notes                                             |
| --------------------------- | ------- | ------------------------------------------------- |
| `id` / `generation_id`      | uuid    |                                                   |
| `platform`                  | enum    | meta / dv360 / tiktok / stackadapt / linkedin / … |
| `copy_text`                 | text    | generated ad copy                                 |
| `image_url`                 | varchar | rendered creative                                 |
| `status`                    | enum    | success / failed                                  |
| `error_message`             | text    |                                                   |
| `created_at` / `updated_at` | tstz    |                                                   |

#### `attribution_reports` — Attribution Agent outputs

**Purpose**: Saved attribution analyses (multi-touch, MMM, last-click). `channels` lists what was analyzed, `model_config` captures the hyperparameters, `results` holds the JSON weights / journey counts, and `insights` is the natural-language summary the AM shares with the client. The Portal renders this row's content as a dashboard.

| Column                                       | Type    | Notes                                          |
| -------------------------------------------- | ------- | ---------------------------------------------- |
| `id` / `agency_id` / `client_id` / `user_id` | uuid    |                                                |
| `title`                                      | varchar |                                                |
| `report_type`                                | varchar | `multi_touch` / `mmm` / `last_click`           |
| `date_range_start` / `date_range_end`        | date    |                                                |
| `channels`                                   | jsonb   | list of channels analyzed                      |
| `model_config`                               | jsonb   | model hyperparameters                          |
| `results`                                    | jsonb   | attribution weights, journey counts            |
| `insights`                                   | text    | natural-language summary                       |
| `model_used`                                 | varchar |                                                |
| `status`                                     | varchar | `pending` / `running` / `completed` / `failed` |

---

### 3.4 Activation, campaigns & reporting

#### `audience_exports` — pushes to DSPs

**Purpose**: Tracks each "send this persona's audience to a DSP" job. Includes the target platform (Meta Custom Audience / DV360 Customer Match / TikTok), the DSP-side audience ID after success, the targeting spec applied, retry count, and any error. This is where the platform records what it pushed outward to the ad ecosystem.

| Column                            | Type    | Notes                                                         |
| --------------------------------- | ------- | ------------------------------------------------------------- |
| `id` / `agency_id` / `persona_id` | uuid    |                                                               |
| `platform`                        | varchar | meta_custom_audience / dv360_customer_match / tiktok_audience |
| `external_audience_id`            | varchar | DSP-side ID                                                   |
| `targeting_spec`                  | jsonb   | filter + suppression details                                  |
| `status`                          | varchar | pending / running / success / failed                          |
| `error_message`                   | text    |                                                               |
| `retry_count`                     | integer |                                                               |
| `created_at` / `completed_at`     | tstz    |                                                               |

#### `campaign_budget_configs` — daily/total budget + pacing alerts

**Purpose**: Per-campaign budget config — daily cap, total cap, and the over/under-pacing threshold that fires alerts (default 15%). The pacing cron job compares real spend (from `marketing_data_points`) against these and writes a `notifications` row when a campaign drifts.

| Column                           | Type    | Notes                           |
| -------------------------------- | ------- | ------------------------------- |
| `id` / `agency_id` / `client_id` | uuid    |                                 |
| `platform`                       | varchar |                                 |
| `external_campaign_id`           | varchar |                                 |
| `campaign_name`                  | varchar |                                 |
| `daily_budget` / `total_budget`  | numeric |                                 |
| `pacing_alert_threshold`         | double  | default `0.15` (15% over/under) |
| `alert_enabled`                  | boolean | default `true`                  |
| `created_at` / `updated_at`      | tstz    |                                 |

#### `report_schedules` — scheduled PDF/email reports

**Purpose**: Defines a recurring PDF report — its cadence (daily/weekly/monthly), which KPIs to include, recipient list (Fernet-encrypted), per-report white-label overrides, and when it should next run. The scheduler reads `next_run_at` and dispatches the rendering job.

| Column                           | Type    | Notes                       |
| -------------------------------- | ------- | --------------------------- |
| `id` / `agency_id` / `client_id` | uuid    |                             |
| `schedule_name`                  | varchar |                             |
| `frequency`                      | varchar | daily / weekly / monthly    |
| `recipients_encrypted`           | text    | Fernet-encrypted email list |
| `metrics_config`                 | jsonb   | which KPIs to include       |
| `brand_config_override`          | jsonb   | per-report white-label      |
| `is_active`                      | boolean | default `true`              |
| `last_sent_at` / `next_run_at`   | tstz    |                             |

#### `report_history` — every generated report

**Purpose**: One row per rendered/sent report (whether scheduled or ad-hoc). Holds the S3/MinIO file path, file size, recipient count, status, and any send-failure detail. Retained even after DSAR deletes so we can prove "what we showed the client on X date" — these reports are immutable client deliverables.

| Column                                    | Type    | Notes                          |
| ----------------------------------------- | ------- | ------------------------------ |
| `id`                                      | uuid    | PK                             |
| `agency_id` / `client_id` / `schedule_id` | uuid    |                                |
| `report_type`                             | varchar | default `campaign_performance` |
| `file_path`                               | varchar | S3/MinIO key                   |
| `file_size_bytes`                         | integer |                                |
| `recipients_count`                        | integer |                                |
| `status`                                  | varchar | pending / sent / failed        |
| `error_message`                           | text    |                                |
| `created_at` / `completed_at`             | tstz    |                                |

---

### 3.5 Compliance (per-Agency copies)

#### `consent_records` — same shape as platform DB; rows scoped to this Agency

**Purpose**: Per-Agency copy of the consent ledger. When data enters this Agency's tenant DB (e.g. a HubSpot lead with `consent_marketing=true`), a row is written here so the consent travels with the data and can be re-checked at activation time.

#### `dsar_requests` — same shape as platform DB; rows scoped to this Agency

**Purpose**: Per-Agency copy of DSAR cases. The DSAR worker walks **every tenant DB plus the platform DB** when fulfilling a request, so each Agency keeps its own slice of the case state. Aggregated back to the platform DB request row when complete.

> DSAR worker fans out across **platform DB + every relevant tenant DB** (via `TenantSessionRouter`), then aggregates results into the platform-DB request row.

---

### 3.6 Observability (per-Agency copies)

#### `notifications` — in-app notification feed

**Purpose**: The bell-icon dropdown in the UI reads from here. Backend services push rows for sync failures, budget alerts, DSAR deadlines approaching, new attribution reports, integration disconnects, and more. `is_read` drives the unread count; `severity` color-codes the chip.

| Column                  | Type    | Notes                                                                |
| ----------------------- | ------- | -------------------------------------------------------------------- |
| `id`                    | uuid    | PK                                                                   |
| `agency_id` / `user_id` | uuid    |                                                                      |
| `title`                 | varchar |                                                                      |
| `message`               | text    |                                                                      |
| `category`              | varchar | `system` / `compliance` / `integration` / `agent` (default `system`) |
| `severity`              | varchar | `info` / `warning` / `critical` (default `info`)                     |
| `is_read`               | boolean | default `false`                                                      |
| `metadata`              | jsonb   |                                                                      |
| `created_at`            | tstz    |                                                                      |

#### `token_usage` — same shape as platform DB; per-Agency LLM cost ledger

**Purpose**: Per-Agency mirror of LLM call accounting. AI Agents write here first (closest to the data they operated on); a nightly aggregator can roll the rows up to the platform DB if cross-Agency billing reports are needed.

---

## 4. Key cross-table relationships

```
agencies(id) ──────┐
                   │
                   ├───► users.agency_id
                   ├───► user_invitations.agency_id
                   ├───► roles.agency_id              (custom roles only)
                   ├───► agency_role_permissions.agency_id
                   ├───► audit_logs.agency_id
                   ├───► token_usage.agency_id
                   ├───► dsar_requests.agency_id
                   ├───► consent_records.agency_id
                   └───► [tenant DB] every business row.agency_id

roles(code) ───────┐
                   ├───► users.role
                   ├───► role_permissions.role
                   └───► agency_role_permissions.role

permissions(code) ─┬───► role_permissions.permission_code
                   └───► agency_role_permissions.permission_code

[tenant DB]
clients(id) ───────┐
                   ├───► personas.client_account_id (FK)
                   ├───► integrations.client_id
                   ├───► credentials.client_id
                   ├───► campaign_budget_configs.client_id
                   ├───► audience_exports.persona_id → personas → client
                   ├───► report_schedules.client_id
                   └───► consent_records.client_id

integrations(id) ──┬───► sync_logs.integration_id
                   ├───► marketing_data_points.integration_id
                   └───► field_mappings.integration_id

generations(id) ───► generation_results.generation_id
report_schedules(id) ───► report_history.schedule_id
```

---

## 5. Conventions & encryption summary

| Field pattern                                         | Treatment                                                                                    |
| ----------------------------------------------------- | -------------------------------------------------------------------------------------------- |
| Any column named `*_encrypted` or storing tokens      | Fernet (symmetric, AES-128 CBC + HMAC) — per-Agency key in KMS                               |
| `email` on `users` and `user_invitations`             | Fernet-encrypted + `email_hash` (SHA-256 + salt) for lookup                                  |
| `subject_hash` on `consent_records` / `dsar_requests` | SHA-256(email + agency_salt) — never reversible                                              |
| `db_dsn` on `agencies`                                | Fernet — never appears in logs / CLI / Sentry                                                |
| `audit_logs.extra_data`                               | Structured JSON — must NOT contain raw PII                                                   |
| Any `*_at` column                                     | Postgres `timestamp with time zone` (UTC stored, tz-converted at read)                       |
| UUID primary keys                                     | `gen_random_uuid()` (pgcrypto) for new tables; UUID v7 reserved for future record-id columns |

---

## 6. Regenerate command

```bash
cd docs/schema-snapshot

# Platform DB (structure only)
PGPASSWORD=receptiviq pg_dump -h localhost -U receptiviq -d receptiviq \
  --schema-only --no-owner --no-privileges > platform_receptiviq.sql

# Representative tenant DB
PGPASSWORD=receptiviq pg_dump -h localhost -U receptiviq -d tenant_fy \
  --schema-only --no-owner --no-privileges > tenant_fy.sql
```

Then regenerate this doc by re-running the column dump queries against
`information_schema.columns` and updating section 2 / 3 as needed.

---

## 7. Related references

- Chinese version of this snapshot index: [`README.md`](./README.md)
- End-to-end data flow narrative: [`../END-TO-END-DATA-FLOW.md`](../END-TO-END-DATA-FLOW.md)
- Multi-tenant architecture: [`../MULTI-TENANT-DB.md`](../MULTI-TENANT-DB.md)
- Compliance program: [`../../features/compliance/architecture.md`](../../features/compliance/architecture.md)
- Migration source-of-truth: [`../../infra/migrations/`](../../infra/migrations/)
