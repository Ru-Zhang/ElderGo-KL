# Render 与 Google Cloud SQL 连接文档

本文档说明如何让部署在 **Render** 上的后端服务连接部署在 **Google Cloud SQL for PostgreSQL** 上的 ElderGo KL 数据库。

正确连接结构：

```text
Render Frontend
        -> Render Backend / FastAPI
        -> Google Cloud SQL PostgreSQL
```

前端不能直接连接数据库。数据库连接信息只放在 Render 后端服务的环境变量中。

## 1. Google Cloud SQL 数据库准备

Cloud SQL 建议配置：

```text
数据库类型: PostgreSQL
版本: PostgreSQL 16 或 17
实例规格: shared-core / 最低可选配置
存储: 10 GB
高可用: 关闭
公网 IP: 开启
数据库名: eldergo
```

本地导入数据时，PowerShell 示例：

```powershell
cd D:\Monash_FIT\FIT5120\data_cleaning
.\.venv\Scripts\Activate.ps1

$env:DATABASE_URL="postgresql://postgres:YOUR_PASSWORD@CLOUD_SQL_PUBLIC_IP:5432/eldergo?sslmode=require"
python database\import_to_postgres.py --reset
```

必须保留：

```text
?sslmode=require
```

否则 Cloud SQL 可能拒绝连接并报 `no encryption`。

## 2. 在 Cloud SQL 添加 Render 后端出口 IP

Render 后端连接 Cloud SQL public IP 时，Cloud SQL 必须允许 Render 后端的出口 IP。

在 Render 后端服务页面：

```text
Backend Web Service
-> Connect
-> Outbound
```

复制所有 outbound IP addresses / CIDR ranges。

然后在 Google Cloud：

```text
Cloud SQL
-> 你的 PostgreSQL 实例
-> Connections / 连接
-> Networking / 网络
-> Authorized networks / 已获授权的网络
-> Add network / 添加网络
```

逐个添加 Render 给出的 IP 或 CIDR。

示例：

```text
名称: render-backend-1
IP 范围: xxx.xxx.xxx.xxx/xx
```

如果你还需要从本地电脑导入或调试，也可以临时添加：

```text
名称: my-laptop
IP 范围: YOUR_PUBLIC_IP/32
```

不要添加：

```text
0.0.0.0/0
```

这会允许所有公网 IP 尝试连接数据库，不安全。

## 3. 在 Render 后端设置数据库连接

进入 Render 后端服务：

```text
Backend Web Service
-> Environment
-> Environment Variables
```

添加环境变量：

```text
DATABASE_URL=postgresql://postgres:YOUR_PASSWORD@CLOUD_SQL_PUBLIC_IP:5432/eldergo?sslmode=require
```

如果密码里有特殊字符，例如：

```text
@ # : / ? & %
```

建议重置成只包含字母和数字的密码，或者对密码做 URL encode。

后端代码只从环境变量读取数据库地址：

```python
import os

DATABASE_URL = os.environ["DATABASE_URL"]
```

`psycopg` 示例：

```python
import os
import psycopg

with psycopg.connect(os.environ["DATABASE_URL"]) as conn:
    with conn.cursor() as cur:
        cur.execute("SELECT COUNT(*) FROM rail_stations")
        count = cur.fetchone()[0]
```

## 4. Render 前端如何连接

Render 前端只需要知道后端 API 地址。

Vite 示例：

```text
VITE_API_BASE_URL=https://YOUR_BACKEND_SERVICE.onrender.com
```

前端请求示例：

```text
GET https://YOUR_BACKEND_SERVICE.onrender.com/locations/search?q=KL Sentral
POST https://YOUR_BACKEND_SERVICE.onrender.com/routes/recommend
```

不要在前端设置或暴露：

```text
DATABASE_URL
```

## 5. FastAPI CORS 设置

后端需要允许 Render 前端域名访问。

```python
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://YOUR_FRONTEND_SERVICE.onrender.com",
        "http://localhost:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

## 6. 后端数据库连通性测试接口

建议在 FastAPI 后端添加一个健康检查接口：

```python
import os
import psycopg
from fastapi import FastAPI

app = FastAPI()

@app.get("/health/db")
def db_health():
    with psycopg.connect(os.environ["DATABASE_URL"]) as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT COUNT(*) FROM rail_stations")
            rail_station_count = cur.fetchone()[0]
    return {"rail_stations": rail_station_count}
```

部署后访问：

```text
https://YOUR_BACKEND_SERVICE.onrender.com/health/db
```

预期返回类似：

```json
{
  "rail_stations": 358
}
```

## 7. Cloud SQL 验证 SQL

可以在 Cloud SQL Studio 中运行：

```sql
SELECT COUNT(*) FROM rail_stations;
SELECT COUNT(*) FROM accessibility_points;
SELECT COUNT(*) FROM searchable_locations;
SELECT postgis_full_version();
```

搜索测试：

```sql
SELECT location_id, location_type, display_name, accessibility_status, confidence
FROM searchable_locations
WHERE display_name ILIKE '%KL Sentral%'
LIMIT 20;
```

空间查询测试：

```sql
SELECT
    station.station_name,
    point.name,
    point.feature_type,
    point.accessibility_type,
    ROUND(ST_Distance(station.geom::geography, point.geom::geography)) AS distance_m
FROM rail_stations station
JOIN accessibility_points point
  ON ST_DWithin(station.geom::geography, point.geom::geography, 50)
WHERE station.station_name ILIKE '%KL Sentral%'
ORDER BY distance_m
LIMIT 20;
```

## 8. 常见问题

### password authentication failed

检查：

```text
DATABASE_URL 用户名是否正确
DATABASE_URL 密码是否正确
密码是否包含需要 URL encode 的特殊字符
Cloud SQL 用户密码是否已重置成功
```

### no encryption

连接字符串末尾加：

```text
?sslmode=require
```

### connection timeout

检查：

```text
Cloud SQL public IP 是否开启
Render backend outbound IP 是否已加入 Cloud SQL authorized networks
Cloud SQL 实例是否正在运行
Render 后端服务 region 是否变化
```

### CORS error

检查：

```text
FastAPI allow_origins 是否包含 Render 前端 URL
前端 API base URL 是否指向后端，而不是数据库
```

## 9. 安全注意事项

- `DATABASE_URL` 只放在 Render 后端环境变量里。
- 不要把数据库密码提交到 GitHub。
- 不要让前端知道 PostgreSQL 连接字符串。
- 不要在 Cloud SQL authorized networks 中使用 `0.0.0.0/0`。
- 本地导入完成后，可以删除 `my-laptop` 授权网络。
- 课设结束后如果不再使用，删除 Cloud SQL 实例，避免继续计费。
