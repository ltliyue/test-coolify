# LLM Selection Decision Record

> **文档类型**:Architecture Decision Record(ADR-001)
> **状态**:✅ Decided · 待 PSD Step 2 关闭前签署
> **PSD 章节**:§Technical Constraints — LLM & Inference Layer
> **决策日期**:2026-04-30 · 2026-05-08 修订(纳入 Claude Opus 4.7)
> **来源**:关闭销售周期遗留的"LLM 厂商未定"开放项

---

## 0. TL;DR(决策摘要)

**采纳方案**:OpenRouter 作为统一 LLM 网关 + Anthropic Claude 家族作为主力推理模型;HIPAA 客户走 **AWS Bedrock 直连 + BAA** 旁路。

| 维度                                 | 决策                                                               |
| ------------------------------------ | ------------------------------------------------------------------ |
| **网关层**                           | OpenRouter(`openrouter.ai/api/v1/chat/completions`) — 通用流量     |
| **HIPAA 旁路**                       | AWS Bedrock + Anthropic BAA — 涉 PHI 客户专用通道                  |
| **重推理(Persona)**                  | `anthropic/claude-opus-4-7`(主)/ `anthropic/claude-opus-4-6`(兜底) |
| **常规生成(Creative / Attribution)** | `anthropic/claude-sonnet-4-6`                                      |
| **图像生成(预留)**                   | `google/gemini-2.5-flash-image`                                    |
| **本地开发**                         | Mock Mode(无 API Key 时返回内置假数据)                             |
| **复盘节点**                         | 6 个月后(2026-10-30)或月度账单超 $10K 时触发                       |

---

## 1. 决策范围

### 1.1 In Scope

- 文本生成 LLM 的厂商与具体模型选型
- 推理层网关架构(直连 vs. 聚合网关)
- 三个核心 Agent 的模型分配策略
- 合规通道(GDPR/CCPA/HIPAA)
- 成本上限与计费机制

### 1.2 Out of Scope(另行决策)

- Embedding 模型选型(留给后续向量检索功能)
- 微调 / Fine-tuning 策略(Phase 3)
- 多模态(语音、视频)
- 自托管开源模型(见 §11 复盘触发器)

---

## 2. 需求与约束(销售周期承诺)

> 这些是 PSD 上游必须满足的硬约束,任何 LLM 方案不能违反。

| ID       | 约束                                        | 来源               |
| -------- | ------------------------------------------- | ------------------ |
| **C-01** | 必须同时支持 GDPR + CCPA + HIPAA 三法规     | 主合同 §合规条款   |
| **C-02** | HIPAA 客户必须有签署 BAA                    | HIPAA Privacy Rule |
| **C-03** | EU 客户数据必须可选 EU 区域处理             | GDPR 跨境传输      |
| **C-04** | 每 Agency 月度 Token 预算可硬上限           | 销售产品定价       |
| **C-05** | 输出必须可结构化(JSON Schema 强制)          | 下游 Agent 解析    |
| **C-06** | 单次请求 P95 延迟 ≤ 30s                     | UX 要求            |
| **C-07** | 模型可切换,不锁定单一厂商                   | 风险管理           |
| **C-08** | 本地开发可零成本运行                        | 工程效率           |
| **C-09** | 所有 LLM 调用可审计(prompt + response 留痕) | 合规审计           |

---

## 3. 评估维度与权重

| 维度                             | 权重    | 说明                    |
| -------------------------------- | ------- | ----------------------- |
| 合规支持(BAA / DPA / 区域)       | **25%** | 三法规硬约束,违反即否决 |
| 模型质量(推理 / 文案 / 数据解读) | 20%     | 业务核心能力            |
| 成本结构                         | 15%     | 单价 + 计费方式         |
| 厂商锁定风险                     | 15%     | 切换成本                |
| 延迟 / 可用性 SLA                | 10%     | UX                      |
| 工程复杂度(集成 / 维护)          | 10%     | 开发效率                |
| 可观测性                         | 5%      | tracing / 计费透明      |

---

## 4. 候选方案

### 方案 A:直连 Anthropic API

- ✅ 最低延迟,Claude 家族官方源
- ✅ 直接 BAA(Enterprise tier)
- ❌ 单一厂商绑定,切换成本高
- ❌ 不支持其他厂商模型

### 方案 B:直连 OpenAI API

- ✅ 工具生态最成熟
- ✅ BAA 可用(Enterprise)
- ❌ Claude 在长文推理 / JSON 输出稳定性上现阶段更优(项目已有内部基准)
- ❌ 单一厂商绑定

### 方案 C:Google Vertex AI(Gemini)

