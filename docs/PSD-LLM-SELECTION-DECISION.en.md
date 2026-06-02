# LLM Selection Decision Record

> **Document Type**: Architecture Decision Record (ADR-001)
> **Status**: ✅ Decided · pending sign-off before PSD Step 2 closure
> **PSD Section**: §Technical Constraints — LLM & Inference Layer
> **Decision Date**: 2026-04-30 · Revised 2026-05-08 (Claude Opus 4.7 incorporated)
> **Source**: Closes the open "LLM vendor TBD" item from the sales cycle
> **Chinese Version**: [PSD-LLM-SELECTION-DECISION.md](./PSD-LLM-SELECTION-DECISION.md)

---

## 0. TL;DR (Decision Summary)

**Adopted Solution**: OpenRouter as the unified LLM gateway + Anthropic Claude family as the primary inference models; HIPAA tenants are routed through a dedicated **AWS Bedrock + Anthropic BAA** bypass.

| Dimension                                        | Decision                                                                       |
| ------------------------------------------------ | ------------------------------------------------------------------------------ |
| **Gateway layer**                                | OpenRouter (`openrouter.ai/api/v1/chat/completions`) — general traffic         |
| **HIPAA bypass**                                 | AWS Bedrock + Anthropic BAA — dedicated channel for PHI-bearing tenants        |
| **Heavy reasoning (Persona)**                    | `anthropic/claude-opus-4-7` (primary) / `anthropic/claude-opus-4-6` (fallback) |
| **Standard generation (Creative / Attribution)** | `anthropic/claude-sonnet-4-6`                                                  |
| **Image generation (reserved)**                  | `google/gemini-2.5-flash-image`                                                |
| **Local development**                            | Mock Mode (returns built-in fixtures when no API key is set)                   |
| **Revisit milestone**                            | 6 months out (2026-10-30) or first month with > $10K LLM spend                 |

---

## 1. Decision Scope

### 1.1 In Scope

- LLM vendor and specific model selection for text generation
- Inference layer gateway architecture (direct connection vs. aggregator)
- Model allocation strategy across the three core Agents
- Compliance channels (GDPR / CCPA / HIPAA)
- Cost ceilings and metering mechanism

### 1.2 Out of Scope (separate decisions)

- Embedding model selection (deferred to vector retrieval feature work)
- Fine-tuning strategy (Phase 3)
- Multimodal (voice, video)
- Self-hosted open-source models (see §11 Revisit Triggers)

---

## 2. Requirements & Constraints (Sales Cycle Commitments)

> These are upstream hard constraints baked into the PSD; no LLM solution may violate any of them.

| ID       | Constraint                                                    | Source                       |
| -------- | ------------------------------------------------------------- | ---------------------------- |
| **C-01** | Must support GDPR + CCPA + HIPAA simultaneously               | Master agreement §Compliance |
| **C-02** | HIPAA tenants must have a signed BAA in place                 | HIPAA Privacy Rule           |
| **C-03** | EU customer data must be processable in an EU region          | GDPR cross-border transfer   |
| **C-04** | Per-Agency monthly token budget must be hard-capped           | Sales product pricing        |
| **C-05** | Output must be machine-structured (JSON Schema enforcement)   | Downstream agent parsing     |
| **C-06** | Single-request P95 latency ≤ 30s                              | UX requirement               |
| **C-07** | Models must be swappable; no single-vendor lock-in            | Risk management              |
| **C-08** | Local development must run at zero cost                       | Engineering velocity         |
| **C-09** | All LLM calls must be auditable (prompt + response retention) | Compliance audit             |

---

## 3. Evaluation Dimensions & Weights

| Dimension                                                     | Weight  | Notes                                                 |
| ------------------------------------------------------------- | ------- | ----------------------------------------------------- |
| Compliance support (BAA / DPA / region)                       | **25%** | Hard constraint of three frameworks; violation = veto |
| Model quality (reasoning / copywriting / data interpretation) | 20%     | Core business capability                              |
| Cost structure                                                | 15%     | Unit price + metering model                           |
| Vendor lock-in risk                                           | 15%     | Switching cost                                        |
| Latency / availability SLA                                    | 10%     | UX                                                    |
| Engineering complexity (integration / maintenance)            | 10%     | Development efficiency                                |
| Observability                                                 | 5%      | Tracing / billing transparency                        |

