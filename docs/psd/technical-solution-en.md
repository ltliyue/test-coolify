# Technical Solution Description

> Status: PSD formal deliverable
---

## 1. Executive Summary

ReceptivIQ is an **AI-native marketing operating platform** for marketing agencies and their brand customers. The goal is not a single reporting tool, but to unify **Market Research · Creative Generation · Media Buying · Attribution · Client Portal** on top of one compliance-bound data and intelligence layer.

**Core architectural principles:**

1. **Unify data first, then expose to AI** — all external data is normalized, deduplicated, validated and enriched before entering the queryable warehouse
2. **PII vs Non-PII separated at ingest** — sensitive personal info never mixes into the general analytics warehouse
3. **AI Brain as the unified intelligence layer** — all Persona / Creative / Attribution / Media agents access data, route models, run tools and emit audit through one Core AI Brain
4. **Multi-tenant isolation as a foundation** — tenant isolation, RBAC, audit, residency and key strategy must be locked before Sprint 1

**Core elements:**

- **3-Lake Medallion Data Strategy**: 🟫 Landing Lake (Bronze) + 🔴 Raw PII-Segregated Lake + 🟢 Processed Lake (physical isolation · 3 independent Neon projects · independent KMS · mTLS network) — raw data lands in Landing first, then derives PII / non-PII into the other two
- **Multi-tenant warehouse** (**Neon Postgres** — product-locked): per-Agency Neon project + dedicated KMS + dedicated compute endpoint; 3 granularity tiers (Standard / Enterprise / Regulated); Neon Branching (git-style zero-copy clone); per-tenant residency. **Client-level isolation is RLS-only** (preserves cross-Agency benchmarking)
- **8-step ELT pipeline**: Extract → Classify → Load → Normalize → Deduplicate → Validate → Enrich → Index (+ Audit cross-cutting)
- **Orchestration engine** (**primary scheduler: choose one**): 🟪 **Dagster OSS** (recommended · native lineage + dagster-dbt) or 🟦 **Apache Airflow** (widespread · 1000+ Provider); 🟧 **AWS Step Functions** for AI write-back approval + DSAR long flows
- **Core AI Brain**: 6 components (Context Builder · LLM Router · Agent Orchestrator · Tool Executor · Memory & Retrieval · Audit & Cost) + 4 Pillar Agents (Persona / Creative / Attribution / Media)
- **Priority 1 Integrations**: 14 external sources + Tresorit for compliant transfer
- **Compliance posture**: GDPR · CCPA · HIPAA · SOC 2 + per-tenant data residency + PII Access Service (controlled plaintext PII egress)
- **SSO** (post-MVP): Google Workspace + Office 365 / Entra ID
- **MVP Functional Pillars**: Market Research · Creative Engine · Media Buying · Attribution · Client Portal
- **Autonomy Boundary**: MVP enforces **human-in-the-loop** (budget changes, ad pauses, platform write-back require human approval)