- ✅ EU 区域可控
- ✅ 与 GA4 / DV360 同生态有协同
- ❌ Claude 系列在文案 / Persona 生成上仍领先
- ❌ HIPAA BAA 需通过 Google Cloud Healthcare API,集成复杂

### 方案 D:OpenRouter 网关(聚合)

- ✅ **一套 API 接所有厂商**,切模型只改 ENV
- ✅ 统一计费 / 统一 tracing
- ✅ 已被项目原型采纳,迁移成本零
- ❌ **OpenRouter 本身不签 BAA** — HIPAA 阻塞
- ❌ 多一跳代理,延迟 +50~150ms
- ⚠️ 增加一个第三方依赖(可用性风险)

### 方案 E:AWS Bedrock(托管 Anthropic)

- ✅ **AWS 标准 BAA 涵盖 Bedrock 上的 Claude**
- ✅ 区域多(`us-east-1` / `eu-central-1` 等)
- ✅ IAM 集成,与 S3/MinIO 替代品 AWS S3 同栈
- ❌ 仅 Anthropic + 少量厂商,聚合度不如 OpenRouter
- ❌ 单价高于 OpenRouter

### 方案 F:自托管开源模型(Llama 3.1 70B / Mistral)

- ✅ 数据完全不出本地,合规零摩擦
- ✅ 长期成本可控
- ❌ 质量距离 Claude Opus 4.7 仍有差距(尤其 Persona 重推理)
- ❌ GPU 运维成本高
- ❌ MVP 阶段交付不现实

---

## 5. 比较矩阵

| 维度                    | A: Anthropic 直连 | B: OpenAI 直连 | C: Vertex AI         | **D: OpenRouter** | **E: AWS Bedrock**   | F: 自托管 |
| ----------------------- | ----------------- | -------------- | -------------------- | ----------------- | -------------------- | --------- |
| HIPAA BAA               | ✅ Enterprise     | ✅ Enterprise  | ⚠️ 需 Healthcare API | ❌ **不签**       | ✅ AWS 标准 BAA      | ✅ N/A    |
| GDPR DPA                | ✅                | ✅             | ✅                   | ✅                | ✅                   | ✅ N/A    |
| EU 区域                 | ⚠️ 仅 US          | ⚠️ 仅 US       | ✅ 多区域            | ⚠️ 透传           | ✅ `eu-central-1` 等 | ✅ N/A    |
| Claude Opus 4.7(1M ctx) | ✅                | ❌             | ❌                   | ✅                | ✅                   | ❌        |
| Claude Opus 4.6         | ✅                | ❌             | ❌                   | ✅                | ✅                   | ❌        |
| 多厂商灰度              | ❌                | ❌             | ❌                   | ✅                | ⚠️ 仅 Bedrock 内     | ❌        |
| 切换成本                | 高                | 高             | 高                   | **低**            | 中                   | 极高      |
| 单价(Sonnet 输入)       | $3/M              | n/a            | n/a                  | $3/M(透传)        | $3/M                 | $0(电费)  |
| 延迟 P50                | ~800ms            | ~700ms         | ~900ms               | ~950ms            | ~750ms               | 视 GPU    |
| 工程复杂度              | 低                | 低             | 中                   | **极低**          | 中                   | 极高      |

> 单价数据为 2026 Q1 公开报价,以厂商账单为准。

---

## 6. 决策与 Rationale

### 6.1 双通道架构(Hybrid)

```
                              ┌───────────────────────────────┐
                              │  Backend: AI Brain (router)   │
                              └───────────────┬───────────────┘
                                              │
                       ┌──────────────────────┴──────────────────────┐
                       │                                              │
            HIPAA 客户?  │ Yes                                          │ No
                       │                                              │
                       ▼                                              ▼
       ┌──────────────────────────────┐            ┌────────────────────────────┐
       │  AWS Bedrock                 │            │  OpenRouter                │
       │  + Anthropic BAA             │            │  + Claude Opus 4.7 (主)    │
       │  + Claude Opus 4.7 / Sonnet  │            │  + Claude Sonnet 4.6       │
       │  Region: us-east-1 / eu-*    │            │  + Gemini Image (预留)     │
       └──────────────────────────────┘            └────────────────────────────┘
```

### 6.2 为什么是 OpenRouter + Bedrock(而非纯 D 或纯 E)

- **HIPAA BAA 硬约束(C-02)否决了纯 OpenRouter** — 销售合同已承诺 HIPAA,而 OpenRouter 不签 BAA,合规链断裂
- **多厂商可切换约束(C-07)否决了纯 Bedrock** — 早期产品阶段必须保留模型 A/B 与厂商切换能力,Bedrock 仅覆盖 Anthropic + 少量厂商,聚合度不足
- **代价**:需要在 `AI Brain` 层加一个 router 分支(约 50 行代码),但能在合规与灵活性之间取得最优解

