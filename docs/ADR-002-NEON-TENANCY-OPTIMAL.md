# ADR-002 (Optimized) — Neon Database-per-Tenant 最优解

> **文档类型**:Architecture Decision Record(ADR-002 v2,基于工具生态最新调研)
> **状态**:✅ 推荐采纳 · 待技术决策人签署
> **决策日期**:2026-05-11
> **取代**:[ADR-002 v1](./ADR-002-NEON-DATABASE-PER-TENANT.md)(DIY 方案,保留用于对照)
> **变化原因**:经外部检索,Neon + ClickHouse(PeerDB)+ Bytebase 等工具生态已成熟,**自研 80% 的工作可由托管/开源工具直接覆盖**

---

## 问题与答案(Quick Answer)

> 直接回答原始两个问题。详细方案见后续章节。

### 问题 1:全局聚合查询变得复杂(超管要看全系统数据,需要跨库)

**答**:**按查询性质分三层路由,主路径走"CDC 到分析仓库"而不是跨 N 个库 join**。

| 查询类型                               | 工具 / 路径                                                        | 延迟      | 自研量          |
| -------------------------------------- | ------------------------------------------------------------------ | --------- | --------------- |
| 单租户业务 CRUD                        | FastAPI 直连该租户 DB(经 catalog DB 查路由)                        | < 50ms    | 已有            |
| **超管历史/分析报表**(主战场,90% 场景) | **Airbyte CDC** → Snowflake → dbt `mart_global_*` → 超管 dashboard | 1-3s      | 仅写 dbt 模型   |
| 超管实时面板("刚发生的事件")           | App 层 `asyncio.gather` fan-out(限并发 10)                         | 100-500ms | 写一个工具函数  |
| DBA ad-hoc 诊断                        | `postgres_fdw` 在 DBA 调试库挂载租户库                             | 慢        | 临时性,不进生产 |

**核心思想**:不要试图让"跨库 join"本身高性能。把跨租户聚合这个问题**搬出 OLTP 层**,丢给 Snowflake / ClickHouse 这种 MPP 列存引擎解决。Airbyte 做托管的 CDC,延迟 < 5 秒,完全满足超管报表需求。

**实时性 < 1 秒的少数场景**用 app fan-out 兜底,但**不作主路径**(超过 ~100 租户会逼近不可用)。

---

### 问题 2:如何确保数据库变更有效应用到 prod 各个 DB + 如何验证?

**答**:**用 Bytebase 替代自研编排器,它原生提供 batch + canary + drift detection + SQL review 四件套**。

| 需求                                         | Bytebase 内置功能                               | 自研需要                                |
| -------------------------------------------- | ----------------------------------------------- | --------------------------------------- |
| **批量执行到 N 个 tenant DB**                | Multi-tenant batch change(一个 issue → 所有 DB) | 自写 Celery 任务 + 并发控制             |
| **灰度部署 / Canary**                        | 3 阶段 canary,任一阶段失败自动暂停              | 自写 Neon Branch API 脚本               |
| **预防危险变更**(如加 NOT NULL 不带 default) | SQL Review 200+ 规则,merge 前拦截               | 自写 smoke test 集                      |
| **检测漂移**(实际库 schema ≠ 期望 schema)    | Schema Sync drift detection 内置 cron           | 自写 reconciliation cron + 健康检查端点 |
| **审计 + 审批工作流**                        | 内置 audit trail + 多级审批                     | 自建                                    |
| **实时可视化部署进度**                       | GUI 看着每个 tenant 升级,异常可暂停             | 自建 Grafana                            |
| **GitOps**(GitHub PR 触发)                   | webhook 集成原生                                | 自建                                    |

**验证机制三层**(Bytebase 全部覆盖):

1. **预发布**:挑 1-3 个 canary tenant(含 HIPAA 客户)先升级,失败自动暂停
2. **过程中**:每升一个 tenant,SQL Review 跑过 → 才标记成功;否则保留旧版本号 + 告警
3. **事后**:Schema Sync 每天对比每个 tenant 实际 schema vs 期望,漂移自动开 fix issue