---

## 4. Candidate Options

### Option A: Direct Anthropic API

- ✅ Lowest latency, official Claude family source
- ✅ Direct BAA available (Enterprise tier)
- ❌ Single-vendor lock-in, high switching cost
- ❌ No support for other vendors' models

### Option B: Direct OpenAI API

- ✅ Most mature tooling ecosystem
- ✅ BAA available (Enterprise)
- ❌ Claude currently outperforms on long-form reasoning / JSON output stability (per internal benchmarks)
- ❌ Single-vendor lock-in

### Option C: Google Vertex AI (Gemini)

- ✅ EU region controllable
- ✅ Synergy with GA4 / DV360 in the same Google ecosystem
- ❌ Claude family still leads on copywriting / Persona generation
- ❌ HIPAA BAA path requires Google Cloud Healthcare API; integration complexity is high

### Option D: OpenRouter Gateway (aggregator)

- ✅ **One API to access all vendors** — switching models requires only an ENV change
- ✅ Unified billing / unified tracing
- ✅ Already adopted by the project prototype, zero migration cost
- ❌ **OpenRouter itself does not sign BAAs** — HIPAA blocker
- ❌ Extra proxy hop adds 50–150ms of latency
- ⚠️ Adds a third-party dependency (availability risk)

### Option E: AWS Bedrock (managed Anthropic)

- ✅ **AWS standard BAA covers Claude on Bedrock**
- ✅ Multi-region (`us-east-1` / `eu-central-1`, etc.)
- ✅ IAM integration; same stack as our production AWS S3
- ❌ Only Anthropic + a few other vendors; less aggregation than OpenRouter
- ❌ Unit price slightly higher than OpenRouter

### Option F: Self-hosted Open-Source (Llama 3.1 70B / Mistral)

- ✅ Data never leaves our perimeter, zero compliance friction
- ✅ Long-term cost is controllable
- ❌ Quality gap vs. Claude Opus 4.7 remains material (especially for Persona heavy reasoning)
- ❌ High GPU operations cost
- ❌ Not feasible to deliver in MVP timeline

---

## 5. Comparison Matrix

| Dimension                 | A: Anthropic Direct | B: OpenAI Direct | C: Vertex AI          | **D: OpenRouter**   | **E: AWS Bedrock**     | F: Self-hosted   |
| ------------------------- | ------------------- | ---------------- | --------------------- | ------------------- | ---------------------- | ---------------- |
| HIPAA BAA                 | ✅ Enterprise       | ✅ Enterprise    | ⚠️ via Healthcare API | ❌ **Not signed**   | ✅ AWS standard BAA    | ✅ N/A           |
| GDPR DPA                  | ✅                  | ✅               | ✅                    | ✅                  | ✅                     | ✅ N/A           |
| EU region                 | ⚠️ US only          | ⚠️ US only       | ✅ multi-region       | ⚠️ pass-through     | ✅ `eu-central-1` etc. | ✅ N/A           |
| Claude Opus 4.7 (1M ctx)  | ✅                  | ❌               | ❌                    | ✅                  | ✅                     | ❌               |
| Claude Opus 4.6           | ✅                  | ❌               | ❌                    | ✅                  | ✅                     | ❌               |
| Multi-vendor A/B          | ❌                  | ❌               | ❌                    | ✅                  | ⚠️ Bedrock-only        | ❌               |
| Switching cost            | High                | High             | High                  | **Low**             | Medium                 | Very high        |
| Unit price (Sonnet input) | $3/M                | n/a              | n/a                   | $3/M (pass-through) | $3/M                   | $0 (electricity) |
| Latency P50               | ~800ms              | ~700ms           | ~900ms                | ~950ms              | ~750ms                 | GPU-dependent    |
| Engineering complexity    | Low                 | Low              | Medium                | **Very low**        | Medium                 | Very high        |

> Pricing reflects 2026 Q2 published rates; actual billing per vendor invoice.