### 6.3 模型分配 Rationale

| Agent           | 模型                            | 选型理由                                                                                                       |
| --------------- | ------------------------------- | -------------------------------------------------------------------------------------------------------------- |
| **Persona**     | **Claude Opus 4.7**(1M context) | 少量样本 → 多视角综合推断;**4.7 升级 1M 上下文**,可一次性吃下完整品牌资料 + 历史活动 + 受众数据,无需上下文压缩 |
| Persona(兜底)   | Claude Opus 4.6                 | 4.7 区域不可用 / 故障时 OpenRouter 自动降级;接口签名一致,切换零代码                                            |
| **Creative**    | Claude Sonnet 4.6               | 模板化产出 + 文风模仿,Sonnet 性价比足够;批量生成对成本敏感,无需 Opus                                           |
| **Attribution** | Claude Sonnet 4.6               | 数据 + 自然语言总结,无需重推理;归因数学计算在 SQL 完成,LLM 只做解读                                            |
| **Image(预留)** | Gemini 2.5 Flash Image          | Anthropic 暂无图像生成;Gemini Flash 在多模态成本/延迟最佳                                                      |

**关于 Opus 4.7 的升级动因**:

- **1M 上下文**(从 4.6 的 200K 提升 5x):允许 Persona Agent 在单次调用中携带完整 Brand Kit + 6-12 个月历史 Campaign 数据 + 跨平台用户行为,**取消现有的 prompt 压缩 / 摘要预处理逻辑**(简化代码 + 减少信息损失)
- **基准提升**:在内部 Persona 评测集上,4.7 相对 4.6 的"洞察深度"评分提升 ~12%(由产品团队人工打分,样本 N=50)
- **同价位**:Anthropic 公布 4.7 与 4.6 同一计费档位($15/$75 per M tokens),无成本上行
- **风险**:新模型上线初期可用性可能波动 → 故保留 4.6 作为 OpenRouter 自动降级目标

---

## 7. 合规姿态(Compliance Posture)

### 7.1 GDPR

- ✅ Anthropic / OpenRouter / AWS 均提供 DPA(Data Processing Agreement)
- ✅ EU 客户路由到 Bedrock `eu-central-1`(法兰克福)
- ✅ 不向 LLM 提供商发送原始 PII — Prompt 进 Brain 前已经过 `anonymize_record_for_warehouse()` 哈希
- ✅ DSAR 删除请求:由于不在 LLM 端持久化,删本地 `token_usage` + `audit_logs` + `persona_results` 即可

### 7.2 CCPA

- ✅ Anthropic 公开声明不将客户 API 数据用于模型训练(zero data retention 选项)
- ✅ 通过 OpenRouter 的请求继承 Anthropic 政策
- ✅ "Do Not Sell"信号:本架构默认不"出售"任何数据

### 7.3 HIPAA

- ✅ **Bedrock 通道**:AWS BAA + Anthropic 子处理者协议,覆盖端到端 PHI 处理
- ✅ **PHI 检测拦截**:`phi_detector.scan_record()` 在 prompt 进 LLM 前最后一道防线
- ⚠️ **风险**:HIPAA 客户的请求**绝不能误走 OpenRouter 通道**,需要在 Brain 层强制断言(见 §10 风险)

---

## 8. 成本模型

### 8.1 单价(2026 Q2)

| 模型                      | 输入($/M tokens) | 输出($/M tokens) | 上下文窗口 |
| ------------------------- | ---------------- | ---------------- | ---------- |
| **Claude Opus 4.7**(主推) | $15              | $75              | **1M**     |
| Claude Opus 4.6(兜底)     | $15              | $75              | 200K       |
| Claude Sonnet 4.6         | $3               | $15              | 200K       |
| Gemini 2.5 Flash Image    | $0.075 / 张图    | —                | —          |

> Opus 4.7 与 4.6 同档位计费,**升级零成本**。1M 上下文按 token 实际消耗计费,不按窗口大小预扣。

### 8.2 月度预算预测(典型 Agency)

假设:中型 Agency,每月 100 个 Persona 任务、500 个 Creative 任务、200 个 Attribution 任务。

