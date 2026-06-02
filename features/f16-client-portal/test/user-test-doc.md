# f16-client-portal 用户测试文档

测试文件：`backend/tests/test_portal.py`（8 用例）

## TC-01: Dashboard

| 步骤                          | 预期           |
| ----------------------------- | -------------- |
| GET /portal/dashboard         | 200, 含 counts |
| agency_admin 看全 agency      | ✅             |
| client_viewer 仅看自己 client | ✅             |

## TC-02: Brand 配置

| 步骤              | 预期                              |
| ----------------- | --------------------------------- |
| GET /portal/brand | 200, 返回当前 client brand_config |
| 更新 brand 后 GET | 反映最新                          |

## TC-03: Personas 简化视图

| 步骤                        | 预期                       |
| --------------------------- | -------------------------- |
| GET /portal/personas        | 200, 字段较 /personas 精简 |
| 无 model_used / source 暴露 | ✅                         |

## TC-04: Creatives

| 步骤                  | 预期      |
| --------------------- | --------- |
| GET /portal/creatives | 200, 列表 |

## TC-05: Reports

| 步骤                | 预期              |
| ------------------- | ----------------- |
| GET /portal/reports | 200, 归因报告列表 |

## TC-06: Counts 数据

| 测试                           | 预期 |
| ------------------------------ | ---- |
| dashboard.personas_count 正确  | ✅   |
| dashboard.creatives_count 正确 | ✅   |

## TC-07: 认证

| 步骤     | 预期 |
| -------- | ---- |
| 无 token | 401  |

## TC-08: 租户隔离

| 测试                          | 预期             |
| ----------------------------- | ---------------- |
| client_viewer 查看其他 client | 403 或只返回自己 |