> 📊 **End-to-end flow (5 stages, mapped to Network Diagram flow strips)**:
> ① Extract (TLS + OAuth) → ② Classify · Transform · Load (raw_pii → Raw Lake / staging+canonical → Processed Lake) → ③ PII-safe Context Retrieval (AI reads Processed Lake only) → ④ Agent Orchestrate (LLM Router + token budget + Langfuse) → ⑤ Deliver (4 agents' output → Agency / Client portals)

---

## 2. Architectural Principles

### 2.1 Privacy by Design

Compliance is embedded in the architecture, not bolted on. PII / PHI must be anonymized or isolated before entering the warehouse. Audit logs are always-on and INSERT-only. Encryption keys are physically separated from data. The AI **does not consume raw PII by default** — context must pass through the Context Builder which filters / tokenizes sensitive fields.

### 2.2 3-Lake (Medallion) Data Strategy

The platform uses the industry-standard **3-tier Medallion architecture**:

- 🟫 **Landing Lake (Bronze)**: the **fully preserved** landing zone for all raw data (PII columns encrypted, non-PII plaintext) — source of truth for reprocessing / DSAR / legal discovery; business/AI are forbidden from reading
- 🔴 **Raw PII-Segregated Lake (Silver-PII)**: PII dim tables derived from Landing (subject dim + per-source PII column extracts) — the sole plaintext PII source for the PII Access Service
- 🟢 **Processed Lake (Silver+Gold)**: non-PII business path derived from Landing (raw → staging → canonical → marts → ai_context) — carries **no plaintext PII**, consumed by business / AI / reporting

**Trust boundaries**: Landing and Raw PII sit within the same PII trust boundary (equal encryption, equal access controls); Processed Lake is an independent business trust boundary (no PII), separated by the **PII Segregation Boundary**. Cross-Lake linkage uses **`pii_token = SHA-256(email_hash + agency_salt)`** irreversible hash — plaintext PII never leaves the PII zone.

### 2.3 Multi-Tenant Isolation (Physical Isolation + Role Hierarchy)

**Three role levels + two isolation layers:**

| Level       | Role                                | Data Visibility                                                            | Isolation                                                               |
| ----------- | ----------------------------------- | -------------------------------------------------------------------------- | ----------------------------------------------------------------------- |
| L1 Platform | **Platform Super Admin** (internal) | Cross-Agency **aggregates / metadata** only (cannot decrypt business data) | Secure aggregation views across Agency DBs                              |
| L2 Tenant   | **Agency** (Operator / Admin)       | All Clients under that Agency                                              | **Physical isolation unit**: dedicated Neon project + dedicated KMS key |
| L3 Brand    | **Client** (Viewer)                 | Only their own `client_id` data                                            | RLS / view inside the Agency database (logical isolation within Agency) |

**Core principles:**

- **Tenant = Agency**: physical isolation boundary sits at the Agency layer. Each Agency owns a dedicated Neon project + dedicated KMS key + (for Enterprise/Regulated) dedicated compute endpoint
- **Client is NOT a physical isolation unit**: multiple Clients under one Agency share the Agency's database, with `client_id` RLS + views providing logical isolation inside the Agency
- **Super Admin cannot decrypt PII/PHI across Agencies**: cross-Agency views only expose aggregate metrics (active Agencies, total token usage, platform health); raw business data stays protected by per-Agency KMS keys
- **App layer**: `agency_id` enforcement + `client_id` RLS (warehouse) + physical isolation — three overlapping layers (defense-in-depth)

Zero-copy cloning supports on-demand isolated analytical replicas per Agency without impacting others.

### 2.4 LLM-Native Orchestration

The Core AI Brain is the **unified AI orchestration layer** — business features never call LLMs directly. Every AI capability (Persona / Creative / Attribution / Media agents and beyond) flows through this layer. It centrally owns context assembly (PII-safe), model routing, token budgeting, agent orchestration, tool-call approval and auditing. This makes models swappable, cost observable, compliance traceable, and prevents the "each feature wires its own LLM" anti-pattern that leaks data and duplicates effort.

### 2.5 Autonomy Boundary

MVP adopts **human-in-the-loop**:

- AI may generate recommendations, explanations and plans
- AI may prepare executable payloads
- **Budget changes, ad launches, pauses and external platform write-back actions require human approval**
- Each tenant can configure autonomy level (conservative / balanced / aggressive)

---

## 3. 3-Lake (Medallion) Data Strategy

The platform uses **three independent Neon projects forming a three-tier Lake**. All raw data is fully written to the Landing Lake first, then derived by field class into the Raw PII Lake and Processed Lake.

### 3.0 Landing Lake (Bronze · Raw Data Landing Zone)

**The first stop for every external response.** The full original record is preserved as-is — PII columns Fernet-encrypted at column level, non-PII columns in plaintext.

**Key policies:**

- Written to `landing.<source>_records` (full record + record_id UUID + ingest_metadata)
- PII columns are Fernet + per-Agency KMS encrypted on write; non-PII columns plaintext
- **Immutable** — no modification, no overwrite, no deletion (except DSAR / retention expiry)
- Business users / AI Brain / dashboards / Pillars are **all forbidden** from reading; only ELT service accounts + compliance auditors can access
- `landing.sync_state` holds the cursor / watermark per source, powering incremental resume

**Compliance position**: Landing and the Raw PII Lake sit within the **same PII trust boundary** (equal independent KMS / VPC / mTLS / access controls). From the auditor's perspective, Landing is the "ground-truth replica of raw data" — together with Raw PII Lake it satisfies GDPR Art. 25 / HIPAA §164.312 / SOC 2 CC6 "raw data traceability + protection" requirements.

| Attribute | Design                                                                                                     |
| --------- | ---------------------------------------------------------------------------------------------------------- |
| Content   | Full original records from 14 P1 sources + Tresorit uploads (PII cols encrypted)                           |
| Storage   | per-Agency dedicated Neon project (`{agency}-landing`) · independent KMS key                               |
| Retention | HIPAA 6y / non-HIPAA 90d                                                                                   |
| Access    | ELT service accounts (write + reprocess read) + compliance auditors (read). Business / AI / Portal: denied |
| Purpose   | Reprocessing / DSAR location / legal discovery / audit traceability                                        |

### 3.1 Raw PII-Segregated Lake (PII Dim Lake)

**Derived from the Landing Lake** — STAGE 3 SPLIT extracts fields classified L2/L3 (PII/PHI) in Landing and writes them here. Holds **only PII fields** (not full records — the full record lives in Landing); this is the sole plaintext source for the PII Access Service.

**Key policies:**

- Only 3 tables: `raw_secure.users` (subject dim) · `raw_secure.<source>_pii_fields` (per-source PII extracts) · `raw_secure.pii_access_log` (egress audit)
- PII fields stay Fernet + per-Agency KMS encrypted (key is independent of Landing's KMS key)
- Identifiers required for analytics are turned into **`pii_token = SHA-256(email_hash + agency_salt)`** — the cross-Lake irreversible subject identifier
- Raw PII **never exposed to AI prompts**, never enters reports, never enters default processed schema
- All access logged to `pii_access_log` (user / tenant / data type / purpose / time / result) — PII Access Service uses this path

| Attribute | Design                                                                                                                            |
| --------- | --------------------------------------------------------------------------------------------------------------------------------- |
| Content   | Subject dim (email/phone enc + hashes + pii_token) + per-source PII extracts + egress audit                                       |
| Storage   | per-Agency dedicated Neon project (`{agency}-raw-pii`) · independent KMS                                                          |
| Retention | Default 90 days; HIPAA 6 years; GDPR financial 7 years                                                                            |
| Access    | ETL service accounts (write) + PII Access Service (gated read) + Compliance Auditors (read). Business users / AI / Portal: denied |
| Audit     | Every SELECT/EXPORT logged; auto-alerting on anomalies                                                                            |

### 3.2 Processed Lake

**Derived from the Landing Lake** — STAGE 3 SPLIT extracts fields classified L0/L1 (non-PII) in Landing and writes them to `processed.raw.<source>_records` in this Lake; the dbt 4-layer pipeline (staging → canonical → marts → ai_context) then transforms them into analytics-ready, retrievable, AI-consumable data. **Carries no plaintext PII**; only the irreversible `pii_token` hash is kept for cross-Lake linkage.

**Typical data:**

- `processed.raw.<source>_records`: non-PII raw fields + pii_token + ingest_metadata (immutable, HIPAA 6y / non-HIPAA 90d)
- Ad platform: Campaign / Ad Group / Line Item / Creative / Spend / Impression / Click / Conversion
- GA4: events / sessions / traffic source / conversion / e-commerce metrics
- Data providers (Experian / TransUnion / Nielsen): audience segments, demographics, psychographics, market signals
- Placer IQ / Quorum: location, behavior, offline signals
- Derived metrics: attribution, media performance, Persona blueprint, Creative performance

### 3.3 PII Segregation Boundary (Hard Isolation)

> **Design intent**: the boundary between the **PII zone** (Landing Lake + Raw PII Lake) and the **Processed Lake** is **hard isolation**, **NOT** "same lake split by partition / schema". Schema or partition split alone is **insufficient** to meet GDPR / CCPA / HIPAA / SOC 2 "reasonable security" and "physical safeguard" clauses. Landing and Raw PII share the same PII trust boundary (equal encryption & access control); the PII Boundary sits between them and the Processed Lake.

The boundary is enforced across **6 layers**:

| #   | Layer          | Enforcement                                                                                                                                                                                                                       |
| --- | -------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| 1   | **Storage**    | The PII zone (Landing + Raw PII, 2 Neon projects) and the Processed Lake (independent Neon project) live in **different physical storage clusters** — different endpoints + storage, **not** schema-split within a single cluster |
| 2   | **Encryption** | The PII zone and the Processed Lake use **completely independent KMS master keys**. Processed Lake service accounts **never hold** the PII zone's decryption keys.                                                                |
| 3   | **Network**    | Private VPC subnet isolation; only the ELT worker crosses (bidirectional mTLS). The Processed Lake network cannot route to Raw Lake storage endpoints.                                                                            |
| 4   | **Identity**   | Least-privilege service accounts; cross-Lake calls use short-lived purpose-bound tokens (≤ 15 min); no long-lived credentials.                                                                                                    |
| 5   | **Data**       | Cross-Lake writes must pass through `anonymize_record_for_warehouse()`; records containing raw PII are **rejected at the storage layer** (schema constraints + write hook).                                                       |
| 6   | **Audit**      | All cross-Lake traffic and anomalies logged INSERT-only, 6-year retention; DLP continuously scans Processed Lake to catch PII leakage.                                                                                            |

**Linkage mechanism**: the three Lakes are linked via **`pii_token` hash join keys** (SHA-256(email_hash + agency_salt)). Processed Lake holds hashes that match Landing / Raw PII Lake hashes for the same subject, but the hash is **irreversible**; plaintext PII never leaves the PII zone (Landing + Raw PII). `record_id` (UUID) is used for same-record back-reference between Landing and Raw PII / Processed (reprocessing / DSAR-location scenarios).

**Compliance attestation (how each regulation is satisfied):**

| Regulation / Clause                                                          | How This Design Satisfies                                                                                    |
| ---------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------ |
| **GDPR** Art. 32 "Security of processing"                                    | Encryption, independent keys, least privilege, audit, DLP — all present                                      |
| **GDPR** Art. 25 "Privacy by Design"                                         | PII never enters the analytics or AI path by default                                                         |
| **HIPAA** §164.312(a) "Access control" + §164.312(e) "Transmission security" | Separated service accounts, mTLS, purpose-bound tokens; BAA clients get isolated KMS                         |
| **HIPAA** §164.308 "Administrative safeguards"                               | INSERT-only audit retained 6 years; workforce clearance (only Compliance Auditors hold Raw Lake read access) |
| **CCPA / CPRA** §1798.81.5 "Reasonable security"                             | Multi-layer physical / network / encryption isolation; DLP; DSAR workflow                                    |
| **SOC 2 Type II** CC6 "Logical and physical access controls"                 | Physical storage separation, independent KMS, audit trail → fulfills the control-matrix evidence collection  |

> If the PII zone and the Processed Lake were merely schema-split inside one database, auditors would treat them as the **same trust boundary** — making "physical safeguard" independently unattestable. **This design explicitly rejects that pattern.**

### 3.4 PII Access Service (Controlled Plaintext Egress)

Several downstream pillars must consume **plaintext PII** as input:

| Use case                                     | Why plaintext is required                                                                                                                                                                                                                                        |
| -------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Lookalike modeling / seed list export**    | Platforms (Meta / DV360 / LiveRamp / Trade Desk) typically accept SHA-256-hashed email/phone as seeds, **and the hash must be computed from plaintext**. If Processed Lake only stores salted internal hashes, you cannot regenerate the platform-specific hash. |
| **Meta Custom Audience upload**              | Accepts SHA-256(email/phone); the hash must be computed at upload time (each platform may use a slightly different hashing protocol).                                                                                                                            |
| **GDPR / CCPA DSAR — data subject location** | Must be able to locate every record for a given individual using name / email / phone ("this person's data").                                                                                                                                                    |
| **Legal request / compliance investigation** | Regulatory or judicial requests requiring identification down to the natural person.                                                                                                                                                                             |

**Design: the PII Access Service is the sole controlled egress for plaintext PII out of Raw Lake.**

```
        ┌──────────────────────────────────────────────────┐
        │           Raw PII-Segregated Lake                │
        │  (encrypted; per-Agency KMS; restricted access)  │
        └────────────────────┬─────────────────────────────┘
                             │
                             ▼ purpose-bound token (≤15min, audited)
        ┌──────────────────────────────────────────────────┐
        │          PII Access Service                      │
        │  • Creds: scoped + purpose-bound + time-limited  │
        │  • Op: read-decrypt → in-memory transform        │
        │  • Egress: only platform-specific hashes or DSAR │
        │  • Audit: who / what / why / when / which rows   │
        └────┬──────────────┬──────────────────┬──────────┘
             │              │                  │
             ▼              ▼                  ▼
         Meta CA       DV360 / LiveRamp        DSAR
         upload        seed list           response pack
         (SHA-256)
```

**Key security properties:**

- **Plaintext PII never leaves the service's memory**: service reads → decrypts → hashes/packs in-memory → egress contains only transformed artifacts (hash list / DSAR JSON)
- **Purpose-bound token**: each operation must declare a purpose (`audience.upload.meta` / `dsar.lookup` / `compliance.investigation`) and obtain a corresponding scoped short-lived credential
- **Operation allow-list**: the service exposes no general SQL — only whitelisted operations (`build_audience_hash_list`, `dsar_locate_subject`, `legal_export`, etc.)
- **Row-level audit**: which `record_id`s were read, by whom, for what purpose, and which output hashes / responses were produced; 6-year retention
- **No coupling with Processed Lake / AI Brain**: the service egresses directly to external platform APIs / customer email (DSAR). Plaintext PII **never enters** the Processed Lake, Context Builder, or any Agent.

**Business user perspective**: when a Campaign Manager triggers "Upload audience to Meta", they never see plaintext PII; the UI reports only "1234 hashed identities exported". Which user can trigger which PII Access category is gated by Agency Admin role.

**Agency-level isolation still holds**: the service uses an independent KMS decryption context per Agency; cross-Agency invocation is impossible.

### 3.5 Data Classification & Shared Reference Strategy (Tenant Scoping & Dedup)

> **Stakeholder question **: When data enters the warehouse, is it tenant-scoped from the moment of ingestion? What about cross-tenant data sources like Nielsen or audience platforms? We don't want to re-ingest duplicate data (e.g. Experian) for every Agency.

**Answer**: classify data **by nature**, not by a one-size-fits-all per-Agency isolation. Ingest path differs per class.

#### 3.5.1 Three Data Classes

| Class                             | Definition                                                                                                                              | Examples                                                                                                                                                                        | Where it lands                                                                                     | Ingest cadence                                                                                       |
| --------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | -------------------------------------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------- |
| **A. Tenant-Private**             | Data belonging to a specific Agency / Client (with or without PII)                                                                      | Meta / DV360 / TikTok / GA4 ad and conversion data; HubSpot CRM; Tresorit-uploaded customer CSVs                                                                                | **per-Agency Neon project** (Raw PII Lake + Processed Lake)                                        | per-Agency, per Agency's schedule                                                                    |
| **B. Shared Reference**           | Platform-licensed, cross-tenant **pure reference data** (no individual-level PII, or PII already aggregated/anonymised by the provider) | Experian demographic taxonomies / segments; Nielsen panel-level reach; Placer IQ POI tags; Quorum legislative metadata; ad-platform public taxonomies (vertical / region codes) | **Shared Reference Lake** (a separate, platform-level Neon project; exposed read-only to Agencies) | platform-wide, single ingest per provider refresh cadence (e.g. Experian monthly, Nielsen bi-weekly) |
| **C. Tenant-Derived from Shared** | Result of joining Shared Reference with the Agency's Tenant-Private data                                                                | "Client X's audience scored against the Experian taxonomy"                                                                                                                      | Written into **that Agency's Processed Lake**; **never written back** to Shared Reference Lake     | Computed on demand, recomputed as needed                                                             |

> **Architectural shift**: from "3-Lake per Agency" (Landing + Raw PII + Processed) extended to "**3-Lake per Agency + 1 Shared Reference Lake (platform-level)**". Shared data is ingested once, paid for once, stored once. Private data remains physically isolated per Agency.

#### 3.5.2 Shared Reference Lake Design

```text
┌─────────────────── Shared Reference Lake (platform-level Neon project) ─────────┐
│  · Dedicated Neon project: shared_reference                                       │
│  · Schemas: shared_experian / shared_nielsen / shared_placeriq / shared_quorum / │
│             shared_taxonomy (IAB / DMA / industry / ISO regions)                 │
│  · No individual-level PII — providers aggregate / anonymise at source            │
│    (contractually enforced)                                                       │
│  · Read access exposed to each Agency through license-gated views                 │
└──────────────────────────────────────────────────────────────────────────────────┘
                              │
                              │  ① Platform ELT, single ingest
                              │     Dagster asset = single source of truth
                              │     content-hash dedup (see §3.5.4)
                              ▼
        ┌─────────────────────────────────────────────────────────────┐
        │  License Gate (per-Agency visibility matrix)                 │
        │   agency_id │ experian │ nielsen │ placeriq │ quorum         │
        │   ─────────┼──────────┼─────────┼──────────┼───────          │
        │   ACME      │   ✓      │   ✓     │    ✗     │   ✗            │
        │   BETA      │   ✓      │   ✗     │    ✓     │   ✓            │
        └─────────────────────────────────────────────────────────────┘
                              │
                              │  ② Expose read-only view per license matrix
                              │     unauthorised categories filtered out
                              ▼
        ┌─────────── ACME's Processed Lake ───────────┐  ┌── BETA's ──────┐
        │  shared.experian → READ ONLY               │  │   …            │
        │  shared.nielsen  → READ ONLY               │  │                │
        │  shared.placeriq → 403 (no license)         │  └────────────────┘
        │  (Agency-owned marts / canonical local)     │
        └────────────────────────────────────────────┘
```

**Implementation notes:**

| Item                    | Detail                                                                                                                                                                                                    |
| ----------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Physical location**   | Shared Reference Lake = a standalone Neon project (peer to Agency projects); exposed **read-only**                                                                                                        |
| **Exposure mechanism**  | Cross-project access via **postgres_fdw** (Foreign Data Wrapper) or a pre-built read-only logical replica, mounted into each Agency's Processed Lake under `shared.*` schema                              |
| **License enforcement** | `license_grants` table holds `(agency_id, source, valid_until, contract_id)`; FDW view carries RLS: `USING (current_setting('app.agency_id') IN (SELECT agency_id FROM license_grants WHERE source=...))` |
| **JOIN pattern**        | Agency ELT runs `JOIN shared.experian_segments` inside its Processed Lake — data is **not copied** to the Agency, only joined at query time                                                               |
| **Audit**               | Every cross-project SELECT logs an audit_event (agency_id · source · rows_read · query_id); 6-year retention                                                                                              |
| **PII boundary**        | Shared Reference Lake **carries no individual-level PII**, so it does not cross the PII Boundary; provider contracts state this explicitly                                                                |
| **HIPAA tenants**       | Can still read Shared Reference (no PHI); Tenant-Derived results remain bound by BAA region constraints                                                                                                   |

#### 3.5.3 Class Mapping for the 14 P1 Integrations

| Integration                                         | Class                                   | Cadence                                    | Lands in                                                            | Notes                                                                         |
| --------------------------------------------------- | --------------------------------------- | ------------------------------------------ | ------------------------------------------------------------------- | ----------------------------------------------------------------------------- |
| **Meta / DV360 / TikTok / Trade Desk / StackAdapt** | A. Tenant-Private                       | per-Agency, near-real-time / hourly        | Agency's Raw PII Lake (user_id / device_id hashed) + Processed Lake | Each Agency holds its own ad-account credentials                              |
| **GA4**                                             | A. Tenant-Private                       | per-Agency, daily                          | Agency's Raw PII Lake (cookie / client_id) + Processed Lake         | Agency owns its own GA4 property                                              |
| **HubSpot**                                         | A. Tenant-Private                       | per-Agency, hourly                         | Agency's Raw PII Lake (email / phone) + Processed Lake              | Each Agency's own HubSpot account                                             |
| **Tresorit**                                        | A. Tenant-Private                       | per-Agency, event-triggered                | Agency's Raw PII Lake                                               | Customer upload — private by nature                                           |
| **Quorum** (legislative monitoring)                 | B. Shared Reference                     | platform-wide, daily                       | Shared Reference Lake `shared_quorum`                               | Legislative data is public; license controls who can read                     |
| **Experian** (demographics)                         | B. Shared Reference                     | platform-wide, monthly                     | Shared Reference Lake `shared_experian`                             | **Key savings point** — avoids N× license + N× ingest                         |
| **TransUnion** (credit + demographics)              | B. Shared Reference + C. Tenant-Derived | platform-wide monthly + per-Agency lookups | Shared holds taxonomy; Agency lookup results land in Processed      | Part of TransUnion queries is keyed off an Agency-supplied list               |
| **LiveRamp** (identity resolution)                  | **C. Tenant-Derived only**              | per-Agency, on-demand                      | Agency's Raw PII Lake (IDR results)                                 | LiveRamp is a lookup service over an Agency-supplied list, not reference data |
| **Nielsen**                                         | B. Shared Reference                     | platform-wide, bi-weekly                   | Shared Reference Lake `shared_nielsen`                              | Panel data is aggregate by design                                             |
| **Placer IQ**                                       | B. Shared Reference                     | platform-wide, monthly                     | Shared Reference Lake `shared_placeriq`                             | POI / footfall data is aggregate by design                                    |

> **Cost impact**: a single Experian license is roughly $80k–$200k/year. Running one license per Agency is not sustainable at 50+ Agencies. Centralised ingest with the platform holding the master license, then charging-back Agencies per usage, cuts effective data cost by **70–90%**.

#### 3.5.4 Dedup at Ingestion

Both A- and B-class ELT Extract paths follow **idempotent + content-hash dedup**:

| Mechanism                              | Detail                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                            |
| -------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **① Cursor resume (Watermark)**        | **Cursor = a stored marker for "where the last pull stopped" (timestamp / offset / page token)**. Each source × tenant (A) or source (B) keeps a `sync_state` row: `(source, scope_id, last_cursor, last_run_at)`. Extract always resumes from `last_cursor`; the prior rows are never re-pulled.<br>**Example**: first run hits Meta API → 1000 rows → `last_cursor = 2026-05-18T14:30`; 1 hour later → API request `since=2026-05-18T14:30` → only 50 new rows returned, the original 1000 are **not** re-pulled.<br>Industry synonyms: Incremental Sync · Watermark Extraction · Delta Loading |
| **② Content Hash**                     | Every record is fingerprinted before insert: `record_hash = SHA-256(canonical_field_subset)`. Table carries `UNIQUE(tenant_id_or_null, source, record_hash)`; identical content is rejected at the storage layer (safety net when cursor fails)                                                                                                                                                                                                                                                                                                                                                   |
| **③ Upsert by Business Key**           | Transform stage uses `MERGE ... ON business_key` (not `INSERT`) — 5 pulls of the same campaign produce 1 canonical row                                                                                                                                                                                                                                                                                                                                                                                                                                                                            |
| **④ Source Refresh Cadence**           | B-class shared data: fixed batches (Experian monthly, Nielsen bi-weekly); no ad-hoc re-pulls. A-class: Agency-configurable but with a min-interval guard (no same-source re-trigger within 5 min)                                                                                                                                                                                                                                                                                                                                                                                                 |
| **⑤ DSAR Delete only affects A-class** | Subject erasure touches A-class Raw PII; B-class carries no individual PII so it is out of DSAR scope (contractually enforced)                                                                                                                                                                                                                                                                                                                                                                                                                                                                    |
| **⑥ Content-fingerprint audit**        | Every ingest logs `(source, scope_id, record_hash_count_new, record_hash_count_skipped)` — provable absence of duplicates                                                                                                                                                                                                                                                                                                                                                                                                                                                                         |

**Concrete flow for a B-class source (Experian):**

```text
Day 1 (start of month):
  Dagster asset: shared.experian.refresh
    → Platform calls Experian API once (master credential)
    → Writes to shared_reference Neon project
    → license_grants already covers ACME, BETA, DELTA → all three can query
    → Total cost: 1 × API call + 1 × storage

Day 15 (Agency ACME wants an ad-hoc refresh):
  ACME UI: "Refresh Experian segments"
    → Rejected: B-class shared data refreshes on platform cadence (next: Day 30)
    → Or: only Platform Super Admin can trigger a cross-platform refresh

Day 30:
  Dagster asset: shared.experian.refresh
    → content-hash dedup: 1,200,000 segments last time, 1,200,030 this time
    → Only 30 new hashes written; rest reused
    → Total write volume: < 1% storage delta
```

**Concrete flow for an A-class source (Meta / GA4):**

```text
ACME @ Hour T:
  Dagster asset: meta.acme.ad_insights[partition=today]
    → Pulls with ACME's OAuth token
    → Writes to ACME's Raw PII Lake (ad_ids etc. are ACME-private)
    → Completely independent of BETA

ACME @ Hour T+1:
  Same asset; cursor resumes from T
    → content-hash dedup removes any T-1 → T overlap already written
```

#### 3.5.5 Key Security / Compliance Properties

- **PII stays in Tenant-Private**: B-class shared data carries no individual-level PII by contract + technical guarantee; it never crosses the PII Boundary
- **License compliance**: unauthorised Agencies are blocked at the view layer via RLS — data is physically present but **logically zero rows** for them. This is the industry-standard pattern, paired with contract audits to satisfy provider compliance
- **Cross-Agency benchmarking unaffected**: Platform Super Admin can still aggregate A-class data across Agencies (e.g. "median TikTok ROAS"); the Shared Reference Lake does not break Agency-level physical isolation
- **DSAR does not touch Shared Reference**: erasure requests act only on A-class Raw PII Lake; B-class data carries no individual records by contract

#### 3.5.6 Decision Summary

| Question                             | Answer                                                                                                                                                                                     |
| ------------------------------------ | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| Is data tenant-scoped at ingestion?  | **A-class: yes** (per-Agency project physical isolation starts at ingest). **B-class: no** (single platform-wide ingest). **C-class: yes** (derived results land in the Agency's own Lake) |
| How do we handle Experian / Nielsen? | **B-class** — single platform-wide ingest, license-gated read views per Agency, visibility enforced by license matrix                                                                      |
| How do we prevent duplicate data?    | 5 layers: cursor resume + record_hash dedup + business-key upsert + fixed refresh cadence + single platform-wide source of truth                                                           |
| Cost impact                          | 70–90% reduction in B-class license + storage cost                                                                                                                                         |
| Compliance impact                    | None (B-class carries no PII by contract; Tenant-Private stays physically isolated; license gating via RLS + audit double-control)                                                         |

### 3.6 Raw Data Lifecycle & Post-Processing Division

> **Stakeholder question**: How is the raw data (which contains everything) processed? How is the post-processed data partitioned?

External-source records are typically a mixture of PII + business fields + metadata (e.g. one Meta `ad_insights` row holds `user_id`, `campaign_id`, `impressions`, and `age_breakdown` all in one). **All incoming raw records must first land in full into the 🟫 Landing Lake (Bronze tier)** for preservation, then be classified, field-split, and derived into the 🔴 Raw PII Lake and 🟢 Processed Lake. This is the standard **Medallion Architecture** — stakeholders and auditors are familiar with it, and reprocessing / DSAR / legal-discovery are all easier.

> **Architecture (Landing-First / Medallion)**:
>
> - **Step 1**: every source response is **fully** written to the 🟫 Landing Lake (PII columns Fernet-encrypted, non-PII plaintext) — this is the "ground-truth replica of raw data"
> - **Step 2**: the classification engine reads Landing and derives outputs into 🔴 PII Lake (PII fields only) and 🟢 Processed Lake (non-PII + pii_token)
> - **Compliance argument**: Landing Lake and Raw PII Lake sit inside the **same PII trust boundary** (independent Neon projects + independent KMS + independent VPC + mTLS). Together they satisfy GDPR Art. 25 + HIPAA §164.312 + SOC 2 CC6 in full.

#### 3.6.1 Four-Stage Processing Flow

```text
┌──────────── STAGE 1: LAND (full record → Bronze) ──────────────────┐
│ External API response → parsed → **fully written to 🟫 Landing Lake**│
│                                                                     │
│  · Table: landing.<source>_records                                  │
│  · The full original record is preserved end-to-end                 │
│    - PII cols (email, phone, ssn …) → field-level Fernet encrypted  │
│    - Non-PII cols (campaign_id, impressions …) → plaintext          │
│  · System-generated record_id (UUID) is the cross-Lake join key     │
│  · ingest_metadata: source, batch_id, fetched_at, record_hash       │
│  · immutable · HIPAA 6y / non-HIPAA 90d                              │
│  · Access: ELT service account + compliance auditor only            │
│  · 🚫 Business users / AI / dashboards are forbidden from reading   │
└────────────────┬───────────────────────────────────────────────────┘
                 │
                 ▼
┌──────────── STAGE 2: CLASSIFY (read Landing, tag per-field) ──────┐
│ Read landing.<source>_records; tag each field by class             │
│                                                                     │
│  · L0 Public:       campaign_id, ad_set_id, creative_name           │
│  · L1 Internal:     spend, impressions, clicks, account_id          │
│  · L2 PII:          email, phone, IP, full_name, address            │
│  · L3 PHI:          health-related fields (HIPAA customer scenarios)│
│  · Output: field_classification_manifest (one row per field)        │
│  · L2/L3 hits → PII/PHI Detector dual-scan; write audit_event       │
│  · 🚦 Process only · not persisted to any warehouse                │
└────────────────┬───────────────────────────────────────────────────┘
                 │
                 ▼
┌──────────── STAGE 3: SPLIT (read Landing, derive to both sides) ──┐
│ Per manifest, derive PII / non-PII outputs (two Neon projects)      │
│                                                                     │
│  ┌─ 🔴 Derive A: PII fields → Raw PII Lake (per-Agency)              │
│  │    · raw_secure.users — subject dim UPSERT                        │
│  │      (email_enc / phone_enc / hashes / pii_token)                 │
│  │    · raw_secure.<source>_pii_fields — per-source PII column       │
│  │      extracts (carries record_id back-reference; no non-PII cols) │
│  │    · Field-level Fernet + per-Agency KMS                          │
│  │      (key is independent of the Landing KMS key)                  │
│  │                                                                   │
│  └─ 🟢 Derive B: non-PII fields → Processed Lake (per-Agency)        │
│       · processed.raw.<source>_records                               │
│         — non-PII fields + pii_token + record_id + ingest_metadata  │
│       · immutable · HIPAA 6y / non-HIPAA 90d                         │
│       · No L2/L3 field present; DLP continuously scans for leakage   │
│                                                                     │
│  Cross-Lake key: pii_token = SHA-256(email_hash + agency_salt)      │
│  ⚠ Landing still holds the full record — source of truth for        │
│    compliance and reprocessing                                      │
└────────────────┬───────────────────────────────────────────────────┘
                 │
                 ▼
┌──────────── STAGE 4: TRANSFORM (dbt 4 layers in Processed Lake) ──┐
│ raw → staging → canonical → marts → ai_context                     │
│                                                                    │
│  processed.raw.<source>_records  (STAGE 3 output; dbt source)      │
│       │                                                            │
│       ▼                                                            │
│  staging.stg_<source>    dbt staging / standardisation             │
│       │                                                            │
│       ▼                                                            │
│  canonical.*         Unified to the 13 Canonical Entities           │
│                      (campaign / persona / touchpoint …)            │
│                      · pii_token JOINs out a unified user entity    │
│                      · The user entity itself carries no plaintext  │
│       │                                                            │
│       ▼                                                            │
│  marts.*             Business-facing aggregates                     │
│                      · Feeds dashboards / APIs / Pillar services    │
│                      · pii_token usually aggregated away (GROUP BY) │
│       │                                                            │
│       ▼                                                            │
│  ai_context.*        AI-safe summaries + pgvector embeddings        │
│                      · Sole source for Context Builder retrieval     │
│                      · No pii_token (anonymised to segment level)   │
└────────────────────────────────────────────────────────────────────┘
```

#### 3.6.2 Post-Processing Division (What Lives Where · 4-Lake architecture)

> **Architecture**: each Agency owns **3 independent Neon projects** (Landing / Raw PII / Processed) plus a platform-level Shared Reference Lake. Landing and Raw PII sit within the same PII trust boundary (both contain PII, protected equally); the Processed Lake is the business / AI path and **carries no plaintext PII**.

| Schema / table                   | Lake                                    | Form                                                                                                 | Retention                | Read access                                                            |
| -------------------------------- | --------------------------------------- | ---------------------------------------------------------------------------------------------------- | ------------------------ | ---------------------------------------------------------------------- |
| `landing.<source>_records`       | **🟫 Landing Lake (Bronze)**            | **Full original record** (PII cols encrypted + non-PII plaintext) · all fields preserved · immutable | HIPAA 6y / non-HIPAA 90d | ELT service account · compliance auditor (business / AI **forbidden**) |
| `landing.sync_state`             | **🟫 Landing Lake**                     | Per-source cursor / watermark / last_run_at (incremental-resume state)                               | Permanent                | ELT service account                                                    |
| `raw_secure.users`               | **🔴 Raw PII Lake**                     | Subject dim: email_encrypted / phone_encrypted / hashes / pii_token                                  | HIPAA 6y / non-HIPAA 90d | PII Access Service · compliance auditor                                |
| `raw_secure.<source>_pii_fields` | **🔴 Raw PII Lake**                     | Per-source PII column extracts (carries record_id back-reference; **no non-PII columns**)            | Same as above            | Same as above                                                          |
| `raw_secure.pii_access_log`      | **🔴 Raw PII Lake**                     | Row-level audit of every PII Access Service call                                                     | HIPAA 6y                 | compliance auditor                                                     |
| `processed.raw.<source>_records` | **🟢 Processed Lake**                   | Non-PII fields + pii_token + ingest_metadata ("non-PII raw record copy", immutable)                  | HIPAA 6y / non-HIPAA 90d | dbt · ELT service account · business read-only                         |
| `staging.stg_<source>`           | **🟢 Processed Lake**                   | dbt staging intermediate                                                                             | 30 days                  | dbt · ELT service account                                              |
| `canonical.<entity>`             | **🟢 Processed Lake**                   | 13 canonical entities (joined via pii_token)                                                         | 3 years                  | business / AI / reporting                                              |
| `marts.<report>`                 | **🟢 Processed Lake**                   | Business aggregates (pii_token mostly GROUP-BY'd away)                                               | 3 years / financial 7y   | business / AI / reporting / portal                                     |
| `ai_context.*`                   | **🟢 Processed Lake**                   | Summaries + pgvector embeddings (segment-level)                                                      | 1 year                   | Core AI Brain · Context Builder                                        |
| `audit.audit_events`             | **🟢 Processed Lake** (separate schema) | Platform-wide INSERT-only audit                                                                      | HIPAA 6y / financial 7y  | compliance auditor · Platform Super Admin                              |
| `shared_*.*`                     | **🟣 Shared Reference Lake**            | B-class reference (no individual PII)                                                                | Per provider contract    | license-holding Agencies (FDW read-only)                               |

#### 3.6.2.1 Which Lake each STAGE writes to (Lake Ownership Matrix · 4-Lake architecture)

> **Common stakeholder question**: which of the 4 STAGES belongs to which Lake? Answer: **STAGE 1 writes Landing; STAGE 3 derives into PII Lake + Processed Lake; STAGE 4 transforms within the Processed Lake**.

| STAGE                                                  | 🟫 Landing Lake                                                                                        | 🔴 Raw PII Lake                                                                        | 🟢 Processed Lake                                           | 🚦 Process-only                                                   |
| ------------------------------------------------------ | ------------------------------------------------------------------------------------------------------ | -------------------------------------------------------------------------------------- | ----------------------------------------------------------- | ----------------------------------------------------------------- |
| **STAGE 1 LAND** (full record → Bronze)                | ✅ `landing.<source>_records` (full record · PII cols encrypted) · `landing.sync_state` (cursor state) | —                                                                                      | —                                                           | —                                                                 |
| **STAGE 2 CLASSIFY** (read Landing, tag per-field)     | reads Landing                                                                                          | —                                                                                      | —                                                           | ✓ Emits `field_classification_manifest` (not stored in warehouse) |
| **STAGE 3 SPLIT** (read Landing, derive to both sides) | reads Landing                                                                                          | ✅ `raw_secure.users` · `raw_secure.<source>_pii_fields` · `raw_secure.pii_access_log` | ✅ `processed.raw.<source>_records`                         | —                                                                 |
| **STAGE 4 TRANSFORM** (dbt 5 layers)                   | —                                                                                                      | —                                                                                      | ✅ `staging.*` → `canonical.*` → `marts.*` → `ai_context.*` | —                                                                 |

**🟫 Landing Lake never holds**: derived tables / staging / canonical / marts / ai_context / audit_events — only the original record + sync_state.
**🔴 Raw PII Lake never holds**: the full original record · non-PII business fields (campaign_id / impressions / etc.) · ingest_metadata · audit_events · any of the staging / canonical / marts / ai_context layers.
**🟢 Processed Lake never holds**: plaintext PII fields (email / phone / full_name / address / IP / SSN) — only the irreversible `pii_token` hash.

#### 3.6.3 End-to-End Example: Meta Ad Insight Record

```text
1) External source returns (plaintext JSON):
   { "ad_id":"123", "campaign_id":"456", "user_id":"meta_hash_abc",
     "email":"john@example.com", "spend":12.50, "impressions":1500 }

2) STAGE 1 → raw_secure.meta_ads_raw:
   ad_id=123, campaign_id=456,
   user_id=meta_hash_abc (L1, plaintext),
   email_encrypted=Fernet(john@example.com) (L2, encrypted),
   email_hash=SHA-256("john@example.com"+salt) (for lookup),
   spend=12.50, impressions=1500,
   ingest_metadata={batch_id, fetched_at, record_hash}

3) STAGE 2 classify:
   ad_id, campaign_id, spend, impressions = L0/L1
   email_encrypted, email_hash = L2 → PII manifest row written

4) STAGE 3 split:
   · email_encrypted stays in raw_secure (does not leave Raw Lake)
   · pii_token = SHA-256(email_hash + agency_salt) computed
   · staging.stg_meta_ads insert:
       ad_id=123, campaign_id=456, user_id=meta_hash_abc,
       pii_token=<token>, spend=12.50, impressions=1500
   · Note: the staging row has no email — only pii_token

5) STAGE 4 dbt:
   · canonical.touchpoint: pii_token + campaign_id + ts + event_type
   · marts.campaign_perf: GROUP BY campaign_id → no pii_token
   · ai_context.audience_summary: pii_token aggregated to segment level

6) Downstream consumption:
   · Dashboards / reports read marts.* (no PII visible)
   · AI Brain reads ai_context.* (no pii_token visible)
   · Meta CA upload: UI → PII Access Service → service reads
     raw_secure.users, decrypts email → computes Meta-protocol SHA-256
     → API egress
```

#### 3.6.4 End-to-End Example: HubSpot Contact Sync (CRM with email/phone)

```text
1) HubSpot API: { "id":"hub-789", "email":"jane@acme.com",
                  "phone":"+1-415-…", "company":"Acme", "lifecycle":"MQL" }

2) STAGE 1 raw_secure.hubspot_contacts_raw:
   id=hub-789,
   email_encrypted=Fernet(jane@acme.com), email_hash=SHA-256(...),
   phone_encrypted=Fernet(+1415...), phone_hash=SHA-256(...),
   company="Acme" (L0), lifecycle="MQL" (L1)

3) STAGE 2: email/phone = L2; company/lifecycle = L0/L1

4) STAGE 3:
   · raw_secure.users UPSERT: pii_token = SHA-256(email_hash + agency_salt)
   · staging.stg_hubspot_contacts:
       hubspot_id=hub-789, pii_token=<token>, company="Acme",
       lifecycle="MQL" — no email/phone at all

5) STAGE 4:
   · canonical.persona JOIN raw_secure.users via pii_token
     yields a unified persona entity (still no email column)
   · marts.lead_funnel aggregates by lifecycle
   · ai_context.crm_summary: anonymised to segment level

6) Downstream:
   · Reports show "Acme · MQL"
   · Email marketing send: Pillar → PII Access Service →
     service reads raw_secure.users → SMTP egress →
     business team never sees jane@acme.com in the UI
```

#### 3.6.5 End-to-End Example: Experian Segment Refresh (B-class)

```text
1) Platform master credential calls Experian API:
   1,200,030 segment rows (taxonomy + segment definitions)
   Note: API returns segment-level aggregates — no individual PII

2) STAGE 1 → Shared Reference Lake.shared_experian.segments_raw:
   · Whole record stored as plaintext (no PII to encrypt)
   · ingest_metadata: refresh_cycle=2025-01, content_hash

3) STAGE 2 classify:
   All fields L0 (public taxonomy data)

4) STAGE 3 split:
   · No split needed — no PII present
   · content_hash dedup: 1,200,000 rows reused, 30 new

5) STAGE 4:
   · shared_experian.segments_canonical
   · Exposed via FDW to license-holding Agencies' Processed Lakes

6) Downstream:
   · ACME's marts.persona JOIN shared.experian_segments via segment_id
     → "Client X's audience profiled against Experian taxonomy"
   · Derived results (C-class) land in ACME's own marts.persona_with_experian
```

#### 3.6.6 Reprocessing & DSAR Coupling (Why raw_secure Must Be Preserved)

| Scenario                       | Operation                                          | Depends on raw_secure for                                                                                                                                                                                            |
| ------------------------------ | -------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **PII Detector upgrade**       | Add SSN rule → rescan history                      | Full-field raw_secure.\*\_raw replay (including previously unrecognised fields)                                                                                                                                      |
| **Business field rule change** | canonical entity schema changes                    | Replay raw_secure → staging → canonical via dbt                                                                                                                                                                      |
| **DSAR delete**                | Subject `john@example.com` requests erasure        | PII Access Service: SHA-256(email+salt) → locate every row with that pii_token across raw_secure / staging / canonical / marts → delete or anonymise per regulation; audit_events preserves the erasure event itself |
| **Legal investigation**        | Regulator demands "all data about this individual" | PII Access Service: same logic → produce DSAR JSON                                                                                                                                                                   |
| **Data quality investigation** | marts report shows anomaly                         | Follow dbt lineage back to raw_secure record                                                                                                                                                                         |
| **Audit-sampling check**       | SOC 2 auditor traces "raw data → report" lineage   | raw_secure → staging → canonical → marts fully reproducible                                                                                                                                                          |

> **Design principle**: `raw_secure.*_raw` is an immutable "ground-truth replica" — once ingested it is not modified, overwritten, or deleted (unless DSAR / retention expiry). `pii_token` is the cross-4-layer "subject locator key" that lets DSAR / reprocessing operate **without decrypting PII** while still pinpointing the subject.

#### 3.6.7 Retention by Tier

| Data layer                        | Lake             | Retention                                                  | Regulation                  |
| --------------------------------- | ---------------- | ---------------------------------------------------------- | --------------------------- |
| `raw_secure.*_raw` (HIPAA tenant) | Raw PII          | **6 years**                                                | HIPAA §164.530(j)           |
| `raw_secure.*_raw` (non-HIPAA)    | Raw PII          | **90 days**                                                | GDPR data minimisation      |
| `raw_secure.users`                | Raw PII          | Contract term + 30 days                                    | GDPR Art. 5(1)(e)           |
| `staging.*`                       | Processed        | **30 days**                                                | Intermediate, recomputable  |
| `canonical.*`                     | Processed        | **3 years**                                                | Business retention          |
| `marts.*`                         | Processed        | **3 years** / financial **7 years**                        | GDPR + financial compliance |
| `ai_context.*`                    | Processed        | **1 year** (refresh)                                       | Derivative, regenerable     |
| `audit.audit_events`              | Processed        | **6 years** / financial **7 years**                        | HIPAA + financial (max)     |
| `shared_*.*`                      | Shared Reference | Per provider contract (often perpetual / refresh-on-cycle) | Provider contract           |

#### 3.6.8 Decision Summary

| Question                            | Answer                                                                                                                                                                             |
| ----------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Where does the raw data go?         | `raw_secure.*_raw` in the **Raw PII Lake** (per-Agency Neon project); PII fields encrypted, non-PII plaintext, full record preserved                                               |
| Why preserve the raw form?          | Required for DSAR / reprocessing / legal investigation / audit traceability                                                                                                        |
| How is post-processed data divided? | 4 dbt layers: `staging` (30d intermediate) → `canonical` (3y standard entities) → `marts` (3y business reporting) → `ai_context` (1y AI retrieval) — all inside **Processed Lake** |
| Does PII exist in Processed?        | **No.** The 4 Processed layers only carry `pii_token` (irreversible hash). Plaintext PII lives only in Raw PII Lake.                                                               |
| How do we join across Lakes?        | `pii_token = SHA-256(email_hash + agency_salt)` — same-Agency Processed can join with Raw; cross-Agency cannot (different salts)                                                   |
| Where do B-class shared data sit?   | Independent schemas in the Shared Reference Lake, no individual PII, exposed via license-gated FDW                                                                                 |

---

## 4. Multi-Tenant Warehouse (Neon Postgres)

### 4.0 Warehouse Choice: Neon Postgres (Product-locked)

> **Product decision**: the warehouse is standardised on **Neon Postgres (serverless)**. Driven by stakeholder preference and the architecture's three core requirements — physical isolation / Branching / zero application-layer migration cost — Neon is the **sole warehouse choice**; Snowflake is no longer retained as a fallback. See [ADR-002-NEON-TENANCY-OPTIMAL](../ADR-002-NEON-TENANCY-OPTIMAL.md).

**Key Neon capabilities:**

| Capability             | Implementation                                                            |
| ---------------------- | ------------------------------------------------------------------------- |
| **Physical isolation** | Dedicated **Project** per Agency (own compute + storage + endpoint + KMS) |
| **Compute / storage**  | Serverless Postgres with dedicated compute endpoint                       |
| **Zero-copy clone**    | **Branching** (git-style branches, instantaneous)                         |
| **Row-Level Security** | Native Postgres `ROW LEVEL SECURITY` + policy                             |
| **Data residency**     | Region-scoped project (us-east / eu-central / ap-\* etc.)                 |
| **App compatibility**  | Standard Postgres protocol; zero migration cost for FastAPI / SQLAlchemy  |
| **Cost model**         | Pay-per-storage + compute (scale-to-zero for idle tenants)                |
| **Ecosystem**          | pgvector · pg_partman · pg_audit natively available                       |

All SQL / implementation details below target Neon Postgres.

### 4.1 Physical Isolation Model (3 Tiers) — Dedicated Project / Database per Agency

**Tenant = Agency**. Each Agency is physically isolated; **Clients under an Agency are logically isolated via RLS inside the Agency database — physical isolation is explicitly NOT extended to the Client level**.

> **Key decision**: do NOT extend physical isolation to the Client layer.
> Stakeholders explicitly require **cross-Agency performance benchmarking** (Rose's stated desire). Per-Client physical isolation would make that capability hard to deliver. Clients are isolated by `client_id` RLS within the Agency database, which satisfies compliance and data-protection requirements.

**No "shared Agency + RLS only" tier**; RLS is always defense-in-depth, never the primary line (see §4.4).

| Agency Tier    | Neon Implementation                                                 | Encryption / Compute                                         | Applies To                                   |
| -------------- | ------------------------------------------------------------------- | ------------------------------------------------------------ | -------------------------------------------- |
| **Standard**   | Dedicated **Neon Project** (per-Agency) + dedicated database + role | Dedicated KMS key; shared Neon org; autoscale compute quota  | Typical agencies                             |
| **Enterprise** | Dedicated Project + dedicated **compute endpoint** + role pool      | Dedicated KMS; dedicated compute endpoint; observable quotas | Large agencies, high data volume, strict SLA |
| **Regulated**  | Dedicated Project + **region-bound deployment** (own region / VPC)  | project-level dedicated key; BAA / DPA mandatory             | HIPAA · strict residency · contractual       |

**Key design principles:**

- **Cross-Agency data is physically unreachable**: queries across Agencies fail at the storage layer (not at app or row-filter)
- **Client-level isolation inside an Agency is logical (RLS)**: Clients of the same Agency share that Agency's database; `client_id` RLS limits visibility. **Cross-Agency benchmarking remains intact** (Super Admin can compare aggregate metrics across all Agencies)
- **Super Admin cross-Agency view**: only exposes secure aggregation views (cannot decrypt plaintext PII / PHI / business data)
- Tier upgrades (Standard → Enterprise → Regulated) executed via Neon branching for smooth zero-copy migration
- Per-Agency keys held independently → leakage of one Agency's key does not compromise others' encrypted data

### 4.2 Recommended Schemas

| Schema       | Purpose                                                                                 |
| ------------ | --------------------------------------------------------------------------------------- |
| `raw_secure` | References to encrypted PII files + restricted metadata (no plaintext sensitive fields) |
| `staging`    | Source-specific normalized tables                                                       |
| `canonical`  | Unified cross-platform entities                                                         |
| `marts`      | Reporting-ready tables (campaign / persona / attribution / portal)                      |
| `ai_context` | AI-safe summaries, embeddings, retrieved context, prompt citations                      |
| `audit`      | Data access, ELT runs, AI requests, compliance events                                   |

### 4.3 Canonical Entities

| Entity               | Notes                                        |
| -------------------- | -------------------------------------------- |
| `tenant`             | Tenant master (agency + config)              |
| `client`             | Brand / client of an agency                  |
| `data_source`        | Source registry (GA4 / Meta / Experian etc.) |
| `campaign`           | Cross-platform unified campaign              |
| `media_placement`    | Ad Group / Line Item abstraction             |
| `creative_asset`     | Creative asset (copy + image + video)        |
| `audience_segment`   | Audience segment (anonymized)                |
| `persona`            | Persona profile                              |
| `touchpoint`         | Touchpoint (impression / click / visit)      |
| `conversion_event`   | Conversion event                             |
| `attribution_result` | Attribution output                           |
| `report`             | Report instance                              |
| `audit_event`        | Audit event                                  |

### 4.4 Row-Level Security (Dual Role)

RLS plays **two distinct roles** in this physical-isolation architecture:

#### 4.4.1 Cross-Agency Protection (Defense-in-Depth)

Cross-Agency physical isolation already comes from dedicated databases; RLS is only an extra insurance layer:

- **Shared metadata / platform audit tables** (e.g. platform-level `audit_event`, `agency_directory`, `token_usage`): cross-Agency but only exposed to Super Admin via aggregation views
- **Standard-tier shared warehouse**: prevents misconfiguration causing cross-database queries
- **Compliance auditor queries**: auto-narrow via `agency_context`

#### 4.4.2 Within-Agency Client Isolation (Primary Use)

**This is the core use of RLS**: multiple Clients of the same Agency share that Agency's database. RLS ensures a Client Viewer only sees their own data.

**Neon Postgres implementation:**

```sql
-- Enable RLS on every fact / dim table inside the Agency database
ALTER TABLE marts.campaign_performance ENABLE ROW LEVEL SECURITY;

CREATE POLICY client_isolation ON marts.campaign_performance
  USING (
    current_setting('app.role') IN ('AGENCY_ADMIN', 'AGENCY_OPERATOR')  -- Agency roles see all
    OR client_id = current_setting('app.client_id')::uuid                 -- Client Viewer sees only own
  );
```

`app.role` and `app.client_id` are injected via `SET LOCAL` at the start of each Client Viewer transaction. **Three overlapping layers:**

1. **Agency physical isolation**: cross-Agency unreachable (dedicated database)
2. **Within-Agency Client RLS**: Client Viewer scoped to their `client_id` rows
3. **App layer**: API endpoints enforce `agency_id` + `client_id` checks

### 4.5 Zero-Copy Cloning

Use cases:

- **Tenant onboarding**: rapid replication of data model, empty schemas, sample config
- **Enterprise isolation replicas**: logical isolation for large customers
- **QA / UAT / regression**: production-like environments
- **Region migration / backup**: cost-effective replicas
- **Customer dispute replay**: compliance auditors review historical snapshots

> ⚠️ Zero-copy clone **does not replace compliant deletion**. PII/PHI data still follows retention, deletion, audit and key-destruction policies.

### 4.6 Per-Tenant Data Residency

Each tenant binds a **primary region** at onboarding (`us-east-1` / `eu-central-1` / `ap-southeast-1` / …). For that tenant:

- Raw Lake / Processed Lake physically reside in the bound region
- KMS keys and backups co-located
- AI inference picks the nearest LLM region (HIPAA + EU clients use AWS Bedrock in-region)
- Cross-region flow intercepted by **residency enforcer (DLP rule engine)**

EU / Canada / healthcare / government-adjacent tenants need separate region-locking evaluation.

---

## 5. ELT Pipeline (8 Steps)

```text
Extract            ┐
  → Classify        │  Pipeline (orchestrator: Dagster OSS / Apache Airflow — choose one)
  → Load            │
  → Transform in Warehouse (Neon Postgres)
       → Normalize  │
       → Deduplicate│
       → Validate   │  ← PHI Detector scans here
       → Enrich     │
       → Index      │
  → Audit (cross-cutting · INSERT-only · 6-year retention)
```

**ELT (not ETL)** because the warehouse (Neon Postgres) is a more scalable transform layer and raw / staging records remain auditable.

**Mapping to Network Diagram flow strips:**

- **Flow strip ① Extract** = §5.1
- **Flow strip ② Classify · Transform · Load** = §5.2–5.8 (7 of the 8 steps run inside the warehouse)
- **Cross-cutting Audit** = §5.9 orchestrator's asset materialization + audit_events table

### 5.1 Extract

API extraction (OAuth / API key / service account) + encrypted file intake (Tresorit / SFTP). Credentials stored in **Credential Vault** (per-tenant encrypted). Retry with exponential backoff.

### 5.2 Classify (PII/PHI routing)

- Auto-detect: HIPAA Safe Harbor 18 identifiers + GDPR PII fields
- Routing: PII/PHI → Raw PII Lake; non-PII → ELT staging directly
- Routing rationale explainable (which field hit which rule)

### 5.3 Load

Safe raw/staging data → warehouse (Neon Postgres); sensitive raw data → PII-segregated lake. Auditable batch ID + source fingerprint.

### 5.4 Normalize

Map source fields to unified canonical schema:

| Source                                                                 | Target Canonical Entity |
| ---------------------------------------------------------------------- | ----------------------- |
| Meta Campaign / TikTok Campaign / DV360 Insertion Order / TTD Campaign | `campaign`              |
| Meta Ad Set / TikTok Ad Group / DV360 Line Item / TTD Ad Group         | `media_placement`       |
| GA4 / Meta / DV360 / TTD conversions                                   | `conversion_event`      |

### 5.5 Deduplicate

Covers: API incremental dupes, file re-uploads, multi-report dupes, CRM cross-system dupes.

Strategy: source-native primary key + tenant-scoped external ID + hash fingerprint + ingestion batch ID + latest-write-wins / source-priority merge.

### 5.6 Validate

- Schema: types, required fields, value ranges
- Business rules: non-negative amounts, dates not in future, currency / timezone / platform enum recognized
- **PII/PHI leakage detection**: rejected when caught

Failed rows go to **quarantine queue**, never enter the main warehouse.

### 5.7 Enrich

- Campaign → client / brand mapping
- Geography, industry, audience-segment label completion
- GA4 conversion → media touchpoint attributable relations
- Third-party profiles (Experian / TransUnion / Nielsen) tied to anonymized audience keys
- Placer IQ / Quorum offline signals tied to market regions

### 5.8 Index

- Structured: `tenant_id` · `client_id` · `campaign_id` · `date` · `source_system`
- Semantic: persona narrative · creative brief · market research notes · campaign insight summary
- Vector: for RAG — **never stores plaintext PII**

### 5.9 Orchestration

**Primary orchestrator: choose one of Dagster OSS or Apache Airflow** (see [ELT-ORCHESTRATION-PRIORITY](../ELT-ORCHESTRATION-PRIORITY.md)). Both can run the platform's 8-step ELT pipeline; selection depends on team familiarity and project phase:

| Dimension           | 🟪 Dagster OSS                                | 🟦 Apache Airflow                            |
| ------------------- | --------------------------------------------- | -------------------------------------------- |
| **Data lineage**    | ✅ Native Asset Graph                         | 🟡 Needs OpenLineage add-on                  |
| **dbt first-class** | ✅ `dagster-dbt` (every model → asset)        | 🟡 `dbt-airflow` provider                    |
| **Multi-tenant**    | ✅ Partition Key = Agency                     | 🟡 DAG parameterization                      |
| **Connector eco**   | 🟡 ~300 integrations                          | ✅ 1000+ providers                           |
| **Learning curve**  | ⚠️ Asset mental model (1-2 weeks)             | ✅ Most widespread in industry               |
| **Compliance**      | ✅ Code Location per-region                   | ✅ Self-host any region                      |
| **Best fit**        | Lineage / multi-tenant / dbt-heavy / AI-trace | Team familiar / 1000+ connectors / DAG model |

> Full evaluation in [ELT-ORCHESTRATION-PRIORITY §4](../ELT-ORCHESTRATION-PRIORITY.md). On an optimal-only basis, Dagster OSS is recommended; if the team is already proficient with Airflow and native lineage is not yet required, Airflow can equally carry the platform's ELT.

**Auxiliary orchestrators**:

- **AWS Step Functions** — Only for AI write-back approval flows (Media Agent → Meta / DV360 / TikTok writes require human approval) and DSAR long flows (intake → PII Access Service → export → email delivery → client confirmation). Triggered by the primary orchestrator (Dagster / Airflow).
- **AWS Glue** — Only for large-volume backfill subtasks (GB+ historical data). Invoked by the primary orchestrator; never the primary scheduler.

**Scale-up path**: If Dagster OSS — when tenants ≥ 10 Agencies / team ≥ 8 → upgrade to **Dagster Cloud Hybrid** (cloud control plane + self-hosted compute, built-in RBAC / SSO / 6-year audit). If Airflow — upgrade to self-host HA cluster or MWAA.

Every step: **idempotent · resumable · rollback-capable · fully audited** (asset materialization / DAG run history + audit_events table).

---

## 6. Core AI Brain

### 6.1 Six Core Components

| Component                | Responsibility                                                                                           |
| ------------------------ | -------------------------------------------------------------------------------------------------------- |
| **Context Builder**      | Gathers tenant-safe / role-safe / PII-safe context from the warehouse (Neon Postgres) (no plaintext PII) |
| **LLM Router**           | Selects model by agent / cost / latency / compliance / tenant policy                                     |
| **Agent Orchestrator**   | Coordinates the 4 Pillar Agents, serial/parallel                                                         |
| **Tool Executor**        | Calls approved read/write tools; write-back operations require approval gates                            |
| **Memory & Retrieval**   | Uses summaries + vector retrieval; no raw PII                                                            |
| **Audit & Cost Control** | Logs prompts / outputs / tokens / data access / model decisions                                          |

### 6.2 LLM Router Strategy

- **Task matching**: Persona deep reasoning → Claude Opus; Creative / Attribution / Media → Claude Sonnet
- **Compliance routing**: HIPAA customers via AWS Bedrock direct + BAA (bypassing OpenRouter)
- **Cost / latency**: routed by token budget / latency / cost tier
- **Portability**: switchable between OpenAI / Anthropic / OpenRouter / enterprise-private models
- See [PSD-LLM-SELECTION-DECISION.en.md](../PSD-LLM-SELECTION-DECISION.en.md)

### 6.3 Four Pillar Agents

| Agent                 | Purpose                                                                                          | Primary Model            | Input                                   | Output                                                              |
| --------------------- | ------------------------------------------------------------------------------------------------ | ------------------------ | --------------------------------------- | ------------------------------------------------------------------- |
| **Persona Agent**     | Generate persona blueprint from market data, audience profile, 3rd-party audience signals        | Claude Opus 4.7 (1M ctx) | Canonical data + business goal          | Persona blueprint, demographic profile, vector embeddings           |
| **Creative Agent**    | Generate creative direction, copy, asset suggestions from brand, persona, historical performance | Claude Sonnet 4.6        | Brand voice + historical CTR + Persona  | Multi-variant copy (headline/body/CTA) + scores                     |
| **Attribution Agent** | Analyze touchpoints, conversion, media performance; produce attribution narrative + optimization | Claude Sonnet 4.6        | Touchpoints + conversion events         | Attribution weights, channel contribution, ROI ranking, explanation |
| **Media Agent**       | Read media performance, budget, pacing; propose or execute optimization (write-back gated)       | Claude Sonnet 4.6        | Budget, target audience, platform rates | Cross-platform allocation, bid recommendations, buying plan         |

### 6.4 Audit & Cost Control

- Every call's input / output / tokens / model / data access logged in `audit.ai_request`
- Token budget: per-tenant `monthly_token_budget`; HTTP 429 on exhaust
- Retries: 3 exponential backoff; 60s total timeout
- Langfuse: each call produces trace + score

---

## 7. Priority 1 Integrations

### 7.1 Data Providers / CRM / Market Signals

| Integration    | Category            | Purpose                                                                                  | Method                        | Priority Value                                                              |
| -------------- | ------------------- | ---------------------------------------------------------------------------------------- | ----------------------------- | --------------------------------------------------------------------------- |
| **Experian**   | Audience            | Mosaic, audience profile, demographics, psychographics                                   | File/API (contract-dependent) | Persona · market research core                                              |
| **TransUnion** | Audience            | Identity, audience, offline/online connection data                                       | API/file                      | Audience enhancement, matching, attribution                                 |
| **LiveRamp**   | Identity Resolution | RampID cross-device identity graph, 1st/2nd-party audience activation, match-rate uplift | API (bidirectional RampID)    | Cross-platform identity, audience activation                                |
| **HubSpot**    | CRM                 | Customer / Lead / Deal / Marketing automation data; CRM master source                    | OAuth + API (Hub API)         | Customer profile, lead-to-conversion attribution, marketing automation data |
| **Nielsen**    | Media Measurement   | Media consumption, audience measurement, market data                                     | API/file                      | Market sizing, media preference, benchmark                                  |
| **Placer IQ**  | Geo / Offline       | Location, store/area foot-traffic, offline behavior                                      | API/file export               | Offline behavior + geo insight                                              |
| **Quorum**     | Advocacy            | Political, community, geographic or audience signals                                     | API/file export               | Regional / audience insight                                                 |

### 7.2 Media / DSP Platforms

| Integration        | Purpose                                                         | Key Data                                                                                                 |
| ------------------ | --------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------- |
| **DV360**          | Google Display & Video 360                                      | Advertiser / Campaign / Insertion Order / Line Item / Creative / Spend / Impression / Click / Conversion |
| **Meta**           | Facebook / Instagram paid media + audience                      | Campaign / Ad Set / Ad / Insight / Pixel Event / Custom Audience                                         |
| **TikTok**         | TikTok Ads + creative performance                               | Advertiser / Campaign / Ad Group / Ad / Spend / Click / Conversion / Creative                            |
| **The Trade Desk** | Programmatic DSP + open web buying                              | Advertiser / Campaign / Ad Group / Creative / Bid / Spend / Conversion                                   |
| **StackAdapt**     | Multi-channel programmatic DSP (Display/Native/Video/CTV/Audio) | Advertiser / Campaign / Ad Group / Creative / Spend / Impression / Click / Conversion                    |
| **GA4**            | First-party web + app analytics                                 | Event / Session / User Property / Traffic Source / Conversion / Ecommerce                                |

### 7.3 Tresorit — Compliant CRM Transfer

For compliant CRM transfer and sensitive file exchange. In MVP, positioned as one of the secure ingestion paths into the **Raw PII-Segregated Lake**.

Applicable scenarios:

- Customer uploads CRM exports
- Uploads of audience files containing email / phone / customer lists
- Uploads of healthcare / regulated client data requiring compliant chain
- Secure alternative when client cannot provide API

---

## 8. Compliance & Data Residency

### 8.1 GDPR

- **DSAR**: access / delete / export / rectify / restrict — SLA ≤ **30 days**
- **Retention**: marketing 3y, financial 7y (strictest applicable)
- **Breach notification**: 72 hours to regulator
- **DPA**: signed with every data processor
- **EU customer data**: defaults to `eu-central-1` / `eu-west-1`

### 8.2 CCPA

- **DSAR SLA ≤ 45 days**
- **Opt-Out**: "Do Not Sell My Personal Information" visible in Client Portal
- **Sale tracking**: third-party disclosure logs

### 8.3 HIPAA

- **BAA** signed; status tracked
- **18 Safe Harbor identifiers** auto-detected and anonymized
- **Encryption**: AES-256 at rest + TLS 1.3 in transit
- **Session timeout**: 15 min idle
- **Audit log**: 6 years INSERT-only
- **Breach notification**: HHS in 60 days
- **LLM path**: AWS Bedrock + BAA bypass

### 8.4 SOC 2 Type II

| Principle            | Controls                                                       |
| -------------------- | -------------------------------------------------------------- |
| Security             | RBAC, MFA, key management, periodic pen-testing                |
| Availability         | SLO 99.9%, multi-AZ, DR drills                                 |
| Processing Integrity | Data integrity checks, change audit, transactional consistency |
| Confidentiality      | 4-level data classification, least privilege, encryption       |
| Privacy              | DSAR, retention, privacy notices, cookie management            |

Annual Type II audit; certificate provided to enterprise customers.

### 8.5 Per-Tenant Data Residency

See §4.6.

### 8.6 PII Segregation Boundary

See §3.3.

---

## 9. Auth & SSO Boundary

> MVP keeps basic auth + RBAC + tenant isolation + audit logging. Google / Office 365 SSO marked post-MVP.

| Capability                          | MVP | Post-MVP     |
| ----------------------------------- | --- | ------------ |
| Email/password + JWT                | ✓   | ✓ (fallback) |
| Google Workspace SSO                | —   | ✓            |
| Microsoft Office 365 / Entra ID SSO | —   | ✓            |
| SCIM provisioning                   | —   | ✓            |
| Enterprise SAML                     | —   | ✓            |
| RBAC + tenant isolation + audit     | ✓   | ✓            |
| MFA (via IdP)                       | —   | ✓            |

**SSO deferral must not sacrifice tenant isolation, permission boundaries, or audit.**

---

## 10. MVP Functional Pillars

| Pillar              | Description                                                                  | Primary Agent     | Key Data Sources                                            |
| ------------------- | ---------------------------------------------------------------------------- | ----------------- | ----------------------------------------------------------- |
| **Market Research** | Audience profile, market insight, competitive analysis, persona blueprint    | Persona Agent     | Experian / TransUnion / GA4 / Nielsen                       |
| **Creative Engine** | Creative copy and asset generation, A/B experiments, brand voice constraints | Creative Agent    | Brand voice + historical CTR                                |
| **Media Buying**    | Cross-platform budget allocation + buying strategy; write-back gated         | Media Agent       | DV360 / Meta / TikTok / Trade Desk / StackAdapt / Placer IQ |
| **Attribution**     | Cross-channel attribution + ROI analysis, narrative reports                  | Attribution Agent | GA4 / LiveRamp / all ad platforms                           |
| **Client Portal**   | White-labeled dashboard, AI summary, report access, role-filtered visibility | (no agent)        | Outputs of the four pillars above                           |

### 10.1 Portal User Types

**Three-level role hierarchy** (top-down: from broadest to narrowest visibility):

| Level           | User Type                           | Primary Experience                                                                     | Data Visibility                                                              |
| --------------- | ----------------------------------- | -------------------------------------------------------------------------------------- | ---------------------------------------------------------------------------- |
| **L1 Platform** | **Platform Super Admin** (internal) | Cross-Agency overview, Agency provisioning, platform health, billing & usage analytics | **Aggregates / metadata across all Agencies** (cannot decrypt business data) |
| **L2 Agency**   | **Agency Admin**                    | Agency settings, Client management, user management, integrations, audit               | **All Clients under that Agency** (full data)                                |
| **L2 Agency**   | **Agency Operator**                 | Daily campaign health, research, creative, media and attribution workflows             | All Clients under the Agency (scoped by business role)                       |
| **L3 Client**   | **Client Viewer**                   | White-labeled summaries, performance reports, approved insights                        | **Only their own Client data** (RLS-filtered inside the Agency DB)           |

**Key boundaries:**

- **Platform Super Admin** only sees cross-Agency **secure aggregation views** (active Agencies, total token usage, platform health). **Cannot query any Agency's plaintext business data** — per-Agency KMS keys are not exposed to platform super admins.
- **Agency Admin / Operator** has full authority across all Clients within their Agency's physical database.
- **Client Viewer** is constrained by `client_id` RLS inside the Agency database, seeing only their own subset.

---

## 11. MVP Technical Decision Summary

| Topic                   | Decision                                                                                                                                                                                                                                                                                                                |
| ----------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Data strategy           | Raw PII-Segregated Lake + Processed Lake                                                                                                                                                                                                                                                                                |
| Warehouse               | **Neon Postgres** (per-Agency project · serverless · Branching)                                                                                                                                                                                                                                                         |
| Isolation               | **Physical isolation at the Agency layer** (per-Agency Neon project + per-Agency KMS key); Enterprise adds dedicated compute endpoint; Regulated gets dedicated region. **Client-level isolation is RLS-only** (no per-Client physical DB → keeps cross-Agency benchmarking). RLS otherwise serves as defense-in-depth. |
| PII                     | Never in general processed warehouse, never in default AI prompts                                                                                                                                                                                                                                                       |
| ELT                     | extract → classify → load → normalize → dedup → validate → enrich → index                                                                                                                                                                                                                                               |
| AI                      | Core AI Brain (6 components) + LLM Router + 4 agents                                                                                                                                                                                                                                                                    |
| Agents                  | Persona · Creative · Attribution · Media                                                                                                                                                                                                                                                                                |
| Autonomy                | Human-in-the-loop (budgets / write-back must be human-approved)                                                                                                                                                                                                                                                         |
| Priority 1 integrations | Experian · TransUnion · LiveRamp · HubSpot · Nielsen · Placer IQ · Quorum · DV360 · Meta · TikTok · The Trade Desk · StackAdapt · GA4 · Tresorit                                                                                                                                                                        |
| Compliance              | GDPR · CCPA · HIPAA · SOC 2                                                                                                                                                                                                                                                                                             |
| Residency               | per-tenant requirement                                                                                                                                                                                                                                                                                                  |
| SSO                     | Google + Office 365 post-MVP                                                                                                                                                                                                                                                                                            |

---

## 12. MVP Implementation Sequence (10 Steps)

| #   | Phase                                | Content                                                                                |
| --- | ------------------------------------ | -------------------------------------------------------------------------------------- |
| 1   | **Foundation architecture**          | Tenant model, compliance boundary, canonical schema, Neon Postgres warehouse structure |
| 2   | **Secure ingestion**                 | Credential vault, file intake, Tresorit flow, API connector framework                  |
| 3   | **Priority read connectors**         | Experian sample · GA4 · Meta · DV360 · TikTok · The Trade Desk                         |
| 4   | **Processed Lake + marts**           | Campaign performance · audience/persona · attribution-ready tables                     |
| 5   | **Core AI Brain**                    | LLM Router · Context Builder · Audit · Token budget                                    |
| 6   | **Market Research pillar**           | Persona Agent + audience blueprint workflow                                            |
| 7   | **Attribution + Client Portal**      | Reports · AI summaries · white-labeled views                                           |
| 8   | **Creative + Media recommendations** | Agent-generated suggestions (read-only)                                                |
| 9   | **Write-back automation**            | Media actions with approval gates                                                      |
| 10  | **Enterprise Auth (post-MVP)**       | Google SSO · Office 365 SSO · SCIM / SAML                                              |

---

## 13. Technical Constraints

| Constraint                                                              | Impact                                                                       |
| ----------------------------------------------------------------------- | ---------------------------------------------------------------------------- |
| Unified canonical schema must lock early                                | Expensive to retrofit after integrations and agents are built                |
| PII segregation is architectural, not optional                          | Affects ingest, storage, AI context, audit and deletion workflows            |
| Warehouse RLS (Neon Postgres) must be designed before tenant data lands | Prevents cross-tenant leakage; supports enterprise readiness                 |
| Data residency is per-tenant                                            | Affects Neon project region, object storage, backups, model-provider routing |
| Source contracts may lag technical work                                 | Experian / TransUnion / Nielsen may require sample-file fallback             |
| Media platform write access may be delayed                              | MVP first supports read/reporting; write-back gated                          |
| GA4 / media historical data may need batch backfill                     | Onboarding expectations need clear lead-time communication                   |
| Tresorit is a secure transfer path, **not a normalized CRM schema**     | CRM file ingestion still needs mapping, validation and PII handling          |
| SSO is post-MVP                                                         | MVP must still include secure auth, RBAC, tenant isolation, audit            |
| AI cannot consume raw PII by default                                    | Requires AI-safe context builder + redaction / tokenization rules            |

---

## 14. Technical Dependencies

| Dependency                                                          | Required For                          | Priority                            |
| ------------------------------------------------------------------- | ------------------------------------- | ----------------------------------- |
| Tenant model + isolation policy                                     | All product pillars                   | **P0**                              |
| Canonical marketing schema                                          | ELT · reporting · AI agents           | **P0**                              |
| PII classification + routing                                        | Compliance · CRM transfer · AI safety | **P0**                              |
| Warehouse account / project · region · role design (Neon preferred) | Warehouse + data residency            | **P0**                              |
| Credential vault                                                    | All API integrations                  | **P0**                              |
| ELT orchestration + monitoring                                      | Integration & data freshness          | **P0**                              |
| Experian sample data                                                | Market Research MVP                   | **P0**                              |
| GA4 + media historical exports                                      | Attribution + onboarding demo         | **P0**                              |
| DV360 / Meta / TikTok / TTD API access                              | Media Buying + reporting              | **P0/P1** (depends on write access) |
| Tresorit transfer process                                           | Compliant CRM intake                  | **P0**                              |
| LLM provider decision                                               | Core AI Brain + cost control          | **P0**                              |
| Human approval workflow                                             | Media write-back, budget changes      | **P1**                              |
| Google / Office 365 SSO                                             | Enterprise auth                       | **Post-MVP**                        |


---

## 15. Key Constraints (input to prioritization tool)

| Category                | Constraint                                                                                                                                                                                                                                                                                                                                   |
| ----------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Data Residency**      | Per-tenant region binding; cross-region forbidden                                                                                                                                                                                                                                                                                            |
| **Encryption**          | AES-256 at rest; TLS 1.3 in transit; per-tenant KMS key                                                                                                                                                                                                                                                                                      |
| **Auth**                | MVP: JWT + basic auth. Post-MVP: Google + Office 365 SSO                                                                                                                                                                                                                                                                                     |
| **Compliance**          | GDPR / CCPA / HIPAA (with BAA) / SOC 2 Type II                                                                                                                                                                                                                                                                                               |
| **PII Boundary**        | Raw Lake closed to business/AI; Processed Lake anonymized; tokenized joins across boundary                                                                                                                                                                                                                                                   |
| **Multi-Tenant**        | **Agency-layer physical isolation** (Neon Postgres): per-Agency Neon project + per-Agency KMS key (baseline); Enterprise adds dedicated compute endpoint; Regulated gets dedicated region. **Client-level isolation is RLS-only** (no per-Client physical DB → preserves cross-Agency benchmarking). Neon Branching for replicas / migration |
| **PII Egress**          | Plaintext PII egresses only through the **PII Access Service** (purpose-bound · short-lived token · in-memory hashing · never enters Processed Lake / AI Brain) to Meta CA / DV360 / LiveRamp / DSAR responses. Inter-Lake boundary is **hard isolation** (independent storage clusters + independent KMS)                                   |
| **LLM Routing**         | OpenRouter default; HIPAA → AWS Bedrock BAA bypass                                                                                                                                                                                                                                                                                           |
| **Autonomy**            | Human-in-the-loop (budgets / write-back / pauses)                                                                                                                                                                                                                                                                                            |
| **Audit**               | INSERT-only; HIPAA 6y; GDPR financial 7y                                                                                                                                                                                                                                                                                                     |
| **DSAR SLA**            | GDPR 30d / CCPA 45d / HIPAA 30d                                                                                                                                                                                                                                                                                                              |
| **Breach Notification** | GDPR 72h / HIPAA 60d                                                                                                                                                                                                                                                                                                                         |
| **P1 Integrations**     | 14 sources: Experian · TransUnion · LiveRamp · HubSpot · Nielsen · Placer IQ · Quorum · DV360 · Meta · TikTok · The Trade Desk · StackAdapt · GA4 · Tresorit                                                                                                                                                                                 |
| **MVP Pillars**         | Market Research · Creative Engine · Media Buying · Attribution · Client Portal                                                                                                                                                                                                                                                               |
| **Canonical Schemas**   | 6: raw_secure · staging · canonical · marts · ai_context · audit                                                                                                                                                                                                                                                                             |
| **Canonical Entities**  | 13: tenant · client · data_source · campaign · media_placement · creative_asset · audience_segment · persona · touchpoint · conversion_event · attribution_result · report · audit_event                                                                                                                                                     |