| Agent       | 调用量 | 平均 Token       | 模型       | 月成本                    |
| ----------- | ------ | ---------------- | ---------- | ------------------------- |
| Persona     | 100    | 2K in + 5K out   | Opus 4.7   | $40.50                    |
| Creative    | 500    | 1.5K in + 2K out | Sonnet 4.6 | $17.25                    |
| Attribution | 200    | 3K in + 1K out   | Sonnet 4.6 | $4.80                     |
| **合计**    |        |                  |            | **~$62.55 / Agency / 月** |

> Opus 4.7 启用 1M 上下文后,Persona 单次调用 Token 上限可至 ~50K input(取消摘要预处理时),月成本上限约 $112.50,仍在预算内。

> 默认 `monthly_token_budget = 1,000,000`,折合约 **$15-30 / Agency / 月**(取决于模型分布)。Sales 卖的"AI Tier"定价应至少覆盖 3x 倍率(给毛利 + buffer)。

### 8.3 计费机制

- 每次 LLM 调用写一条 `token_usage` 记录(`prompt_tokens / completion_tokens / cost_usd`)
- 月度 cron 汇总 → 比对 `agencies.monthly_token_budget` → 超额时 `check_budget()` 抛 `ValueError` → API 返回 HTTP 429
- 实际计费以 OpenRouter / AWS 月账单为准,本地 `cost_usd` 为估算

---

## 9. 性能与 SLA

| 指标     | 目标      | 来源                                          |
| -------- | --------- | --------------------------------------------- |
| P50 延迟 | < 1.5s    | Persona 重推理                                |
| P95 延迟 | < 30s     | 单次请求 P95 延迟 ≤ 30s 的销售承诺(C-06)      |
| 可用性   | 99.5%     | OpenRouter / Bedrock SLA 取下限               |
| 失败兜底 | Mock 输出 | `_MOCK_OUTPUT` 自动降级,不让用户感知 LLM 故障 |

---

## 10. 风险与缓解

| ID       | 风险                              | 概率 | 影响             | 缓解                                                                               |
| -------- | --------------------------------- | ---- | ---------------- | ---------------------------------------------------------------------------------- |
| **R-01** | HIPAA 客户请求误走 OpenRouter     | 中   | **高(法律责任)** | Brain 层强制断言:`if agency.hipaa_enabled: assert route == "bedrock"`;单元测试覆盖 |
| **R-02** | OpenRouter 不可用                 | 低   | 中               | 直连 Anthropic 的备用配置;`_MOCK_OUTPUT` 兜底;Sentry 告警                          |
| **R-03** | Anthropic 涨价 / 弃用模型         | 中   | 中               | OpenRouter 一行 ENV 切到 OpenAI / Gemini;预设兼容性测试集                          |
| **R-04** | LLM 输出违反 JSON Schema          | 中   | 低               | `try: json.loads(content) except: 落 raw_response 字段` 已实现                     |
| **R-05** | Token 预算被恶意刷爆              | 低   | 中               | 已有 `monthly_token_budget` 硬上限 + 429;增加单租户 QPS 限流(TODO)                 |
| **R-06** | Prompt Injection 泄露其他租户数据 | 中   | 高               | Prompt 不携带跨租户数据(Brain 已按 `agency_id` 隔离 Shared Context);定期红队测试   |
| **R-07** | Anthropic 区域故障(全 US 单区域)  | 低   | 中               | 使用 Bedrock 多区域作为 HIPAA 通道时已具备区域隔离;监控 Anthropic Status Page      |

---

## 11. 复盘触发器(Revisit Triggers)

任意一条命中即触发本决策的重新评估:

- ⏰ **时间**:6 个月后(2026-10-30)
- 💰 **成本**:任一月度 LLM 账单超 **$10,000 USD**
- 📈 **规模**:Token 用量超 100M / 月
- 🔧 **质量**:任一 Agent 输出投诉率 > 5%
- 🆕 **新模型**:GPT-5 / Claude Opus 5 / Gemini Ultra 2 等**代际**更新发布(Opus 4.7 已纳入本决策,小版本不触发复盘)
- ⚖️ **合规**:新增法规(如 EU AI Act 高风险条款生效)

---

## 12. 实施清单(Step 2 关闭前必须完成)

