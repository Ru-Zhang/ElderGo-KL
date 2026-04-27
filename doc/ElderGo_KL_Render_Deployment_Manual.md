# ElderGo KL Render 部署手册

## 项目概述

ElderGo KL 是一个为老年用户设计的吉隆坡出行规划应用，包含前端界面和后端API。后端使用FastAPI框架，前端使用React + Vite构建。

## 部署架构

- **后端服务**: Python FastAPI API，使用免费Web服务
- **前端服务**: React静态站点，使用免费静态站点
- **数据库**: PostgreSQL，使用免费数据库实例

## 免费档位兼容性检查

✅ **兼容** - 该项目完全适合Render免费档位：
- 后端依赖轻量（FastAPI, SQLAlchemy, PostgreSQL）
- 前端为静态站点，无需服务器端渲染
- 数据库使用标准PostgreSQL，无特殊要求
- 资源使用预计在免费限制内（750小时/月，1GB RAM）

## 手动部署步骤

### 1. 准备工作

1. 确保代码已推送到GitHub仓库
2. 准备必要的API密钥：
   - Google Maps API Key
   - OpenWeather API Key
3. 确认render.yaml配置正确（已在项目根目录）

### 2. 创建Render账户

1. 访问 [render.com](https://render.com)
2. 使用GitHub账户注册或创建新账户
3. 验证邮箱

### 3. 连接GitHub仓库

1. 在Render Dashboard中，点击 "New" > "Blueprint"
2. 选择 "Connect GitHub" 并授权Render访问你的仓库
3. 搜索并选择你的ElderGo-KL仓库

### 4. 创建PostgreSQL数据库

1. 在Render Dashboard中，点击 "New" > "PostgreSQL"
2. 选择免费计划
3. 设置数据库名称（如：eldergo-kl-db）
4. 记录生成的数据库URL（格式：postgresql://user:password@host:port/database）

### 5. 部署后端服务

1. 在Blueprint部署中，Render会自动识别render.yaml
2. 或者手动创建Web服务：
   - Service Type: Web Service
   - Runtime: Python
   - Build Command: `pip install -r backend/requirements.txt`
   - Start Command: `gunicorn app.main:app --chdir backend -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:$PORT`
3. 设置环境变量：
   - `ELDERGO_ENV`: production
   - `ELDERGO_DEMO_MODE`: true
   - `ELDERGO_CORS_ORIGINS`: https://your-frontend-url.onrender.com
   - `ELDERGO_DATABASE_URL`: [从步骤4获取的数据库URL]
   - `ELDERGO_GOOGLE_MAPS_API_KEY`: [你的Google Maps API Key]
   - `OPENWEATHER_API_KEY`: [你的OpenWeather API Key]

### 6. 部署前端服务

1. 创建新的静态站点服务：
   - Service Type: Static Site
   - Build Command: `cd frontend && npm ci && npm run build`
   - Publish Directory: `frontend/dist`
2. 设置环境变量：
   - `VITE_API_BASE_URL`: https://your-api-url.onrender.com
   - `VITE_GOOGLE_MAPS_API_KEY`: [你的Google Maps API Key]
3. 配置重定向规则（在render.yaml中已配置）：
   - 所有路由重定向到index.html（SPA支持）

### 7. 配置服务关联

1. 确保前端的CORS设置允许后端域名
2. 更新后端的CORS_ORIGINS环境变量为前端URL
3. 测试API调用是否正常

### 8. 数据库初始化

1. 部署后，连接到数据库
2. 运行database/schema.sql创建表结构
3. 运行database/import_to_postgres.py导入数据

### 9. 测试部署

1. 访问前端URL确认界面正常
2. 测试API端点：https://your-api-url.onrender.com/api/v1/health
3. 测试主要功能（路线规划、地点搜索等）

## 注意事项

### 免费档位限制
- 每月750小时运行时间
- Web服务自动休眠（冷启动时间约10-30秒）
- 数据库每月750小时

### 环境变量安全
- 不要在代码中硬编码API密钥
- 使用Render的环境变量管理
- 定期轮换API密钥

### 监控和维护
- 监控Render Dashboard的使用情况
- 设置健康检查端点（已配置：/api/v1/health）
- 定期检查日志

### 故障排除
- 如果部署失败，检查build logs
- 确认所有环境变量正确设置
- 验证数据库连接字符串格式

## 升级到付费档位

如果需要更高可用性或更多资源：
- Web服务升级到Starter ($7/月) 或更高
- 数据库升级到Starter ($7/月) 或更高
- 付费服务无休眠时间，更高性能

## 联系支持

如遇问题，请参考：
- Render文档：https://docs.render.com/
- 项目GitHub Issues</content>
<parameter name="filePath">d:\Monash_FIT\FIT5120\iteration2\ElderGo-KL\doc\ElderGo_KL_Render_Deployment_Manual.md