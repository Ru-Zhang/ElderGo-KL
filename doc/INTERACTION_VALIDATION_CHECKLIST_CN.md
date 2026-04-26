# 前后端与数据库联调验证清单

用于验证 Data plan 第 8 节的关键链路是否可用。

## A. 环境与数据库

- [ ] 后端 `.env` 中 `ELDERGO_DATABASE_URL` 可连接（建议带 `sslmode=require`）。
- [ ] 执行 `python backend/database/import_to_postgres.py --reset` 成功。
- [ ] `rail_stations`、`accessibility_points`、`searchable_locations` 行数大于 0。

## B. 用户缓存链路

- [ ] `POST /users/anonymous` 返回 `anonymous_user_id`（UUID 字符串）。
- [ ] `GET /users/{id}/ui-settings` 返回默认或已保存设置。
- [ ] `PATCH /users/{id}/ui-settings` 后再次 `GET` 值一致。
- [ ] `GET /users/{id}/travel-preferences` 返回默认或已保存偏好。
- [ ] `PATCH /users/{id}/travel-preferences` 后再次 `GET` 值一致。
- [ ] 数据库中存在对应记录：
  - `anonymous_users`
  - `user_ui_settings`
  - `user_travel_preferences`

## C. 站点与设施搜索链路

- [ ] `GET /locations/search?q=KL Sentral` 返回结果。
- [ ] `GET /locations/{location_id}` 返回 `accessibility_status` 与 `confidence`。
- [ ] `GET /locations/popular` 返回站点列表。

## D. 路线推荐与注释链路

- [ ] `POST /routes/recommend` 返回 `recommended_route_id` 与 `steps`。
- [ ] 返回 `steps[].annotation` 字段完整（`status/message/source`）。
- [ ] 数据库新增记录：
  - `route_requests`
  - `recommended_routes`
  - `route_steps`
  - `route_accessibility_annotations`
- [ ] `recommended_routes.recommended_route_id` 与 API 返回值一致。

## E. 关键失败场景

- [ ] Google Maps key 缺失时，接口返回可识别错误（非静默失败）。
- [ ] 数据库不可用时，后端日志可定位到 SQL 失败点。
- [ ] 异常请求体（缺必填字段）返回 4xx，不返回 200。
