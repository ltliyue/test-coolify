# ADR-002:Neon Database-per-Tenant 架构决策

> **文档类型**:Architecture Decision Record(ADR-002)
> **状态**:✅ Decided · 待技术决策人签署
> **决策日期**:2026-05-11
> **关联**:此前 PSD 默认采用"单库多租户 + `agency_id` 过滤"路线;本 ADR 改为"一租户一库"。
> **来源**:Neon 官方文档 [database-per-tenant](https://neon.com/use-cases/database-per-tenant)

---

## 0. TL;DR(决策摘要)

**采纳方案**:**Neon 一租户一库**(每个 Agency 独立 Postgres 数据库),配套构建跨库聚合 + 迁移编排机制。

| 维度                   | 决策                                                               |
| ---------------------- | ------------------------------------------------------------------ |
| **物理隔离方式**       | 每 Agency 一个 Neon database;HIPAA 客户走独立 Neon project         |
| **租户路由**           | 控制面 DB `receptiviq_control` 维护 `tenant_databases` 注册表      |
| **超管实时面板**       | App 层 fan-out(asyncio.gather,并发上限 10)                         |
| **超管分析报表**       | Neon Logical Replication → Snowflake → dbt 跨租户聚合              |
| **跨租户 ad-hoc 诊断** | `postgres_fdw`(仅 DBA 临时工具,不进生产路径)                       |
| **Schema 迁移编排**    | Celery 任务批量执行 Alembic,canary 走 Neon 分支                    |
| **迁移验证**           | 3 层:canary(分支)+ smoke test(每租户)+ reconciliation cron(每小时) |
| **复盘节点**           | 6 个月或租户数超过 100 时触发                                      |

---

## 1. 决策范围

### 1.1 In Scope

- 业务数据库(PostgreSQL)的多租户隔离策略
- 跨租户聚合查询的路径选型
- Schema 迁移的并行执行与验证机制
- 控制面 DB 与租户 DB 的边界
- 凭证管理

### 1.2 Out of Scope(另行决策或维持现状)

- 数据仓库(Snowflake)的租户隔离 — 维持"per-tenant schema"现状
- 对象存储(MinIO/S3)隔离 — 维持"per-tenant prefix"
- AI Brain / OpenRouter 调用的租户隔离 — 维持现状(Brain 内部按 `agency_id` 过滤)
- ETL adapter 的租户隔离 — 维持现状

---

## 2. 上下文与约束

### 2.1 业务约束

| ID       | 约束                                                    | 来源                      |
| -------- | ------------------------------------------------------- | ------------------------- |
| **C-01** | HIPAA 客户必须**物理隔离**(BAA 要求,不可与其他租户共库) | HIPAA Privacy Rule + 合同 |
| **C-02** | GDPR DSAR 删除必须可证(单租户全量删除可追溯)            | GDPR Art. 17              |
| **C-03** | 单租户事故不得波及其他租户(blast radius 隔离)           | SLA                       |
| **C-04** | 支持每租户独立时点恢复(PITR)与 staging copy             | 合规演练 + 客户开发支持   |
| **C-05** | 超管必须能看全平台数据(不能因隔离失去运营视角)          | 内部运营                  |
| **C-06** | 迁移过程不允许长时间停机(滚动升级)                      | 99.5% 可用性承诺          |
| **C-07** | 迁移必须可审计、可对账、可回滚                          | 合规审计                  |

### 2.2 Neon 提供的能力

| 能力                                 | 用法                                                        |
| ------------------------------------ | ----------------------------------------------------------- |
| **Project / Branch / Database 三层** | Agency = database;HIPAA 客户独占 project;test/dev 用 branch |
| **逻辑复制(Logical Replication)**    | Postgres 原生 `CREATE PUBLICATION` / `SUBSCRIPTION`         |
| **分支秒级创建**                     | 零成本 canary / 临时调试 / 灾难恢复源                       |
| **Postgres FDW**                     | 跨库 join 原生支持                                          |
| **连接池(PgBouncer-style)**          | 默认提供,每库独立                                           |

---

## 3. 问题与解决方案

### 3.1 问题一:超管全局聚合查询变复杂

**矛盾点**:数据物理隔离后,以前一条 `SELECT * FROM users WHERE created_at > ...` 现在要扫 N 个库。

#### 解决方案:三层路由按查询性质分流

```
┌─────────────────────────────────────────────────────────────┐
│  超管查询类型                  路径                          │
├─────────────────────────────────────────────────────────────┤
│  ① 实时操作型(15 分钟内)      App 层 fan-out (asyncio)     │
│      e.g. "当前活跃 session"     并发 10,内存聚合           │
│                                                              │
│  ② 分析型(主战场)             Neon logical replication →   │
│      e.g. "30 天 ARR 趋势"        Snowflake → dbt mart        │
│                                   →超管 dashboard             │
│                                                              │
│  ③ Ad-hoc 跨库诊断(罕见)      postgres_fdw 临时挂载         │
│      e.g. "为什么 user_id 撞了"   仅 DBA 工具,非生产路径     │
└─────────────────────────────────────────────────────────────┘
```

##### 3.1.1 第 1 层 — 应用层 fan-out

**使用场景**:超管打开 Ops Console "全平台 token 用量当前余额"、"过去 1 小时登录失败聚合"。

**机制**:

- FastAPI 端点收到超管请求
- 从控制面 DB 查所有租户库连接串
- `asyncio.gather()` 并发执行同一聚合 SQL(每库一个 asyncpg 连接)
- 在 Python 内存中 SUM/COUNT/AVG 聚合
- 限并发 10(`asyncio.Semaphore(10)`)

**性能预算**:

- 单库查询 P95 < 100ms(操作型聚合)
- N 个租户,N/10 批次,总延迟约 `ceil(N/10) × 100ms`
- 50 租户 → ~500ms(可接受);500 租户 → ~5s(需切换到 Snowflake 路径)

**好处**:无新组件、实时数据、实现简单
**代价**:超过 ~100 租户会逼近不可用、连接池压力

##### 3.1.2 第 2 层 — Logical Replication → Snowflake(主推荐路径)

**使用场景**:几乎所有跨租户分析查询、合规审计、月度报表、运营仪表盘。

**数据流**:

```
租户库 N 个                      Snowflake(已有)
┌──────────┐                    ┌─────────────────────────┐
│ tenant_1 │──pub/sub──→        │  raw_pg.tenant_1.users   │
│ tenant_2 │──pub/sub──→        │  raw_pg.tenant_2.users   │
│   ...    │                    │  raw_pg.tenant_N.users   │
│ tenant_N │──pub/sub──→        │  ...all other tables...  │
└──────────┘                    └─────────┬───────────────┘
                                          ↓ dbt
                                ┌─────────────────────────┐
                                │  mart_global_users       │
                                │  mart_global_token_usage │
                                │  mart_global_audit       │
                                │  (UNION ALL across all)  │
                                └─────────┬───────────────┘
                                          ↓
                                   Ops Console 超管视图
```

**机制**:

- 每个租户 Neon DB 配 `CREATE PUBLICATION` 发布 6-8 张关键业务表(`agencies`, `users`, `token_usage`, `audit_logs`, `personas`, ...)
- Snowflake / 中间 ETL 进程作为 subscriber(可走 Airbyte / Fivetran / 自研 Debezium-like)
- 在 Snowflake 内每租户一个 schema 落库
- dbt 模型 `mart_global_*` 用 `UNION ALL` 拼出"全平台视图"
- 超管查 Snowflake,不打扰任何租户库

**性能**:

- 复制延迟通常 < 1s(对超管报表完全够)
- Snowflake MPP 查询不受租户数线性影响
- 超管查询不消耗租户库资源

**好处**:复用已有 dbt / Snowflake / Airflow 栈;延迟小;隔离不破;合规友好(数据不需回流到主库)
**代价**:配置和维护订阅(可脚本化);约 1s 延迟

##### 3.1.3 第 3 层 — `postgres_fdw`(仅诊断用)

**使用场景**:DBA 排查 bug、合规调查时需要跨租户瞬时 join。

**机制**:

- 单独一个"调试库" `receptiviq_dba_console`
- 在里面 `CREATE EXTENSION postgres_fdw`
- 按需 `CREATE SERVER`(指向租户库)+ `CREATE FOREIGN TABLE`
- 用 SQL 直接跨库 join

**纪律**:

- ❌ 绝不放进任何 production API 调用路径
- ❌ 绝不让普通工程师有这库的写权限
- ✅ 仅 DBA 角色账号可访问
- ✅ 所有查询自动写入审计日志

#### 3.1.4 路由决策矩阵(简表)

| 查询场景                | 路径           | 延迟       | 备注            |
| ----------------------- | -------------- | ---------- | --------------- |
| 单租户业务 CRUD         | 直连该租户库   | < 50ms     | 现有逻辑        |
| 超管实时面板            | App fan-out    | 500ms ~ 5s | 不超过 100 租户 |
| 超管历史趋势 / 合规报表 | Snowflake mart | < 2s       | 主战场          |
| 跨租户 ad-hoc join      | postgres_fdw   | 慢         | DBA 工具        |

#### 3.1.5 配套设施

| 项                 | 说明                                                                                                |
| ------------------ | --------------------------------------------------------------------------------------------------- |
| **控制面 DB**      | 单独 Neon 项目 `receptiviq_control`,放 `tenant_databases` 注册表 + 全局配置 + 超管账号              |
| **租户路由中间件** | FastAPI dependency `get_tenant_db_session(user.agency_id)`,从控制面查到连接串(Secrets Manager 引用) |
| **凭证管理**       | 控制面表只存 Secret reference;实际密码走 1Password Connect / AWS Secrets Manager                    |
| **连接池**         | 每租户库走 PgBouncer transaction-mode;Python 侧 `asyncpg.create_pool(min=2, max=20)`                |

---

### 3.2 问题二:迁移有效应用到 prod 各个数据库 + 验证

**矛盾点**:Alembic 默认面向单库,N 个租户库要保证每个都升到同一版本,且失败可定位。

#### 解决方案:Registry + 编排器 + 三层验证

##### 3.2.1 组件 A — 租户库注册表

控制面 DB 里新建 `tenant_databases` 表(逻辑结构):

| 列                           | 含义                                                |
| ---------------------------- | --------------------------------------------------- |
| `tenant_id` (PK)             | Agency UUID,与业务 `agencies.id` 关联               |
| `neon_project_id`            | Neon 控制台项目 ID                                  |
| `neon_db_name`               | 数据库名(e.g. `tenant_a3f9b21`)                     |
| `connection_secret_ref`      | Secrets Manager / 1Password 中密码项的引用,不存明文 |
| `region`                     | Neon region(EU 客户走 `eu-central-1`)               |
| `current_schema_version`     | Alembic revision hash                               |
| `target_schema_version`      | 期望版本(部署时由编排器写入)                        |
| `last_migration_at`          | timestamp                                           |
| `last_migration_status`      | `success` / `failed` / `in_progress`                |
| `last_migration_error`       | 失败时记错误堆栈                                    |
| `migration_lock_until`       | 防重入锁,过期自动释放                               |
| `hipaa_enabled`              | 是否走独立 Neon project                             |
| `created_at` / `archived_at` | 生命周期                                            |

**作用**:

- **单一事实源**:谁有哪些库一目了然
- **审计追踪**:每次迁移成功 / 失败留痕
- **防重入**:`migration_lock_until` 防止并发跑同一个租户
- **GDPR 删除友好**:archived 而非物理删,保留审计

##### 3.2.2 组件 B — 迁移编排器(Celery 任务)

任务签名:`apply_migrations_to_tenant(tenant_id: UUID, target_version: str)`

执行步骤:

1. 从注册表读连接串(经 Secrets Manager 解析)
2. `SET migration_lock_until = now() + interval '10 min'`(防重入)
3. 调用 `alembic.command.upgrade(config, target_version)`(直接 Python API,不走 shell)
4. 跑 smoke test(下面 Layer 2)
5. 成功 → `UPDATE tenant_databases SET current_schema_version=:target, last_migration_at=now(), last_migration_status='success', last_migration_error=NULL, migration_lock_until=NULL`
6. 失败 → 记 `last_migration_status='failed'` + 完整堆栈 → 触发告警(Sentry + PagerDuty)

**调度入口**:`apply_migrations_to_all(target_version)`

- 查注册表所有 `current_schema_version != target_version AND archived_at IS NULL` 的租户
- Celery `group()` 批量提交,并发上限 10
- `chord()` 汇总回调:统计成功 / 失败数,发汇总 Slack 通知

**为什么 Alembic 适合多库批跑**:

- **天然幂等**:同一 revision 跑两次第二次自动跳过 — 失败重试零风险
- **支持任意 connection URL**:Python API 可动态传入 connection string
- 版本号(revision hash)可用于精确对账

##### 3.2.3 组件 C — 三层验证

**Layer 1:Canary(预发布)**

```
1. 选 3 个代表性租户:
   - 1 个 HIPAA 客户(独立 project)
   - 1 个高用量普通租户
   - 1 个低用量普通租户
2. 调用 Neon API 为每个租户库 branch 一份(秒级、零成本)
3. 在 branch 上跑 alembic upgrade
4. 跑完整 smoke test 集
5. 通过 → 标记 canary 阶段成功,允许进入生产 fan-out
   失败 → 丢弃 branch,中止部署,告警
```

**Layer 2:Smoke test(部署过程中,per-tenant gate)**

每个租户 alembic 跑完后,**强制**执行一组只读 SQL:

- 关键业务表 `SELECT count(*) FROM agencies / users / token_usage / audit_logs` 不报错
- 新增列查得到(`SELECT new_col FROM ... LIMIT 1`)
- 新约束生效(如 NOT NULL 列上试图插 NULL 应该被拒)
- `SELECT version_num FROM alembic_version` 等于 target

**任一失败 → 不更新 `current_schema_version`**,该租户继续保留旧版本号,告警

**Layer 3:Reconciliation cron(部署后持续验证)**

每小时跑一次 Celery beat 任务:

1. 读控制面 `tenant_databases.target_schema_version`
2. 逐租户 SSH-less 连接,读 `alembic_version.version_num`
3. 三态对账:
   - ✅ **一致**:无操作
   - ⚠️ **注册表先行,实际库未更新**:漂移告警(可能跨 cluster 不同步)
   - 🚨 **实际库先行,注册表未更新**:严重告警(说明绕过了编排器,极不应该发生)
4. 暴露内部端点 `GET /internal/health/schema-versions` 返回 JSON
5. Grafana 仪表盘看"待迁移租户数"趋势

##### 3.2.4 部署流程(端到端时间线)

```
1. Dev push migration PR
       │
2. CI:alembic check + 单测(本地 sqlite/duckdb)
       │
3. Merge → main → Render deploy hook 触发
       │
4. 控制面 DB:alembic upgrade head(单库,直接跑)
       │
5. Canary 阶段:挑 3 个租户 branch 跑迁移 + smoke test
       │  失败 → 中止 + 告警
       ↓ 通过
6. 批量 Celery group(并发 10):
   for each tenant (current_version != target):
     ├─ acquire lock
     ├─ alembic upgrade head
     ├─ smoke test
     ├─ update current_schema_version (only on success)
     └─ release lock
       │
7. chord 回调:汇总 success/failed,发 Slack
       │
8. Reconciliation cron(每小时):对账
       │
9. Grafana 仪表盘归零 = 完全完成
```

##### 3.2.5 工程纪律(进 CONTRIBUTING.md)

| 规则                                               | 理由                                                                             |
| -------------------------------------------------- | -------------------------------------------------------------------------------- |
| 每个 alembic 迁移必须 **backwards-compatible**     | N → N+1 部署窗口中,N 的代码必须与 N+1 schema 共存(滚动部署)                      |
| 加列 → 不带 NOT NULL;后续迁移再补 NOT NULL(2-step) | 防止运行中代码插入失败                                                           |
| 删列 → 先发代码停止读写,后发删除迁移(2-step)       | 防止运行中代码读到不存在列                                                       |
| 改类型 → 加新列 → 双写 → 切读 → 删旧列(4-step)     | 同上                                                                             |
| 大数据回填 **绝不**在迁移里做                      | 锁表风险 — 用独立 Celery 任务分批跑                                              |
| 每个 `upgrade()` 必须提供完整的 `downgrade()`      | Canary 失败时丢弃 branch 依然需要它(Neon branch 销毁也走 downgrade 路径作为备份) |
| 控制面 DB 走**独立** alembic env                   | 不和租户 schema 混用                                                             |

---

## 4. 替代方案与否决理由

| 方案                                               | 否决理由                                                         |
| -------------------------------------------------- | ---------------------------------------------------------------- |
| **单库多租户 + `agency_id` 列过滤**(当前 PSD 默认) | 违反 C-01(HIPAA 物理隔离要求);DSAR 删除难追溯;blast radius 大    |
| **schema-per-tenant(同一 DB)**                     | 仍共用同一 Postgres 实例,资源竞争未根本解决;HIPAA 客户依然不达标 |
| **完全独立的 cluster-per-tenant**                  | 成本爆炸;Neon 的轻量 project + database 已经够用                 |
| **应用层全部用 fan-out 解决聚合**                  | 不可扩展(租户数 > 100 即崩);连接池压力                           |
| **CDC 走 Debezium + Kafka**                        | 项目无 Kafka,新增基础设施过重;Neon logical replication 已足够    |
| **跨库 join 走 postgres_fdw 作为主路径**           | 性能差;不能进生产 API                                            |

---

## 5. 风险与缓解

| ID       | 风险                                          | 概率 | 影响          | 缓解                                                                                                   |
| -------- | --------------------------------------------- | ---- | ------------- | ------------------------------------------------------------------------------------------------------ |
| **R-01** | 租户数增长导致 Logical Replication 订阅数过多 | 中   | 中            | Neon 单 project 上限够用(每 db 一个 subscription);超 100 租户时评估批量复制工具(Fivetran / 自研 batch) |
| **R-02** | 控制面 DB 成为单点故障                        | 低   | 高            | 控制面表数据简单(< 1000 行 / 1 年),走 Neon HA + PITR + 每小时备份到 S3                                 |
| **R-03** | 应用层 fan-out 把连接池打爆                   | 中   | 中            | Semaphore 限并发 10;PgBouncer transaction-mode                                                         |
| **R-04** | 迁移在某个租户库失败,部分租户已升级           | 中   | 中            | 必须 backwards-compatible(N 代码兼容 N+1);失败租户保留旧版,新部署代码兼容混合状态运行                  |
| **R-05** | 复制延迟导致超管报表"看不到刚发生的事"        | 中   | 低            | 用户预期管理(报表标注 "数据有 5 秒延迟");关键场景走 Layer 1 fan-out                                    |
| **R-06** | postgres_fdw 被滥用进生产路径                 | 低   | 高            | 控制面 DB 与 DBA 调试库账号严格分权;CI lint 检查代码中 `FOREIGN TABLE` 引用                            |
| **R-07** | 凭证泄露导致单租户被滥用                      | 低   | 高            | 控制面表只存 Secret reference(不存明文);Secrets Manager 90 天自动轮换                                  |
| **R-08** | DSAR 删除时跨 Snowflake schema 漏删           | 中   | 高(GDPR 罚款) | DSAR pipeline 设计为:删租户 Postgres → 同步删 Snowflake schema → 删 S3 prefix(三步原子化、失败可重试)  |

---

## 6. 复盘触发器(Revisit Triggers)

任一命中即触发本决策重新评估:

- ⏰ **时间**:6 个月后(2026-11-11)
- 📈 **规模**:租户数超过 **100**(应用层 fan-out 已接近上限)
- 💰 **成本**:Neon 月度账单超过 $500
- 🐛 **质量**:Reconciliation 漂移告警超过 1 次 / 月
- 🆕 **能力**:Neon 推出"Multi-tenant query 联邦"原生能力
- ⚖️ **合规**:出现需要跨租户实时强一致 join 的合规需求

---

## 7. 实施清单(Roadmap)

| 任务                                                                  | 类别     | 工时  | 依赖             |
| --------------------------------------------------------------------- | -------- | ----- | ---------------- |
| 新增控制面 Neon 项目 `receptiviq_control` + `tenant_databases` schema | 基础设施 | 0.5 d | —                |
| FastAPI 加 `TenantSession` dependency + 路由中间件                    | 后端     | 1 d   | 控制面 schema    |
| 改造现有 ORM 查询(分批,从 `users` / `audit_logs` 起)                  | 后端     | 2-3 d | TenantSession    |
| Secrets Manager 集成 + 凭证管理                                       | 安全     | 1 d   | —                |
| Neon Logical Replication 配置脚本(per-tenant 一键启)                  | 数据     | 1 d   | 控制面           |
| Snowflake 接收端:per-tenant schema + dbt `mart_global_*`              | 数据     | 1-2 d | LR 配置          |
| Celery `apply_migrations_to_tenant` + 调度入口                        | 后端     | 1 d   | 控制面           |
| Canary deploy 脚本(Neon branch + smoke test 集)                       | DevOps   | 1 d   | Migration runner |
| `/internal/health/schema-versions` 端点 + Reconciliation cron         | 后端     | 0.5 d | —                |
| Grafana 仪表盘(待迁移租户数 · 复制延迟 · fan-out 延迟)                | 监控     | 0.5 d | —                |
| 文档:CONTRIBUTING 新增"多租户迁移规范"                                | 文档     | 0.5 d | —                |
| 单元测试:fan-out 路由 · 迁移幂等性 · smoke test 集                    | QA       | 1.5 d | 主体完成         |

**合计:约 11-13 工作日**(单人,可拆并行至 ~7 工作日)

---

## 8. 与现状代码的差距(待补齐)

| 项                  | 当前状态                        | ADR 要求                    | 工作量    |
| ------------------- | ------------------------------- | --------------------------- | --------- |
| 数据库连接          | 单库 `DATABASE_URL`             | 多库,经控制面查询           | ~1 d      |
| `agency_id` 列过滤  | 所有查询强制带                  | 大部分可移除,仅控制面表保留 | 重构 ~2 d |
| Alembic env         | 单 env                          | 控制面 env + 租户 env 双轨  | ~0.5 d    |
| Logical Replication | ❌                              | 新增                        | ~1 d      |
| 控制面 DB           | ❌                              | 新增                        | ~0.5 d    |
| 迁移编排器          | ❌(手动 `alembic upgrade head`) | Celery 批量                 | ~1 d      |
| Canary 流程         | ❌                              | Neon 分支 + smoke test      | ~1 d      |
| 对账机制            | ❌                              | Reconciliation cron         | ~0.5 d    |

---

## 9. 签署

| 角色              | 姓名           | 日期     | 状态 |
| ----------------- | -------------- | -------- | ---- |
| 技术决策人(CTO)   | ******\_****** | \_\_\_\_ | ⬜   |
| 数据库管理员(DBA) | ******\_****** | \_\_\_\_ | ⬜   |
| 合规官 / DPO      | ******\_****** | \_\_\_\_ | ⬜   |
| 后端架构师        | ******\_****** | \_\_\_\_ | ⬜   |
| DevOps Lead       | ******\_****** | \_\_\_\_ | ⬜   |

---

## 附录 A:与 LLM Selection ADR(ADR-001)的关联

ADR-001 定义了"HIPAA 客户走 AWS Bedrock 旁路"。本 ADR 进一步明确**HIPAA 客户的数据库也必须独立 Neon project**,两者协同实现完整 HIPAA 数据流隔离:

```
HIPAA 客户的数据流:
  ┌──────────────────────────────────────────────────┐
  │  独立 Neon project(EU/US 选项)                  │
  │   ↓ Logical Replication                          │
  │  Snowflake EU region(独立 schema)               │
  │   ↓ dbt                                          │
  │  AI Brain → AWS Bedrock(BAA 覆盖)               │
  │   ↓ trace                                        │
  │  Langfuse self-hosted(不走 Cloud)               │
  └──────────────────────────────────────────────────┘
```

---

## 附录 B:核心术语表

| 术语                    | 含义                                                                     |
| ----------------------- | ------------------------------------------------------------------------ |
| **控制面 DB**           | `receptiviq_control` — 不存业务数据,只放租户注册表 / 全局配置 / 超管账号 |
| **租户 DB**             | `tenant_<uuid>` — 单个 Agency 的所有业务数据                             |
| **Canary 租户**         | 用于预发布迁移测试的代表性租户(3 个)                                     |
| **Reconciliation**      | 定期对账机制:对比注册表 vs 实际库的版本号                                |
| **smoke test 集**       | 迁移后必跑的一组只读 SQL,验证 schema 健康                                |
| **App fan-out**         | 后端并发连接多个租户库,在应用层聚合结果                                  |
| **Logical Replication** | Postgres 原生的发布 / 订阅复制机制                                       |
| **CDC**                 | Change Data Capture — 捕获数据库变更并流向下游                           |
| **postgres_fdw**        | Postgres Foreign Data Wrapper,跨库 join 原生扩展                         |
| **Neon Branch**         | Neon 提供的零成本数据库分叉(秒级创建,COW 存储)                           |

---

## 附录 C:相关文档

- [Neon — Database per Tenant](https://neon.com/use-cases/database-per-tenant)
- [Postgres Logical Replication Docs](https://www.postgresql.org/docs/current/logical-replication.html)
- [docs/PSD-LLM-SELECTION-DECISION.md](./PSD-LLM-SELECTION-DECISION.md) — ADR-001
- [docs/CLIENT-ACCOUNT-CHECKLIST.md](./CLIENT-ACCOUNT-CHECKLIST.md) — Neon 在客户清单中标 P0
- [features/PROJECT-PLAN.md](../features/PROJECT-PLAN.md) — 项目路线图
- [CLAUDE.md](../CLAUDE.md) §Compliance Rules

---

> 文档版本历史
> v1.0 · 2026-05-11 · 初版,定义 Neon 一租户一库架构 + 跨库聚合 + 迁移编排