- [x] **代码层:Brain 路由分支** — `backend/app/services/ai/brain.py` 增加 `route_request()` HIPAA 分支
- [ ] **模型升级** — `backend/app/core/config.py` 修改 `PERSONA_MODEL = "anthropic/claude-opus-4-7"`,保留 `PERSONA_MODEL_FALLBACK = "anthropic/claude-opus-4-6"`
- [ ] **降级逻辑** — Persona Agent 在 Opus 4.7 返回 5xx 时自动重试 4.6(httpx 重试中间件)
- [ ] **配置层:新增 ENV** — `BEDROCK_REGION` / `BEDROCK_ROLE_ARN` / `BEDROCK_BAA_ENABLED`
- [ ] **Agency 模型字段** — `agencies.hipaa_enabled BOOLEAN DEFAULT FALSE`(已有)、`agencies.preferred_llm_route VARCHAR DEFAULT 'openrouter'`
- [ ] **审计强化** — `audit_logs.llm_route` 字段记录每次走的通道(`openrouter` / `bedrock`)
- [ ] **测试** — `test_ai.py` 新增 HIPAA 路由强制断言用例
- [ ] **文档** — 本 ADR 进 PSD §Technical Constraints
- [ ] **商务** — Anthropic Bedrock BAA 签署(AR/法务推进)
- [ ] **监控** — Langfuse 标签区分 `route=openrouter` / `route=bedrock`

---

## 13. 签署

| 角色                     | 姓名               | 日期     | 状态 |
| ------------------------ | ------------------ | -------- | ---- |
| 技术决策人(CTO)          | **\*\***\_**\*\*** | \_\_\_\_ | ⬜   |
| 产品负责人               | **\*\***\_**\*\*** | \_\_\_\_ | ⬜   |
| 合规官 / DPO             | **\*\***\_**\*\*** | \_\_\_\_ | ⬜   |
| 销售代表(确认与合同一致) | **\*\***\_**\*\*** | \_\_\_\_ | ⬜   |
| 法务(BAA / DPA)          | **\*\***\_**\*\*** | \_\_\_\_ | ⬜   |

---

## 附录 A:与项目现状的差距

> 本节列出本决策相对当前 main 分支代码的"待补齐"项。

| 项                                  | 当前状态                                                   | 决策要求                          | 工作量   |
| ----------------------------------- | ---------------------------------------------------------- | --------------------------------- | -------- |
| OpenRouter 通道                     | ✅ 已实现([brain.py](../backend/app/services/ai/brain.py)) | 保持                              | 0        |
| Persona 模型版本                    | ⚠️ `claude-opus-4-6`(config.py:53)                         | 升级为 `claude-opus-4-7`,4.6 兜底 | ~0.5 d   |
| 1M 上下文启用                       | ❌ 未利用                                                  | 取消 Persona 的 prompt 压缩       | ~1 d     |
| Bedrock 通道                        | ❌ 未实现                                                  | 新增                              | ~3 d     |
| HIPAA 路由强制                      | ❌ 未实现                                                  | 新增断言                          | ~0.5 d   |
| `agencies.preferred_llm_route` 字段 | ❌ 未有                                                    | 新增迁移                          | ~0.5 d   |
| 路由审计字段                        | ❌ 未有                                                    | 加 `audit_logs.llm_route`         | ~0.5 d   |
| Bedrock BAA 商务流程                | ❌ 未启动                                                  | 推进                              | 法务跟进 |

---

## 附录 B:被否决方案的归档理由

| 方案              | 否决原因                                                               |
| ----------------- | ---------------------------------------------------------------------- |
| 纯 Anthropic 直连 | 单一厂商锁定违反"模型可切换,不锁定单一厂商"约束(C-07);无法做多模型 A/B |
| 纯 OpenAI         | 当前 Persona / Creative 评测不及 Claude;且我们已有 Anthropic 商务关系  |
| 纯 Vertex AI      | HIPAA 路径需 Google Healthcare API,集成成本 > Bedrock                  |
| 纯 OpenRouter     | **不签 BAA**,违反"HIPAA 客户必须有签署 BAA"硬约束(C-02)                |
| 纯 Bedrock        | 失去多厂商灰度能力,违反"模型可切换,不锁定单一厂商"约束(C-07)           |
| 自托管            | MVP 阶段时间不允许;质量差距 > 可接受范围                               |

---

## 附录 C:相关 ADR / 文档

- [docs/ARCHITECTURE-DEEP-DIVE.md](./ARCHITECTURE-DEEP-DIVE.md) — §1 LLM 选型与路由(实现细节)
- [features/PROJECT-PLAN.md](../features/PROJECT-PLAN.md) — F-09 Core AI Brain 模块状态
- [features/compliance/architecture.md](../features/compliance/architecture.md) — 合规顶层策略
- [CLAUDE.md](../CLAUDE.md) — §Compliance Rules

---

> 文档版本历史
> v1.0 · 2026-04-30 · 初版,关闭销售周期"LLM 厂商未定"开放项
> v1.1 · 2026-05-08 · 纳入 Claude Opus 4.7(1M 上下文)作为 Persona 主模型,4.6 转为自动降级兜底;新增升级动因 / 实施清单 / 单价表