**部署成本**:Bytebase Community Edition 自托管 1 个 Docker 容器,**半天部署 + 半天接入**,免费(10 instance 内)/ $20/user/月(Pro)。

**为什么这是最优解**:Bytebase 是开源的(可自托管避开数据出境合规问题)+ Neon-native(原生支持)+ 已有 25 种 DB engine 适配,**未来如果某些租户切换到 BigQuery/Spanner 等也无需更换工具**。

---

## 0. TL;DR(最优解 vs 自研)

| 维度                    | ADR v1(自研)                                              | **ADR v2(最优 / 推荐)**                                                                |
| ----------------------- | --------------------------------------------------------- | -------------------------------------------------------------------------------------- |
| **控制面 DB 命名**      | `receptiviq_control` 自定义                               | **`catalog database`**(Neon 官方术语,文档对齐)                                         |
| **跨租户 CDC**          | Neon Logical Replication 自己写 publisher/subscriber 脚本 | **PeerDB**(ClickHouse 子公司,Neon-native 一键接入)或 **Airbyte**(Snowflake 路径)       |
| **跨租户分析仓库**      | Snowflake(已有)                                           | **ClickHouse**(实时性 +20x,租户多时成本降一个量级)或 **保留 Snowflake**(已有 dbt 复用) |
| **超管实时面板**        | Python `asyncio.gather` fan-out 自己写                    | **Materialize**(物化视图托管)或 **ClickHouse 直查**(P50 < 50ms)                        |
| **Schema 迁移编排**     | 自己写 Celery 任务 + 手动 Alembic                         | **Bytebase**(开源,multi-tenant batch change 原生支持)或 **Atlas**(declarative,纯 OSS)  |
| **Canary**              | 自己用 Neon Branch API 写                                 | Bytebase 内置 canary + 实时 GUI 监控                                                   |
| **Smoke test**          | 自己写 SQL 集                                             | Bytebase **SQL Review 200+ 规则** 开箱即用                                             |
| **Reconciliation 对账** | 自己写 cron + 端点                                        | Bytebase **Schema Sync** 内置 drift detection                                          |
| **自研代码量**          | ~11-13 工作日                                             | **~3-5 工作日**(主要是接入配置 + 业务路由)                                             |

---

## 1. 行业调研要点(为什么改方案)

### 1.1 Neon 官方推荐:Catalog Database 模式

