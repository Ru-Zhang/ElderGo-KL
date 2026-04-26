# 数据库 Schema 唯一来源约束

为避免初始化脚本混用导致表结构不一致，当前项目数据库结构以如下文件作为唯一来源：

- `backend/database/schema.sql`

## 约束规则

- 初始化数据库、重建环境、CI 校验时，统一使用上述文件。
- ETL 导入仅使用：
  - `backend/database/import_to_postgres.py`
- 若需变更表结构，先更新 `backend/database/schema.sql`，再同步更新：
  - 受影响的后端 SQL 读写逻辑
  - Data plan 文档中的字段说明

## 推荐初始化流程

1. 配置 `DATABASE_URL`（或后端 `ELDERGO_DATABASE_URL`）。
2. 执行：
   - `python backend/database/import_to_postgres.py --reset`
3. 验证核心表与索引存在后，再启动后端服务。

## 禁止事项

- 不再使用或新增并行的 `backend/sql/001_init_schema.sql` 作为生产初始化入口。
- 不允许在多个 schema 文件中手工维护同一批表定义。
