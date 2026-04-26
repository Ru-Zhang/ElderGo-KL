# Data Plan 交互审计（当前实现）

本文基于 `doc/DATA_PLAN_CN.md` 第 8 节，对当前代码中的前端、后端、数据库交互进行审计，并标注风险等级与处理状态。

## 已对齐项

- 前端统一通过后端 REST API 访问数据，不直连数据库。
- `locations` 查询链路已经走 PostgreSQL（含 `searchable_locations`、`rail_routes`、`station_accessibility_profiles`）。
- ETL 导入流程覆盖 Data plan 第 7 节定义的静态表（`rail_*`、`accessibility_points`、`station_accessibility_profiles`、`searchable_locations`）。

## 关键差异与风险

| 差异项 | 风险 | 当前状态 |
|---|---|---|
| 用户缓存此前只在进程内字典，重启丢失 | 高 | 已修复：接入 `anonymous_users`、`user_ui_settings`、`user_travel_preferences` |
| 路线推荐结果此前未写入运行时表 | 高 | 已修复：接入 `route_requests`、`recommended_routes`、`route_steps`、`route_accessibility_annotations` |
| 文档中的用户接口写法与实现存在差异（`resolve`/`PUT` vs `anonymous`/`PATCH`） | 中 | 待同步文档契约或统一接口 |
| schema 路径易混淆（历史文档提到 `backend/sql/001_init_schema.sql`） | 中 | 已收敛：以 `backend/database/schema.sql` 为唯一来源 |

## 本次代码落实范围

- 用户缓存落库：
  - `backend/app/services/user_service.py`
  - `backend/app/api/v1/endpoints/users.py`
- 路线结果落库：
  - `backend/app/services/route_service.py`

## 仍建议后续跟进

- 将 `DATA_PLAN_CN.md` 第 8 节中的用户接口路径/方法与现状统一。
- 补充数据库集成测试，验证推荐路线写入后字段完整性（尤其 annotation 字段约束）。