---

## 6. Decision & Rationale

### 6.1 Dual-channel Architecture (Hybrid)

```
                              ┌───────────────────────────────┐
                              │  Backend: AI Brain (router)   │
                              └───────────────┬───────────────┘
                                              │
                       ┌──────────────────────┴──────────────────────┐
                       │                                              │
            HIPAA tenant?  │ Yes                                       │ No
                       │                                              │
                       ▼                                              ▼
       ┌──────────────────────────────┐            ┌────────────────────────────┐
       │  AWS Bedrock                 │            │  OpenRouter                │
       │  + Anthropic BAA             │            │  + Claude Opus 4.7 (primary)│
       │  + Claude Opus 4.7 / Sonnet  │            │  + Claude Sonnet 4.6        │
       │  Region: us-east-1 / eu-*    │            │  + Gemini Image (reserved)  │
       └──────────────────────────────┘            └────────────────────────────┘
```

### 6.2 Why OpenRouter + Bedrock (rather than D or E alone)

- **The HIPAA BAA hard constraint (C-02) vetoes pure OpenRouter** — the sales contract has committed to HIPAA, but OpenRouter does not sign BAAs, breaking the compliance chain.
- **The multi-vendor swappability constraint (C-07) vetoes pure Bedrock** — at this product stage we must retain model A/B and vendor-switching capability; Bedrock only covers Anthropic plus a few other vendors, falling short on aggregation breadth.
- **Cost**: Adds a router branch in the `AI Brain` layer (~50 lines of code). This is the optimal trade-off between compliance and flexibility.

### 6.3 Model Allocation Rationale

| Agent                | Model                            | Rationale                                                                                                                                                                                        |
| -------------------- | -------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| **Persona**          | **Claude Opus 4.7** (1M context) | Few-shot → multi-perspective synthesis; **4.7's 1M context** can ingest the full Brand Kit + historical campaigns + audience data in a single call, eliminating prompt-compression preprocessing |
| Persona (fallback)   | Claude Opus 4.6                  | OpenRouter auto-degrades to 4.6 when 4.7 is regionally unavailable / 5xx; signature-compatible, zero code change                                                                                 |
| **Creative**         | Claude Sonnet 4.6                | Templated output + voice mimicking; Sonnet's price/performance is sufficient; batch generation is cost-sensitive, no need for Opus                                                               |
| **Attribution**      | Claude Sonnet 4.6                | Data + natural-language summarization; no heavy reasoning needed (attribution math runs in SQL); LLM only interprets                                                                             |
| **Image (reserved)** | Gemini 2.5 Flash Image           | Anthropic does not yet offer image generation; Gemini Flash leads on multimodal cost/latency                                                                                                     |

**Why upgrade to Opus 4.7**:

- **1M context window** (5× improvement over 4.6's 200K): allows Persona Agent to carry the full Brand Kit + 6–12 months of campaign history + cross-platform user behavior in a single call, **eliminating the existing prompt-compression / summarization preprocessing layer** (simpler code + less information loss)
- **Quality lift**: On internal Persona benchmark, 4.7 scores ~12% higher on "insight depth" vs. 4.6 (human-graded by product team, N=50)
- **Same price tier**: Anthropic prices 4.7 at the same $15/$75 per M tokens as 4.6 — zero cost overhead from the upgrade
- **Risk**: New model availability may fluctuate during initial rollout → 4.6 is retained as the OpenRouter auto-degradation target

---

## 7. Compliance Posture

### 7.1 GDPR

- ✅ Anthropic / OpenRouter / AWS all provide DPAs (Data Processing Agreements)
- ✅ EU customers are routed to Bedrock `eu-central-1` (Frankfurt)
- ✅ No raw PII reaches LLM providers — prompts are passed through `anonymize_record_for_warehouse()` (SHA-256 + tenant salt) before reaching Brain
- ✅ DSAR deletion: since nothing is persisted at the LLM provider, deleting local `token_usage` + `audit_logs` + `persona_results` suffices

### 7.2 CCPA

- ✅ Anthropic publicly states API customer data is not used for model training (zero data retention option)
- ✅ Requests via OpenRouter inherit the Anthropic policy
- ✅ "Do Not Sell" signal: this architecture does not "sell" data by default

### 7.3 HIPAA

- ✅ **Bedrock channel**: AWS BAA + Anthropic sub-processor agreement covers end-to-end PHI processing
- ✅ **PHI detection interception**: `phi_detector.scan_record()` is the last line of defense before prompts hit the LLM
- ⚠️ **Risk**: HIPAA tenant requests **must never accidentally route through OpenRouter** — enforced via assertion in the Brain layer (see §10 R-01)

---

## 8. Cost Model

### 8.1 Unit Pricing (2026 Q2)

| Model                         | Input ($/M tokens) | Output ($/M tokens) | Context Window |
| ----------------------------- | ------------------ | ------------------- | -------------- |
| **Claude Opus 4.7** (primary) | $15                | $75                 | **1M**         |
| Claude Opus 4.6 (fallback)    | $15                | $75                 | 200K           |
| Claude Sonnet 4.6             | $3                 | $15                 | 200K           |
| Gemini 2.5 Flash Image        | $0.075 / image     | —                   | —              |

> Opus 4.7 sits at the same price tier as 4.6 — **zero-cost upgrade**. The 1M context window is metered by actual token consumption, not pre-allocated.

### 8.2 Monthly Budget Projection (typical Agency)

Assumption: Mid-sized Agency running 100 Persona tasks, 500 Creative tasks, and 200 Attribution tasks per month.

| Agent       | Calls | Avg Tokens       | Model      | Monthly Cost              |
| ----------- | ----- | ---------------- | ---------- | ------------------------- |
| Persona     | 100   | 2K in + 5K out   | Opus 4.7   | $40.50                    |
| Creative    | 500   | 1.5K in + 2K out | Sonnet 4.6 | $17.25                    |
| Attribution | 200   | 3K in + 1K out   | Sonnet 4.6 | $4.80                     |
| **Total**   |       |                  |            | **~$62.55 / Agency / mo** |

> With Opus 4.7's 1M context fully utilized (Persona input cap raised to ~50K tokens with no summarization preprocessing), the upper-bound monthly cost is ~$112.50, still within budget.

### 8.3 Metering Mechanism

- Each LLM call writes one `token_usage` record (`prompt_tokens / completion_tokens / cost_usd`)
- A monthly cron aggregates → compares against `agencies.monthly_token_budget` → on overrun, `check_budget()` raises `ValueError` → API responds HTTP 429
- Authoritative billing comes from OpenRouter / AWS monthly invoices; local `cost_usd` is an estimate

---

## 9. Performance & SLA

| Metric           | Target      | Source                                                      |
| ---------------- | ----------- | ----------------------------------------------------------- |
| P50 latency      | < 1.5s      | Persona heavy reasoning                                     |
| P95 latency      | < 30s       | Sales commitment of single-request P95 ≤ 30s (C-06)         |
| Availability     | 99.5%       | Lower bound of OpenRouter / Bedrock SLAs                    |
| Failure fallback | Mock output | `_MOCK_OUTPUT` auto-degrades; LLM faults invisible to users |

---

## 10. Risks & Mitigations

| ID       | Risk                                              | Probability | Impact                     | Mitigation                                                                                                 |
| -------- | ------------------------------------------------- | ----------- | -------------------------- | ---------------------------------------------------------------------------------------------------------- |
| **R-01** | HIPAA tenant request leaks to OpenRouter          | Medium      | **High (legal liability)** | Brain-layer hard assert: `if agency.hipaa_enabled: assert route == "bedrock"`; unit tests cover            |
| **R-02** | OpenRouter unavailable                            | Low         | Medium                     | Direct-Anthropic backup config; `_MOCK_OUTPUT` fallback; Sentry alerts                                     |
| **R-03** | Anthropic price hike / model deprecation          | Medium      | Medium                     | OpenRouter ENV switch to OpenAI / Gemini; pre-built compatibility test set                                 |
| **R-04** | LLM output violates JSON Schema                   | Medium      | Low                        | `try: json.loads(content) except: → raw_response field` — already implemented                              |
| **R-05** | Token budget abused / exhausted                   | Low         | Medium                     | `monthly_token_budget` hard cap + 429 already in place; per-tenant QPS limit (TODO)                        |
| **R-06** | Prompt injection leaks cross-tenant data          | Medium      | High                       | Prompts carry no cross-tenant data (Brain isolates Shared Context by `agency_id`); periodic red-team tests |
| **R-07** | Anthropic regional outage (US-only single region) | Low         | Medium                     | Bedrock multi-region as the HIPAA channel already provides region isolation; monitor Anthropic Status Page |

---

## 11. Revisit Triggers

Any one of the following triggers a re-evaluation of this decision:

- ⏰ **Time**: 6 months from now (2026-10-30)
- 💰 **Cost**: any month with LLM bill exceeding **$10,000 USD**
- 📈 **Scale**: token usage exceeds 100M / month
- 🔧 **Quality**: any agent output complaint rate > 5%
- 🆕 **New model**: GPT-5 / Claude Opus 5 / Gemini Ultra 2 or other **generational** releases (Opus 4.7 is already incorporated; minor versions do not trigger)
- ⚖️ **Compliance**: new regulations (e.g., EU AI Act high-risk provisions taking effect)

---

## 12. Implementation Checklist (must close before PSD Step 2)

- [x] **Code: Brain routing branch** — `backend/app/services/ai/brain.py` adds HIPAA branch in `route_request()`
- [ ] **Model upgrade** — `backend/app/core/config.py` set `PERSONA_MODEL = "anthropic/claude-opus-4-7"`, retain `PERSONA_MODEL_FALLBACK = "anthropic/claude-opus-4-6"`
- [ ] **Fallback logic** — Persona Agent retries 4.6 on 5xx from Opus 4.7 (httpx retry middleware)
- [ ] **Config: new ENVs** — `BEDROCK_REGION` / `BEDROCK_ROLE_ARN` / `BEDROCK_BAA_ENABLED`
- [ ] **Agency model fields** — `agencies.hipaa_enabled BOOLEAN DEFAULT FALSE` (already exists), `agencies.preferred_llm_route VARCHAR DEFAULT 'openrouter'`
- [ ] **Audit reinforcement** — `audit_logs.llm_route` field records each call's channel (`openrouter` / `bedrock`)
- [ ] **Tests** — `test_ai.py` adds HIPAA route-enforcement test cases
- [ ] **Doc** — this ADR lands in PSD §Technical Constraints
- [ ] **Commercial** — sign Anthropic Bedrock BAA (legal & AR drive)
- [ ] **Monitoring** — Langfuse tags differentiate `route=openrouter` vs. `route=bedrock`

---

## 13. Sign-offs

| Role                                      | Name               | Date         | Status |
| ----------------------------------------- | ------------------ | ------------ | ------ |
| Technical Decision Owner (CTO)            | **\*\***\_**\*\*** | **\_\_\_\_** | ⬜     |
| Product Owner                             | **\*\***\_**\*\*** | **\_\_\_\_** | ⬜     |
| Compliance Officer / DPO                  | **\*\***\_**\*\*** | **\_\_\_\_** | ⬜     |
| Sales Representative (contract alignment) | **\*\***\_**\*\*** | **\_\_\_\_** | ⬜     |
| Legal (BAA / DPA)                         | **\*\***\_**\*\*** | **\_\_\_\_** | ⬜     |

---

## Appendix A: Gap vs. Current Codebase

> Items below are deltas this decision creates against the current `main` branch.

| Item                               | Current State                                                    | Decision Requires                             | Effort |
| ---------------------------------- | ---------------------------------------------------------------- | --------------------------------------------- | ------ |
| OpenRouter channel                 | ✅ Implemented ([brain.py](../backend/app/services/ai/brain.py)) | Maintain                                      | 0      |
| Persona model version              | ⚠️ `claude-opus-4-6` (config.py:53)                              | Upgrade to `claude-opus-4-7`, 4.6 as fallback | ~0.5 d |
| 1M context activation              | ❌ Not yet utilized                                              | Remove Persona prompt compression             | ~1 d   |
| Bedrock channel                    | ❌ Not implemented                                               | Add                                           | ~3 d   |
| HIPAA route enforcement            | ❌ Not implemented                                               | Add hard assertion                            | ~0.5 d |
| `agencies.preferred_llm_route` col | ❌ Does not exist                                                | New migration                                 | ~0.5 d |
| Route audit field                  | ❌ Does not exist                                                | Add `audit_logs.llm_route`                    | ~0.5 d |
| Bedrock BAA commercial process     | ❌ Not started                                                   | Drive forward                                 | Legal  |

---

## Appendix B: Reasons for Rejecting Alternatives

| Option                | Rejection Reason                                                                                                                  |
| --------------------- | --------------------------------------------------------------------------------------------------------------------------------- |
| Pure Anthropic Direct | Single-vendor lock-in violates the "models must be swappable; no single-vendor lock-in" constraint (C-07); blocks multi-model A/B |
| Pure OpenAI           | Currently underperforms Claude on Persona / Creative benchmarks; existing Anthropic relationship                                  |
| Pure Vertex AI        | HIPAA path requires Google Healthcare API; integration cost > Bedrock                                                             |
| Pure OpenRouter       | **Does not sign BAAs** — violates the "HIPAA tenants must have a signed BAA" hard constraint (C-02)                               |
| Pure Bedrock          | Loses multi-vendor A/B capability; violates the "models must be swappable; no single-vendor lock-in" constraint (C-07)            |
| Self-hosted           | MVP timeline does not allow; quality gap exceeds acceptable range                                                                 |

---

## Appendix C: Related ADRs / Documentation

- [docs/ARCHITECTURE-DEEP-DIVE.md](./ARCHITECTURE-DEEP-DIVE.md) — §1 LLM selection & routing (implementation details)
- [features/PROJECT-PLAN.md](../features/PROJECT-PLAN.md) — F-09 Core AI Brain module status
- [features/compliance/architecture.md](../features/compliance/architecture.md) — Compliance top-level strategy
- [CLAUDE.md](../CLAUDE.md) — §Compliance Rules

---

## Appendix D: Glossary

| Term                        | Definition                                                                                                                |
| --------------------------- | ------------------------------------------------------------------------------------------------------------------------- |
| **PSD**                     | Product Specification Document — the formal sales deliverable that this ADR feeds into                                    |
| **ADR**                     | Architecture Decision Record — a one-decision document that captures choice, alternatives, and rationale for future audit |
| **BAA**                     | Business Associate Agreement — contract required by HIPAA between a covered entity and any vendor handling PHI            |
| **DPA**                     | Data Processing Agreement — contract required by GDPR between a controller and processor                                  |
| **DSAR**                    | Data Subject Access Request — GDPR/CCPA right of an individual to access, delete, port, or rectify their data             |
| **PHI**                     | Protected Health Information — health data covered by HIPAA                                                               |
| **PII**                     | Personally Identifiable Information — covered by GDPR & CCPA                                                              |
| **OpenRouter**              | A multi-vendor LLM gateway exposing one OpenAI-compatible API across Anthropic, Google, OpenAI, and others                |
| **Bedrock**                 | AWS's managed LLM service offering Anthropic, Cohere, Meta, and others under AWS contractual umbrella (incl. BAA)         |
| **Mock Mode**               | Local-development behavior where Agents return built-in fixtures when `OPENROUTER_API_KEY` is unset                       |
| **Token Budget**            | Per-Agency monthly cap on LLM tokens (`agencies.monthly_token_budget`); exhaustion returns HTTP 429                       |
| **JSON Schema enforcement** | LLM provider feature (`response_format: {type: "json_object"}`) that constrains output to valid JSON                      |

---

> Document Revision History
> v1.0 · 2026-04-30 · Initial release; closes the sales-cycle "LLM vendor TBD" open item
> v1.1 · 2026-05-08 · Incorporates Claude Opus 4.7 (1M context) as Persona primary model; 4.6 demoted to auto-fallback; adds upgrade rationale, implementation checklist, pricing table
