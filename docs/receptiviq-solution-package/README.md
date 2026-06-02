# ReceptivIQ Solution Package

本文件夹用于存放 ReceptivIQ 交流分享会与方案评审材料，基于前期访谈、三方系统接入清单，以及当前确认的目标架构整理。

## 文件清单

- [01-technical-solution-description.md](01-technical-solution-description.md)  
  技术方案说明：双湖数据策略、Snowflake 多租户仓库、ELT、Core AI Brain、Priority 1 集成、合规姿态。

- [02-network-diagram.md](02-network-diagram.md)  
  网络与数据流图：外部数据源、PII 隔离边界、ELT、Snowflake、AI Brain、Agents、应用门户之间的数据流。

- [03-architecture-solution-schema.md](03-architecture-solution-schema.md)  
  平台架构 Schema：从数据源层到门户层的完整分层架构，并标注关键约束和优先级依赖。

- [diagrams/](diagrams/)  
  对应图形资产，包含 SVG 图片和 Mermaid 源文件。

## 图形资产

- [High-Level Data Flow](diagrams/01-high-level-data-flow.svg)
- [PII Segregation Architecture](diagrams/02-pii-segregation-architecture.svg)
- [Runtime Request Flow](diagrams/03-runtime-request-flow.svg)
- [Platform Architecture Schema](diagrams/04-platform-architecture-schema.svg)

## Bilingual Versions

- Chinese: [00-solution-package.zh.md](00-solution-package.zh.md)
- English: [00-solution-package.en.md](00-solution-package.en.md)
- Chinese diagrams are available under [diagrams/zh](diagrams/zh/).

## 使用建议

交流分享会可以按以下顺序讲：

1. 先讲 `01`：为什么采用双湖 + Snowflake + AI Brain。
2. 再讲 `02`：用网络图解释数据从哪里来、如何隔离、如何进入 AI。
3. 最后讲 `03`：把架构拆成可实施模块，作为后续 MVP 优先级排序输入。
