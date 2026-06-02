# F-16 客户门户 — 测试执行报告

- **测试时间**：2026-03-31
- **测试环境**：macOS，Python 3.9.6，PostgreSQL（receptiviq@localhost:5432/receptiviq）
- **测试命令**：`PYTHONPATH=. DATABASE_URL=postgresql+asyncpg://receptiviq:receptiviq@localhost:5432/receptiviq python3 -m pytest tests/test_portal.py -v`
- **测试结果**：✅ 8/8 通过，0 失败，0 跳过

---

## 测试用例执行明细

| #   | 测试用例                            | 结果      | 说明                                                 |
| --- | ----------------------------------- | --------- | ---------------------------------------------------- |
| 1   | `test_portal_dashboard`             | ✅ PASSED | 返回 brand/persona_count/creative_count/report_count |
| 2   | `test_portal_brand`                 | ✅ PASSED | 返回品牌配置字段（白标用）                           |
| 3   | `test_portal_brand_reflects_update` | ✅ PASSED | PUT brands/config 后 portal/brand 反映更新           |
| 4   | `test_portal_personas`              | ✅ PASSED | 精简视图，不暴露 model_used/source                   |
| 5   | `test_portal_creatives`             | ✅ PASSED | 精简视图，含 platforms 列表                          |
| 6   | `test_portal_reports`               | ✅ PASSED | 精简视图，不暴露 results/model_used                  |
| 7   | `test_portal_dashboard_counts`      | ✅ PASSED | 创建资源后 dashboard 计数联动增加                    |
| 8   | `test_portal_requires_auth`         | ✅ PASSED | 无 JWT 返回 401                                      |

---

## 总结

- **5 个只读端点**：dashboard/brand/personas/creatives/reports
- **白标支持**：client_viewer 优先取 client.brand_config，fallback 到 agency
- **数据隔离**：所有查询按 agency_id 过滤
- **精简视图**：不暴露内部字段（model_used/source/cost 等）
- **全量回归**：135/135 通过（8 新增 + 127 回归），0 失败