> 来源:[Neon Docs · Multitenancy](https://neon.com/docs/guides/multitenancy) + [Database per Tenant](https://neon.com/use-cases/database-per-tenant)

Neon 明确将控制面 DB 命名为 **catalog database**,并给出标准 schema 形态:

- `customer` / `project` / `database` 三表
- 用 `citext` 存非大小写敏感字段
- `uuid` 主键
- 关键列上**强制索引**(用于 control plane 高频查询)

**对我们的意义**:不要发明新术语,直接对齐 `catalog database` 让运维 / DBA 上手成本为零。

### 1.2 CDC 工具:PeerDB 已被 ClickHouse 收购,变成"Neon-native"的产品

> 来源:[Neon Blog · CDC from Neon to ClickHouse via PeerDB](https://neon.com/blog/postgres-meets-analytics-cdc-from-neon-to-clickhouse-via-peerdb)

- **PeerDB** 原本是独立 CDC 工具,2024 年被 ClickHouse 收购,现作为 **ClickPipes** 集成进 ClickHouse Cloud
- Neon → PeerDB → ClickHouse 是一条**官方推荐路径**,延迟 < 5s,吞吐每秒数十万行
- 一键配置:Neon UI 启用 Logical Replication 后,PeerDB 自动发现并订阅
- **替代了我们自己写 publication/subscription 脚本的 1 天工作**

**Snowflake 路径**:如果坚持用 Snowflake(项目已有),走 **Airbyte**([Neon → Snowflake 官方指南](https://neon.com/docs/guides/logical-replication-airbyte-snowflake)),同样托管化。

### 1.3 实时查询引擎:ClickHouse 在多租户聚合场景显著优于 Snowflake

> 来源:[ClickHouse vs Snowflake](https://www.flexera.com/blog/finops/clickhouse-vs-snowflake/) + [Neon Case Study · DoubleCloud](https://double.cloud/resources/case-studies/neon-increases-data-granularity-with-managed-clickhouse/)

| 维度                | ClickHouse                    | Snowflake                      |
| ------------------- | ----------------------------- | ------------------------------ |
| **典型查询延迟**    | P50 < 50ms(聚合)              | P50 1-3s                       |
| **租户数扩展性**    | 单集群可处理 10K+ 租户 schema | 多 schema 时 metadata 操作变慢 |
| **成本(典型场景)**  | $200-500/月                   | $1000-2000/月                  |
| **dbt 兼容**        | ✅(原生 adapter)              | ✅(已有)                       |
| **复用现有 ETL 栈** | 需新接                        | 项目已有                       |

**取舍**:本项目租户数预计 < 50 时,**保留 Snowflake** 复用现有 dbt 栈最划算;租户数 > 100 或需要"超管面板秒级响应"时,**切换 / 并存 ClickHouse**。

### 1.4 Schema 迁移工具:Bytebase 是当前最优 multi-tenant 编排器

> 来源:[Bytebase · Multi-Tenant Patterns](https://www.bytebase.com/blog/multi-tenant-database-architecture-patterns-explained/) + [Bytebase vs Atlas](https://www.bytebase.com/blog/bytebase-vs-atlas/)

Bytebase 内置以下**正好对应我们 ADR v1 自研的所有功能**:

- ✅ **Multi-tenant batch change**:一个 issue 跨数百 tenant DB 部署
- ✅ **Canary 支持**:阶段性灰度,任一阶段失败自动暂停
- ✅ **SQL Review**:200+ 规则,捕获"加 NOT NULL 不带默认值"等危险变更
- ✅ **Schema Sync**:drift detection 内置,等同于我们的 reconciliation cron
- ✅ **GitOps**:从 GitHub PR 直接触发部署
- ✅ **审计 + 审批工作流**
- ✅ **实时 GUI 监控**:看着每个 tenant 升级进度,异常可暂停
- ✅ **开源**:Community 版免费(支持 10 个 instance);超量后 $20/user/月

**对比 Atlas**:Atlas 是 declarative SQL-first 工具,适合"代码即合约"团队,但**缺 GUI 和审批工作流**。Bytebase 适合"运维需要可视化、有审批流程"的团队。

**结论**:Bytebase 直接替代我们 ADR v1 中的 Celery orchestrator + canary scripts + reconciliation cron 三件套。

---

## 2. 最优架构(全景)

```
┌────────────────────────────────────────────────────────────────────────┐
│                                                                          │
│   Catalog Database (Neon)                                                │
│   - customer · project · database (Neon official schema)                │
│   - schema_version per tenant                                           │
│                                                                          │
└────────┬───────────────────────────────────────────────────────────────┘
         │
         │ tenant routing (FastAPI dependency)
         ▼
┌────────────────────────────────────────────────────────────────────────┐
│   Tenant Postgres DBs (Neon database-per-tenant)                        │
│   - tenant_a3f9... · tenant_b21c... · tenant_c84d... · ...               │
│   - HIPAA clients on separate Neon projects (EU/US regions)            │
└────┬────────────────────────────────────────────┬─────────────────────┘
     │                                            │
     │ PeerDB / Airbyte CDC                       │ App fan-out (rare)
     │ (managed, near-real-time)                  │ asyncio.gather
     ▼                                            ▼
┌──────────────────────────┐              ┌──────────────────┐
│  ClickHouse  或  Snowflake │              │  Super-admin UI   │
│  - per-tenant schema      │              │  (for "live now"  │
│  - dbt mart_global_*      │              │   queries only)   │
│  - 秒级查询响应             │              └──────────────────┘
└────────────┬─────────────┘
             │
             ▼
   Super-admin Dashboard
   (主流量入口)

──────── 旁路 ────────

┌──────────────────────────────────────────────────────────────┐
│  Bytebase  (schema change orchestrator)                       │
│  - GitOps integration with GitHub PR                          │
│  - Batch change across all tenant DBs                         │
│  - Canary stages (HIPAA tenant · power user · long-tail)      │
│  - SQL Review (200+ rules) before merge                       │
│  - Schema Sync (drift detection cron, built-in)               │
│  - Audit + approval workflow                                  │
└────────────┬─────────────────────────────────────────────────┘
             │
             ▼
   Catalog DB + all Tenant DBs
   (one batch issue applies to all)
```

---

## 3. 问题 1 最优解:跨租户聚合查询

### 3.1 三层路由,但工具全部托管化

| 查询类型                           | 工具                                                      | 延迟目标  | 工程量                            |
| ---------------------------------- | --------------------------------------------------------- | --------- | --------------------------------- |
| 单租户业务 CRUD                    | FastAPI 直连(经 catalog 查路由)                           | < 50ms    | 已有                              |
| 超管实时面板("当前在线人数")       | **App fan-out** 兜底 OR **Materialize 物化视图**          | 100-500ms | App fan-out 自研,Materialize 托管 |
| 超管分析报表 / 合规审计 / 月度统计 | **ClickHouse**(经 PeerDB CDC)或 **Snowflake**(经 Airbyte) | 1-3s      | **零自研**(配置 PeerDB / Airbyte) |
| DBA ad-hoc 诊断                    | `postgres_fdw`                                            | 慢        | 仅 DBA 工具,不进生产              |

### 3.2 推荐组合(本项目专属)

```
推荐:  Tenant DBs → Airbyte (CDC) → Snowflake → dbt → 超管 dashboard
       └ Phase 2 评估:租户超 100 或延迟 > 3s 时切 ClickHouse
```

**理由**:

1. 项目已有 Snowflake + dbt + Airflow,**保持栈不变**
2. Airbyte 托管(Airbyte Cloud 起步 $0,流量级别后按量付费)
3. 跨租户超管视图用 `UNION ALL` 跨 schema 拼接,**dbt mart*global*\*** 模型实现
4. **app fan-out 仅作为兜底**(实时性要求 < 1 分钟时使用),并发 10,Semaphore 限流

### 3.3 哪些场景**不要用** CDC,要用 fan-out

| 场景                                                     | 原因                                                  |
| -------------------------------------------------------- | ----------------------------------------------------- |
| 超管修改全平台配置后立刻验证(< 1 秒延迟)                 | CDC 有 1-5s 延迟                                      |
| 跨租户事务性 join("租户 A 和 B 共享了一个外部 user_id?") | 仓库 schema 分离,join 复杂                            |
| 紧急合规事件实时排查                                     | 走不通 ETL 管道,直接 fan-out 才能保证刚发生的数据可见 |

### 3.4 实施清单(Problem 1)

| 任务                                                      | 工具          | 工时  |
| --------------------------------------------------------- | ------------- | ----- |
| 在 Neon 上启用 Logical Replication(全租户库)              | Neon UI / API | 0.5 d |
| 配置 Airbyte connection(Neon → Snowflake)                 | Airbyte Cloud | 0.5 d |
| Snowflake 接收 schema 设计(per-tenant + global mart)      | dbt           | 1 d   |
| dbt `mart_global_*` 模型(union all 跨租户)                | dbt           | 0.5 d |
| FastAPI `TenantSession` dependency + app fan-out 工具函数 | Python        | 1 d   |
| 超管 dashboard API 端点(走 Snowflake 主流量)              | Python        | 0.5 d |

**总计:~4 工作日**(vs ADR v1 的 6-7 天)

---

## 4. 问题 2 最优解:迁移编排 + 验证

### 4.1 推荐:Bytebase Community Edition

> 接入步骤: **半天部署 + 半天迁移现有 Alembic 脚本**

#### 部署

- 自托管 Bytebase(单容器 Docker)或 Bytebase Cloud
- 注册所有 Neon database 实例(GUI 或 API 一次性批量导入,从 catalog DB 读)

#### GitOps 集成

- Bytebase 监听 GitHub repo 的 `migrations/` 目录
- PR 合并 → Bytebase 自动创建 **change issue**
- Issue 上可见每个 tenant 的部署状态(待审批 / 部署中 / 完成 / 失败)

#### 三阶段 canary 配置

```
Stage 1: 1 个测试 tenant(staging)     → 必须通过
   ↓
Stage 2: 3 个 canary tenants:
         - 1 HIPAA client
         - 1 高用量
         - 1 低用量                     → 任一失败暂停
   ↓
Stage 3: 全量 tenants(批量 10 并行)    → 全部完成或部分失败
```

#### SQL Review 规则

Bytebase 自带规则可直接启用:

- ❌ `NOT NULL` 列不带 default(危险)
- ❌ `DROP TABLE`(高风险,需 manual override)
- ❌ `ALTER COLUMN TYPE`(锁表风险,要求拆 4 步)
- ❌ 数据回填语句进迁移(应该用 task,不应进 migration)
- ⚠️ Index 创建未带 `CONCURRENTLY`
- ✅ 自定义规则:迁移文件命名规范、必须有 downgrade、etc.

#### Schema Drift 检测

Bytebase **内置 cron**(默认每天扫描),对比每个 tenant 实际 schema 与目标 schema:

- 一致 ✅
- 漂移 ⚠️ → 自动生成"修复 issue"等审批
- 等同于我们 ADR v1 中的 reconciliation cron,但**零自研**

### 4.2 现有 Alembic 迁移文件如何兼容?

**两条路:**

**路径 A:保留 Alembic 文件,Bytebase 作为编排层**

- 现有 `alembic/versions/*.py` 不动
- Bytebase 用 "Imperative migration" 模式逐个执行 `alembic upgrade head`
- 优点:零代码改动;缺点:失去 Bytebase 的 SQL Review 增益

**路径 B:导出为纯 SQL,Bytebase 作为执行器**(推荐)

- Alembic offline mode 导出每个 revision 为纯 SQL 文件
- Bytebase 直接管理这些 SQL 文件
- 优点:Bytebase 的 SQL Review 全部生效;迁移历史更透明
- 工作量:一次性脚本 0.5 天

### 4.3 备选:Atlas(纯 OSS,无 GUI)

如果团队倾向"代码即合约 / 不要额外 GUI 服务":

- Atlas declarative SQL schema 文件
- `atlas migrate apply --dry-run` for canary
- 在 GitHub Actions 里跑批量 apply 到所有 tenant
- **但需要自己实现 reconciliation 和监控仪表盘**,工作量回升到 ADR v1 水平

### 4.4 实施清单(Problem 2)

| 任务                                     | 工具         | 工时  |
| ---------------------------------------- | ------------ | ----- |
| 部署 Bytebase Community(Docker)          | Docker       | 0.5 d |
| 批量注册 tenant DBs(从 catalog 读)       | Bytebase API | 0.5 d |
| 配置 GitOps webhook(GitHub → Bytebase)   | Bytebase UI  | 0.5 d |
| 配置三阶段 canary 策略                   | Bytebase UI  | 0.5 d |
| 启用 SQL Review 规则集                   | Bytebase UI  | 0.5 d |
| 现有 Alembic 文件导出为 SQL(脚本)        | Python       | 0.5 d |
| 启用 Schema Drift cron + 配置 Slack 告警 | Bytebase UI  | 0.5 d |
| 文档:CONTRIBUTING 改用 Bytebase 工作流   | 文档         | 0.5 d |

**总计:~4 工作日**(vs ADR v1 的 5 天 + 长期维护成本)

---

## 5. Build vs Buy 决策矩阵

| 维度                    | 自研(ADR v1)                                   | Bytebase + Airbyte(本 ADR v2)             |
| ----------------------- | ---------------------------------------------- | ----------------------------------------- |
| **首次实施工时**        | 11-13 天                                       | **4-5 天**                                |
| **长期维护成本**        | 持续维护 Celery 任务 / canary 脚本 / 对账 cron | 几乎零(工具厂商维护)                      |
| **GUI / 可视化**        | 需自建 Grafana                                 | **开箱即用**                              |
| **审批工作流**          | 自建(或忽略)                                   | **开箱即用**                              |
| **多 DB engine 兼容**   | 仅 Postgres                                    | **25 种**(若以后接 BigQuery / Spanner 等) |
| **风险:工具供应商绑定** | 无                                             | 中(Bytebase 开源可自托管,可控)            |
| **风险:迁移成本**       | 无                                             | 一次性 0.5 天导 SQL                       |
| **合规审计**            | 需自建                                         | **内置 audit trail**                      |
| **隐性成本**            | 工程师反复造轮子时间                           | Bytebase Pro $20/user/月(5 人 = $100/月)  |

**结论**:**对一个 Phase 1-2 阶段的项目,Bytebase + Airbyte 的工时回报比远超自研**。
仅当遇到以下情况才回到自研:

- 工具供应商业务变更(eg. Bytebase 提价 5x)
- 出现工具无法解决的高度定制需求(目前未见)
- 团队规模 > 50 工程师,定制成本可摊薄

---

## 6. 迁移路径(从现状到最优)

```
当前状态(单库 + agency_id 过滤)
  │
  ▼  Phase A(基础设施,3 天)
新建 Neon catalog DB · 启用 Logical Replication · 写 schema · 批量 provision 2-3 个测试 tenant DB
  │
  ▼  Phase B(后端路由,3 天)
FastAPI TenantSession dependency · 改造现有 ORM 查询(分批,先 users/audit_logs)· 控制面 API 端点
  │
  ▼  Phase C(分析侧,2 天)
配 Airbyte 接 Snowflake · dbt mart_global_* · 超管 dashboard 接 Snowflake
  │
  ▼  Phase D(运维侧,2 天)
部署 Bytebase · 注册 tenant DBs · 配置 canary 阶段 · 启用 SQL Review · Schema Sync cron
  │
  ▼  Phase E(灰度,1-2 天)
迁移真实租户(从最不重要的 1 个开始)· 验证 · 推广
```

**总计:11-13 天端到端**(其中 4-5 天是 Bytebase + Airbyte 工具集成,7-8 天是业务路由改造)

---

## 7. 成本估算(月度)

| 项                           | 自研方案        | 工具方案                        |
| ---------------------------- | --------------- | ------------------------------- |
| Neon catalog DB(单库)        | $19(Pro)        | $19                             |
| Neon tenant DBs(20 个)       | $20×20=$400     | $20×20=$400(免费层 50 个 DB 内) |
| Snowflake                    | 现有            | 现有                            |
| Airbyte(CDC,20 连接)         | n/a             | $300-500(按流量)                |
| Bytebase Community(自托管)   | n/a             | $0                              |
| Bytebase Pro(可选,GUI 协作)  | n/a             | $100(5 user × $20)              |
| 自研代码长期维护(工程师工时) | ~3 天/季度      | 几乎 0                          |
| **月度净增**                 | $419 + 工程工时 | **$719-919**(节约工程工时)      |

**回报分析**:多花 ~$300-500 / 月,**省下每季度 3 天工程师时间** = 净赚

---

## 8. 风险与缓解(更新自 ADR v1)

| ID       | 风险                                          | 概率 | 影响 | 缓解                                                                                                              |
| -------- | --------------------------------------------- | ---- | ---- | ----------------------------------------------------------------------------------------------------------------- |
| **R-01** | Bytebase 厂商变更 / 提价                      | 低   | 中   | Community Edition 开源自托管,可控;Atlas 是备选(可一周内切换)                                                      |
| **R-02** | Airbyte 连接器 bug 导致 CDC 漏数据            | 低   | 中   | Bytebase Schema Sync 兼任 CDC 完整性巡检;关键表有 `updated_at` watermark,数据漏 24h 内可发现                      |
| **R-03** | 租户数快速增长(50→200)导致 Airbyte 成本爆炸   | 中   | 中   | 设触发器:租户数 > 80 时评估切 PeerDB 自托管 或 ClickHouse                                                         |
| **R-04** | 应用层 fan-out 兜底场景被滥用进生产路径       | 中   | 中   | API 层 lint:`@requires_super_admin` 装饰器才能用 fan-out 路径;CI 检查                                             |
| **R-05** | Bytebase 部署后,绕过它直接改库的事件          | 中   | 高   | Drift detection 必开 + Slack/PagerDuty 告警;数据库账号权限收紧(只有 Bytebase service account 能 DDL)              |
| **R-06** | Phase B 改造期间,新旧路径并存导致部分查询失败 | 中   | 中   | Feature flag 滚动切换;改造单元测试覆盖率 > 90%                                                                    |
| **R-07** | HIPAA 客户的 Bytebase / Airbyte 必须签 BAA    | 中   | 高   | Bytebase 自托管 + Airbyte 自托管(或 Bytebase Enterprise + Airbyte 签 BAA);最差走 ADR-001 中 Bedrock 模式,完全隔离 |

---

## 9. 工具选型最终决策表

| 角色                  | 推荐工具                                 | 备选                     | 备注                      |
| --------------------- | ---------------------------------------- | ------------------------ | ------------------------- |
| **租户路由 / 控制面** | Neon catalog database(自实现 schema)     | —                        | 按 Neon 官方命名          |
| **CDC → 分析仓库**    | **Airbyte**(Neon → Snowflake)            | PeerDB(if ClickHouse)    | 项目已有 Snowflake        |
| **跨租户分析查询**    | Snowflake + dbt(已有)                    | ClickHouse(性能升级路径) | 租户超 100 时切           |
| **实时面板兜底**      | Python asyncio fan-out(自写)             | Materialize(托管,$$$)    | 简单场景用 fan-out 即可   |
| **DBA ad-hoc 诊断**   | `postgres_fdw`                           | —                        | 不进生产路径              |
| **Schema 迁移编排**   | **Bytebase Community**                   | Atlas(if no GUI)         | 4 天接入,替代 5+ 天自研   |
| **凭证管理**          | AWS Secrets Manager 或 1Password Connect | HashiCorp Vault          | 已在 ADR-001 选 1Password |
| **跨租户审计聚合**    | Snowflake + dbt audit_global             | —                        | 复用 mart_global          |

---

## 10. 签署

| 角色              | 姓名               | 日期     | 状态 |
| ----------------- | ------------------ | -------- | ---- |
| 技术决策人(CTO)   | **\*\***\_**\*\*** | \_\_\_\_ | ⬜   |
| 数据库管理员(DBA) | **\*\***\_**\*\*** | \_\_\_\_ | ⬜   |
| 合规官 / DPO      | **\*\***\_**\*\*** | \_\_\_\_ | ⬜   |
| 后端架构师        | **\*\***\_**\*\*** | \_\_\_\_ | ⬜   |
| DevOps Lead       | **\*\***\_**\*\*** | \_\_\_\_ | ⬜   |

---

## 11. 复盘触发器

- ⏰ **时间**:6 个月后(2026-11-11)
- 📈 **规模**:租户数超过 80(评估 Airbyte 切 PeerDB 自托管)
- 📊 **租户数超过 150**:评估 Snowflake 切 ClickHouse
- 💰 **成本**:CDC 工具月度账单超 $1000
- 🐛 **质量**:Bytebase Drift Alert 超过 1 次/月
- 🆕 **能力**:Neon 推出 "Native cross-database query federation"(预期 2026 Q4)
- ⚖️ **合规**:出现 Bytebase / Airbyte BAA 阻塞 HIPAA 客户

---

## 附录 A:决策对照表(ADR v1 vs v2)

| ADR v1 自建项                                        | ADR v2 替代物                   | 节省                           |
| ---------------------------------------------------- | ------------------------------- | ------------------------------ |
| Celery 任务 `apply_migrations_to_tenant`             | Bytebase batch change           | 1 d                            |
| Canary deploy 脚本(Neon Branch API)                  | Bytebase canary stages          | 1 d                            |
| Smoke test SQL 集                                    | Bytebase SQL Review(200+ rules) | 0.5 d                          |
| Reconciliation cron + `/health/schema-versions` 端点 | Bytebase Schema Sync            | 0.5 d                          |
| Grafana 仪表盘                                       | Bytebase 内置 GUI               | 0.5 d                          |
| Logical Replication publication/subscription 脚本    | Airbyte / PeerDB                | 1 d                            |
| `mart_global_*` dbt 模型(都要写)                     | 一致                            | 0                              |
| FastAPI `TenantSession` 路由                         | 一致                            | 0                              |
| 控制面 DB schema                                     | 一致(改名 catalog)              | 0                              |
| **合计节省**                                         |                                 | **~4.5 天工时 + 长期维护成本** |

---

## 附录 B:与 ADR-001(LLM Selection)的协同

HIPAA 客户完整数据隔离链(更新版):

```
独立 Neon project(EU/US)                    ┐
   ↓ Airbyte/PeerDB(签 BAA)                 │
独立 Snowflake account / schema             │
   ↓ dbt                                     │  Bytebase 自托管
独立 LLM 通道(AWS Bedrock,见 ADR-001)     │  (避开 Cloud BAA 问题)
   ↓ trace                                   │
Langfuse self-hosted                         ┘
```

ADR-001 + ADR-002 v2 协同保证 HIPAA 端到端 BAA 覆盖。

---

## 附录 C:参考资料

### Neon 官方

- [Neon · Database per Tenant](https://neon.com/use-cases/database-per-tenant)
- [Neon · Multi-tenancy Guide](https://neon.com/docs/guides/multitenancy)
- [Neon · Multi-tenancy & Database-per-User Design](https://neon.com/blog/multi-tenancy-and-database-per-user-design-in-postgres)
- [Neon · HIPAA Compliance for B2B SaaS](https://neon.com/blog/hipaa-multitenancy-b2b-saas)
- [Neon · Stream data via Logical Replication](https://neon.com/blog/stream-data-from-neon-to-external-data-sources-via-logical-replication)
- [Neon · CDC to ClickHouse via PeerDB](https://neon.com/blog/postgres-meets-analytics-cdc-from-neon-to-clickhouse-via-peerdb)
- [Neon · Airbyte to Snowflake guide](https://neon.com/docs/guides/logical-replication-airbyte-snowflake)

### 工具厂商

- [Bytebase · Multi-Tenant Patterns](https://www.bytebase.com/blog/multi-tenant-database-architecture-patterns-explained/)
- [Bytebase vs Atlas comparison](https://www.bytebase.com/blog/bytebase-vs-atlas/)
- [Bytebase · Top Schema Migration Tools 2026](https://www.bytebase.com/blog/top-database-schema-change-tool-evolution/)
- [Atlas · Multi-tenant migrations](https://atlasgo.io/guides/orms/sqlalchemy)
- [ClickHouse vs Snowflake](https://www.flexera.com/blog/finops/clickhouse-vs-snowflake/)
- [Materialize · Ingest from Neon](https://materialize.com/docs/ingest-data/postgres/neon/)

### 学习材料

- [PlanetScale · Approaches to tenancy in Postgres](https://planetscale.com/blog/approaches-to-tenancy-in-postgres)
- [Multi-Tenant Architecture: DB-per-Tenant vs Shared Schema (2026)](https://dev.to/young_gao/multi-tenant-architecture-database-per-tenant-vs-shared-schema-1n2e)
- [Crunchy Data · Designing Postgres for Multi-tenancy](https://www.crunchydata.com/blog/designing-your-postgres-database-for-multi-tenancy)
- [Flyway multi-tenant migration tutorial](https://medium.com/@sentinelfoxinc/postgresql-multi-tenant-migration-using-flyway-tool-aa11608fb8b4)

### 项目内文档

- [docs/ADR-002-NEON-DATABASE-PER-TENANT.md](./ADR-002-NEON-DATABASE-PER-TENANT.md) — v1 自研版(对照用)
- [docs/PSD-LLM-SELECTION-DECISION.md](./PSD-LLM-SELECTION-DECISION.md) — ADR-001
- [docs/CLIENT-ACCOUNT-CHECKLIST.md](./CLIENT-ACCOUNT-CHECKLIST.md) — 客户账号清单(需追加 Bytebase + Airbyte)

---

> 文档版本历史
> v2.0 · 2026-05-11 · 基于工具生态调研重写,推荐 Bytebase + Airbyte 替代自研 80% 部分
