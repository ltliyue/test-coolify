# ReceptivIQ PSD — Technical Solution Bundle

> Product Specification Document (PSD) — Technical deliverables bundle
> 产品规格说明书 — 技术交付物合集

This directory contains the three foundational technical artifacts that feed directly into the ReceptivIQ Product Specification Document (PSD). Together they describe the agreed architectural approach, illustrate end-to-end data flow, and document the platform's compliance posture.

本目录包含三件支撑 ReceptivIQ 产品规格说明书（PSD）的核心技术交付物：技术方案描述、网络数据流图、平台架构示意图。

---

## Deliverables / 交付物

### 1. Technical Solution Description / 技术方案描述

| File / 文件                                              | Language |
| -------------------------------------------------------- | -------- |
| [`technical-solution.md`](./technical-solution.md)       | 中文     |
| [`technical-solution-en.md`](./technical-solution-en.md) | English  |

**Covers / 涵盖**：

- Two-Lake Data Strategy (Raw PII-Segregated Lake + Processed Lake)
- Snowflake multi-tenant warehouse (RLS + Zero-Copy Cloning + Data Residency)
- ELT pipeline (Extract → Classify → Load → Normalize → Deduplicate → Validate → Enrich → Index)
- Core AI Brain (LLM Router + 4 Pillar Agents: Persona / Creative / Attribution / Media)
- Priority 1 Integrations (14 P1 + extensible via +More): Experian · TransUnion · LiveRamp · HubSpot · Nielsen · Placer IQ · Quorum · DV360 · Meta · TikTok · The Trade Desk · StackAdapt · GA4 · Tresorit
- Compliance posture (GDPR / CCPA / HIPAA / SOC 2 + per-tenant data residency)
- Auth & SSO (Google + Office 365, post-MVP)
- MVP Functional Pillars (Market Research / Creative Engine / Media Buying / Attribution / Client Portal)

### 2. Network Diagram / 网络数据流图

| File / 文件                                                                               | Format  |
| ----------------------------------------------------------------------------------------- | ------- |
| [`network-diagram.svg`](./network-diagram.svg) · [`.png`](./network-diagram.png)          | 中文    |
| [`network-diagram-en.svg`](./network-diagram-en.svg) · [`.png`](./network-diagram-en.png) | English |

**Illustrates / 图示**：External Sources → ELT Pipeline → Two-Lake Warehouse → Core AI Brain → Pillar Agents → Application/Portal — including the compliance boundary and PII segregation zone.

Generator scripts: `docs/diagrams/psd-network-diagram.py` (CN) · `psd-network-diagram-en.py` (EN)

### 3. Architecture Solution Schema / 平台架构示意图

| File / 文件                                                                                           | Format  |
| ----------------------------------------------------------------------------------------------------- | ------- |
| [`architecture-schema.svg`](./architecture-schema.svg) · [`.png`](./architecture-schema.png)          | 中文    |
| [`architecture-schema-en.svg`](./architecture-schema-en.svg) · [`.png`](./architecture-schema-en.png) | English |

**Illustrates / 图示**：Full platform schema — 7-layer end-to-end view from data sources up to client portal, with technical constraints, dependencies, and a cross-cutting Compliance panel on the right.

Generator scripts: `docs/diagrams/psd-architecture-schema.py` (CN) · `psd-architecture-schema-en.py` (EN)

---

## Related Documents / 关联文档

- [`../PSD-LLM-SELECTION-DECISION.md`](../PSD-LLM-SELECTION-DECISION.md) — LLM selection rationale (OpenRouter + Claude family)
- [`../ADR-002-NEON-TENANCY-OPTIMAL.md`](../ADR-002-NEON-TENANCY-OPTIMAL.md) — Database-per-tenant strategy (catalog DB + Bytebase + PeerDB)
- [`../ADR-003-DAGSTER-VS-AIRFLOW.md`](../ADR-003-DAGSTER-VS-AIRFLOW.md) — Orchestration engine selection
- [`../ARCHITECTURE-DIAGRAM.md`](../ARCHITECTURE-DIAGRAM.md) — System architecture (Mermaid views)
- [`../diagrams/dev-stack-layered.md`](../diagrams/dev-stack-layered.md) — Layered stack reference

---

## Regenerating Diagrams / 重新生成图

```bash
cd docs/diagrams
python3 psd-network-diagram.py         # → docs/psd/network-diagram.{svg,png}
python3 psd-network-diagram-en.py      # → docs/psd/network-diagram-en.{svg,png}
python3 psd-architecture-schema.py     # → docs/psd/architecture-schema.{svg,png}
python3 psd-architecture-schema-en.py  # → docs/psd/architecture-schema-en.{svg,png}
```

Requirements: Python 3.9+, `rsvg-convert` (or fallback to `inkscape` / `imagemagick`) for PNG conversion.
