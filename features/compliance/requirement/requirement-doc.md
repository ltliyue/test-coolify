# compliance 需求文档

> 来源：Dev Brief v2 §Non-Functional Requirements + 合规顶层策略
> 状态：F-00 基础层，所有模块的前置依赖

## 功能概述

实现 GDPR + CCPA + HIPAA 三法规同时满足的合规基础层。合规不是附加功能，而是所有开发决策的前置架构约束（Privacy by Design）。

## 功能需求

### FR-1: 数据匿名化工具

- SHA-256 哈希用户标识符（含租户盐值）
- IP 地址截断（IPv4 /24，IPv6 /48）
- Email 掩码（日志展示用）
- 批量入仓前的记录级匿名化

### FR-2: PHI 检测

- 扫描 HIPAA Safe Harbor 18 类标识符
- 检测到 PHI 时记录警告日志
- Safe Harbor de-identification 去标识化

### FR-3: HIPAA 会话超时

- 15 分钟不活动自动超时
- Redis-backed + 内存 LRU fallback
- 中间件层自动 extend TTL

### FR-4: DSAR 数据主体请求

- access（访问）/ delete（删除）/ export（导出）/ rectify（更正）/ restrict（限制）
- SLA：GDPR 30天 / CCPA 45天 / HIPAA 30天
- 删除时保留审计痕迹本身

### FR-5: 同意记录管理

- 记录同意的 purpose、granted、consent_text 快照
- 存储 subject_hash 而非明文 email
- 支持随时撤回

### FR-6: 审计日志

- INSERT-only（数据库触发器强制）
- 覆盖所有 API 端点、仓库读写、PHI 访问
- 保留 6 年（三法规最严值）

## 非功能需求

- 加密传输：TLS 1.3
- 静态加密：AES-256（Fernet）
- 每个 Agency 独立加密密钥（目标架构）
- 数据保留策略取三法规最严值

## 合规规则映射

完整 18 条规则见 `CLAUDE.md` 合规章节，来源 `features/compliance/architecture.md` 顶层策略。
