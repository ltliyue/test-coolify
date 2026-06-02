# f15-field-mapping 需求文档

> 来源：ETL 转换层需求 + canonical schema 设计
> 状态：MVP P1

## 功能概述

字段映射配置系统。定义各平台原始字段到 canonical schema 的映射规则，支持版本管理和回滚。

## 功能需求

### FR-1: 映射配置 CRUD

- 创建 / 读取 / 更新 / 软删除
- 按 platform 分组
- agency_id 隔离

### FR-2: 版本管理

- 每次更新产生新 version
- 保留历史版本（FieldMappingVersion 表）
- 支持按 version 查询

### FR-3: 版本回滚

- POST `/field-mappings/{id}/rollback/{version}`
- 恢复历史版本为当前激活版本

### FR-4: Transform Engine

- 四种变换：direct / value_mapping / unit_conversion / formula
- 24 个 canonical 标准字段
- 支持 preview（未保存前试运行）

### FR-5: 平台模板

- 6 个平台默认模板：ga4 / meta_ads / hubspot / tiktok_ads / dv360 / stackadapt
- 新建时可基于模板初始化

## 非功能需求

- 映射配置大小 ≤ 4KB（L-02 合规修复）
- 单个映射条目 ≤ 200 条

## 合规要求

- 所有 API 端点带 audit_simple()
- agency_id 隔离
- transform config 不含可执行代码（仅声明式规则）
