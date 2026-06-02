# F-12 Attribution Agent — 测试执行报告

- **测试时间**：2026-03-31
- **测试环境**：macOS，Python 3.9.6，PostgreSQL（receptiviq@localhost:5432/receptiviq）
- **测试命令**：`PYTHONPATH=. DATABASE_URL=postgresql+asyncpg://receptiviq:receptiviq@localhost:5432/receptiviq python3 -m pytest tests/test_attribution.py -v`
- **测试结果**：✅ 9/9 通过，0 失败，0 跳过

---

## 测试用例执行明细

### F-12：Attribution Agent（test_attribution.py）

| #   | 测试用例                               | 结果      | 说明                                         |
| --- | -------------------------------------- | --------- | -------------------------------------------- |
| 1   | `test_generate_attribution_report`     | ✅ PASSED | 生成归因报告，status=completed，results 非空 |
| 2   | `test_attribution_report_has_results`  | ✅ PASSED | results 含 channels 或 attribution_model     |
| 3   | `test_list_attribution_reports`        | ✅ PASSED | 生成后列表非空                               |
| 4   | `test_get_attribution_report_by_id`    | ✅ PASSED | GET /{id} 返回正确报告                       |
| 5   | `test_get_nonexistent_report_404`      | ✅ PASSED | 不存在的 ID 返回 404                         |
| 6   | `test_attribution_with_date_range`     | ✅ PASSED | 日期范围参数正确存储和返回                   |
| 7   | `test_attribution_report_has_insights` | ✅ PASSED | insights 字段非空（来自 LLM 推荐摘要）       |
| 8   | `test_attribution_requires_auth`       | ✅ PASSED | 无 JWT 返回 401                              |
| 9   | `test_attribution_bound_to_agency`     | ✅ PASSED | agency_id 与当前用户匹配                     |

---

## 总结

- **3 个 API 端点**：POST /report, GET /reports, GET /reports/{id}
- **归因模型**：multi_touch/last_click/first_click/custom
- **DuckDB 集成**：从仓库查询实际数据作为 LLM 上下文
- **AI 分析**：调用 Attribution Agent（Claude Sonnet），无 API key 时返回 mock 报告
- **全量回归**：118/118 通过（9 新增 + 109 回归），0 失败
