# ReceptivIQ Technical Solution Package

## 1. Solution Overview

ReceptivIQ is an AI-native marketing operating platform for agencies and their brand clients. The platform unifies market research, creative generation, media buying, attribution, and client portal experiences on top of a compliant, secure, and scalable data and AI architecture.

The agreed technical direction is:

- Two-lake data strategy: Raw PII-Segregated Lake + Processed Lake.
- Snowflake as the core analytical warehouse.
- ELT: extract and load first, then transform inside Snowflake.
- Core AI Brain as the unified AI orchestration layer.
- Persona, Creative, Attribution, and Media agents coordinated through the Core AI Brain.
- Compliance posture covering GDPR, CCPA, HIPAA, and SOC 2.
- Data residency flagged as a per-tenant requirement.
- Google and Office365 SSO are post-MVP.

## 2. Two-Lake Data Strategy

| Data Zone | Purpose | Typical Data | Access Principle |
| --- | --- | --- | --- |
| Raw PII-Segregated Lake | Isolated raw sensitive-data zone | CRM files, email, phone, customer lists, PHI, regulated identity fields | Tenant-level keys, least privilege, strong audit |
| Processed Lake | Standardized analytical data zone | Anonymized audiences, ad metrics, GA4 events, attribution outputs, persona insights | Reporting, AI retrieval, analytics |

PII/PHI is routed to the isolated path at ingestion time. It does not directly enter the general processed lake and is not included in AI prompts by default. Analytical joins are supported through tenant-scoped hashed identifiers or tokenized join keys.

## 3. Snowflake Data Warehouse

Snowflake hosts processed data, canonical schemas, semantic layers, AI retrieval indexes, and reporting marts.

Recommended isolation model:

| Tenant Tier | Isolation Model | Use Case |
| --- | --- | --- |
| Standard | Shared account with tenant_id + row-level security | Standard SaaS tenants |
| Enterprise | Dedicated database/schema, role, and warehouse | Enterprise tenants |
| Regulated | Dedicated Snowflake account or region-bound deployment | HIPAA, strict residency, regulated clients |

Snowflake zero-copy cloning is used for:

- New tenant onboarding.
- Enterprise tenant replication.
- QA/UAT environments.
- Tenant replication, region migration preparation, and regression testing.

## 4. ELT Pipeline

This architecture should use ELT. Snowflake is the scalable transformation layer, while auditable raw/staging records remain available for replay and governance.

Standard flow:

```text
Extract
  -> Classify
  -> Load
  -> Transform in Snowflake
      -> Normalize
      -> Deduplicate
      -> Validate
      -> Enrich
      -> Index
  -> Audit
```

Key transformations:

- Normalize: unify fields from DV360, Meta, TikTok, The Trade Desk, GA4, and other sources.
- Deduplicate: handle duplicate API pages, repeated file uploads, and repeated report exports.
- Validate: enforce required fields, types, enums, time windows, and PII/PHI safety.
- Enrich: add tenant/client mappings, geography, industry, audience labels, and attribution relationships.
- Index: build structured indexes, semantic indexes, and AI retrieval indexes.

## 5. Core AI Brain

The Core AI Brain is the platform's intelligence control layer.

| Component | Responsibility |
| --- | --- |
| Context Builder | Retrieves tenant-safe, role-safe, PII-safe context from Snowflake |
| LLM Router | Selects models based on task type, cost, latency, and compliance policy |
| Agent Orchestrator | Coordinates Persona, Creative, Attribution, and Media agents |
| Tool Executor | Executes approved tools; external write-back requires human approval |
| Audit and Budget | Logs prompts, models, tokens, data access, and outputs |

MVP should use a human-in-the-loop model. AI can generate recommendations and executable payloads, but budget changes, ad pauses, campaign launches, and external platform write-back require human confirmation.

## 6. Agents

| Agent | Role |
| --- | --- |
| Persona Agent | Generates audience blueprints, market insights, and persona profiles |
| Creative Agent | Generates creative direction, copy, and brand voice recommendations |
| Attribution Agent | Analyzes touchpoints, conversions, channel contribution, and optimization opportunities |
| Media Agent | Monitors media performance and pacing, then recommends optimizations |

## 7. Priority 1 Integrations

| Integration | Type | Main Use |
| --- | --- | --- |
| Experian | Data provider | Mosaic, persona data, demographics, psychographics |
| TransUnion | Data provider | Audience enrichment, identity linkage, offline-to-online matching |
| Nielsen | Data provider | Media consumption, audience measurement, market benchmarks |
| Placer IQ | Location and offline signals | Geography, foot traffic, regional behavior |
| Quorum | Regional/audience signals | Regional insight, community signals, market research |
| DV360 | DSP | Campaigns, insertion orders, line items, creatives, reporting |
| Meta | Paid media | Campaigns, ad sets, ads, insights, pixel events |
| TikTok | Paid media | Campaigns, ad groups, ads, creative performance |
| The Trade Desk | DSP | Programmatic campaigns, bids, spend, conversions |
| GA4 | Analytics | Events, sessions, traffic sources, conversions, ecommerce |
| Tresorit | Compliant file transfer | CRM files, customer lists, sensitive file intake |

## 8. Compliance Posture

| Compliance Domain | Requirement |
| --- | --- |
| GDPR | Data minimization, DSAR, deletion, restriction of processing, residency |
| CCPA | Do Not Sell/Share, consumer access and deletion, data classification |
| HIPAA | PHI segregation, minimum necessary access, audit, session timeout, BAA |
| SOC 2 | Access controls, logging, monitoring, change management, vendor management |

Data residency is a per-tenant requirement. During tenant onboarding, region requirements must be captured and used to determine Snowflake region, object storage region, backup region, and model-processing region.

## 9. MVP Functional Pillars

| Pillar | MVP Role |
| --- | --- |
| Market Research | Audience research, persona blueprints, market insights |
| Creative Engine | Creative concepts, copy variants, brand voice recommendations |
| Media Buying | Media performance monitoring, pacing, optimization recommendations |
| Attribution | Multi-touch attribution, channel contribution, reporting narratives |
| Client Portal | White-labeled dashboards, AI summaries, report access, role-filtered visibility |

## 10. Key Dependencies

| Dependency | Impact |
| --- | --- |
| Canonical schema | Foundation for integrations, reporting, and AI agents |
| Tenant isolation | Multi-tenant safety, RLS, permissions, compliance |
| PII segregation | CRM transfer, AI safety, DSAR, HIPAA |
| Snowflake role/region design | Residency, enterprise isolation, RLS |
| Credential vault | Required by all API integrations |
| ELT orchestration | Data freshness, retry, monitoring |
| LLM provider decision | Model routing, cost, compliance restrictions |
| Media write access | Determines whether Media Agent can execute write-back |
| SSO | Post-MVP: Google and Office365 |

## 11. Recommended MVP Sequence

1. Foundation: tenant model, PII boundary, canonical schema, Snowflake structure.
2. Secure ingestion: credential vault, Tresorit, API connector framework.
3. Priority read connectors: Experian, GA4, Meta, DV360, TikTok, The Trade Desk.
4. Processed lake and marts: campaign, audience, attribution, portal tables.
5. Core AI Brain: LLM router, context builder, audit, token budget.
6. Market Research: Persona Agent and audience blueprint workflow.
7. Attribution + Client Portal.
8. Creative + Media recommendations.
9. Human-approved write-back automation.
10. Google / Office365 SSO.
