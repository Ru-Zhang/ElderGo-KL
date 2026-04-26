# ElderGo KL 建设计划（中文版本）

## 1. 本文件目的

这份建设计划把 **ElderGo KL Analysis and Design** 文件和 **DATA_PLAN_EN.md** 转换成一个可以给 Cursor、Codex 和开发团队使用的实际开发流程。

主要目标是确保产品可以满足团队已经设计好的：

- Epic
- User Story
- Acceptance Criteria
- DATA_PLAN 中的数据架构

核心决定是：

```text
Figma 决定 ElderGo KL 长什么样。
DATA_PLAN 决定 ElderGo KL 怎么工作。
FastAPI 负责连接前端、Google Maps 和 PostgreSQL/PostGIS。
```

这代表团队不需要推翻 Figma UI。现在的 Figma 设计可以继续使用，但要把它从“静态界面”转换成可以重复使用的 React 组件，并且连接到 DATA_PLAN 所描述的后端和数据库流程。

---

## 2. 产品方向总结

ElderGo KL 是一个面向 Klang Valley 老年人的友好型公共交通路线规划 Web 系统。目标用户主要是视力较弱、行动较慢、数字能力较低，甚至可能有语言障碍的长者。

产品应该通过以下方式降低用户压力：

- 简单清楚的界面
- 大字体
- 清楚的底部导航
- 减少操作步骤
- 不显示太多路线选项
- 只推荐一个最适合的路线
- 清楚显示可达性 / 无障碍信息

产品应该支持：

- 大字体切换
- English / Bahasa Melayu 语言切换
- 固定底部导航
- 个人出行偏好设置
- 起点和终点输入，并支持 Google autocomplete
- 选择出行时间后才推荐路线
- 最终只显示一个推荐路线
- 路线步骤和车站的无障碍提示
- 车站搜索和车站详情页
- 使用说明、买票、Concession、Privacy 等帮助页面
- 将路线保存成图片
- 通过 WhatsApp 或复制链接分享路线给家人
- 只回答交通相关问题的受控 AI 助手
- 第一次使用时的 onboarding 引导

最重要的原则是：

```text
系统不能编造 accessibility、ticket、station 或 route 信息。
```

如果某些 accessibility 数据缺失，应该显示：

```text
unknown
limited information
not yet verified
```

不要把缺失数据当成“不支持”。

---

## 3. 技术架构

建议架构如下：

```text
React / TypeScript Frontend
        ↓ REST API
FastAPI Backend
        ↓ SQL / ORM
PostgreSQL + PostGIS
        ↓
Static rail data + accessibility data + route result records

Google Maps API 在运行时负责：
- autocomplete
- place details
- geocoding
- candidate routes
- transit steps
- walking steps
- map polyline
```

前端不能直接连接 PostgreSQL。所有数据库读写都应该通过 FastAPI 完成。

---

## 4. Figma 和 DATA_PLAN 的关系

### 4.1 目前 Figma 的优点

现在提供的 Figma 画面已经覆盖了很多设计好的功能：

| Figma 画面 | 对应 Epic / 功能 |
|---|---|
| 有起点、终点、Search 的 Planning 页面 | Epic 3：路线输入和时间选择 |
| Accessibility first、Least walk、Fewest transfers 的 Preference 页面 | Epic 2：个人化出行偏好 |
| Chatbot bottom sheet | Epic 8：受控 AI 出行助手 |
| Help 页面：Use ElderGo、Buy Ticket、Apply for Concession、Privacy Info | Epic 7：帮助和长者优惠信息 |
| Station 页面：搜索和 Popular Stations | Epic 6：车站搜索和发现 |
| 顶部 BM 和 A+ 按钮 | Epic 1：语言和字体适配 |
| 底部导航 | Epic 1：固定全局导航 |

所以视觉方向是可以保留的，不需要重新设计。

### 4.2 需要做的技术转变

目前 Figma 导出的代码不能只停留在静态页面。需要转成数据驱动结构：

```text
Static Figma screen
        ↓
Reusable React component
        ↓
Connected to AppContext
        ↓
Connected to frontend API service layer
        ↓
Connected to FastAPI backend
        ↓
Connected to PostgreSQL/PostGIS and Google Maps API
```

例子：

- Station 页面不能永远 hardcode “KL Sentral”、“Pasar Seni”、“Bukit Bintang”、“SunU-Monash”。这些可以先作为 temporary fallback data，但正式版本应该 call `/locations/popular` 和 `/locations/search`。
- Preference 页面不能只把 toggles 存在 React state。它应该保存到 `/users/{anonymous_user_id}/travel-preferences`。
- Chatbot 按钮视觉上可以继续放在底部中间，但技术上应该打开 overlay / bottom sheet，而不是跳转到另一个页面。这样用户关闭 chatbot 后，原本页面状态不会丢失。
- Language 和 font 按钮应该更新整个 app，但不能清空用户已经输入的起点、终点或其他资料。

---

## 5. 建议项目结构

```text
eldergo-kl/
│
├── frontend/
│   ├── src/
│   │   ├── app/
│   │   │   ├── App.tsx
│   │   │   ├── AppProvider.tsx
│   │   │   └── types.ts
│   │   │
│   │   ├── components/
│   │   │   ├── layout/
│   │   │   │   ├── TopBar.tsx
│   │   │   │   ├── BottomNav.tsx
│   │   │   │   └── AppShell.tsx
│   │   │   │
│   │   │   ├── common/
│   │   │   │   ├── ElderButton.tsx
│   │   │   │   ├── ElderCard.tsx
│   │   │   │   ├── ToggleRow.tsx
│   │   │   │   ├── ErrorState.tsx
│   │   │   │   └── LoadingState.tsx
│   │   │   │
│   │   │   └── chatbot/
│   │   │       └── AIChatbotSheet.tsx
│   │   │
│   │   ├── pages/
│   │   │   ├── PlanningPage.tsx
│   │   │   ├── PlanYourTimePage.tsx
│   │   │   ├── RouteResultPage.tsx
│   │   │   ├── PreferencePage.tsx
│   │   │   ├── StationsHomePage.tsx
│   │   │   ├── StationDetailPage.tsx
│   │   │   ├── HelpPage.tsx
│   │   │   ├── UseElderGoPage.tsx
│   │   │   ├── TicketGuidePage.tsx
│   │   │   ├── ConcessionGuidePage.tsx
│   │   │   └── PrivacyInfoPage.tsx
│   │   │
│   │   ├── services/
│   │   │   ├── api.ts
│   │   │   ├── usersApi.ts
│   │   │   ├── routesApi.ts
│   │   │   ├── locationsApi.ts
│   │   │   ├── aiApi.ts
│   │   │   └── googlePlaces.ts
│   │   │
│   │   ├── i18n/
│   │   │   ├── en.json
│   │   │   └── ms.json
│   │   │
│   │   └── utils/
│   │       ├── deviceId.ts
│   │       ├── routeImageExport.ts
│   │       └── shareRoute.ts
│   │
│   └── package.json
│
├── backend/
│   ├── app/
│   │   ├── main.py
│   │   ├── db.py
│   │   ├── models/
│   │   ├── schemas/
│   │   ├── routers/
│   │   │   ├── users.py
│   │   │   ├── locations.py
│   │   │   ├── routes.py
│   │   │   ├── ai.py
│   │   │   └── content.py
│   │   │
│   │   └── services/
│   │       ├── google_maps_service.py
│   │       ├── route_scoring_service.py
│   │       ├── accessibility_annotation_service.py
│   │       ├── station_matching_service.py
│   │       └── ai_guardrail_service.py
│   │
│   ├── etl/
│   │   ├── import_gtfs.py
│   │   ├── import_accessibility_points.py
│   │   ├── build_station_accessibility_profiles.py
│   │   └── sync_searchable_locations.py
│   │
│   ├── sql/
│   │   └── 001_init_schema.sql
│   │
│   └── requirements.txt
│
└── docker-compose.yml
```

---

## 6. 后端需要的数据表

后端数据库应该严格跟随 DATA_PLAN_EN.md。

### 6.1 Business Tables

```text
rail_agencies
rail_routes
rail_stations
rail_station_routes
accessibility_points
station_accessibility_profiles
route_requests
recommended_routes
route_steps
route_accessibility_annotations
searchable_locations
```

### 6.2 User Cache Tables

```text
anonymous_users
user_ui_settings
user_travel_preferences
recent_place_cache
ai_conversations
ai_messages
```

### 6.3 PostgreSQL 需要开启的 extensions

```sql
CREATE EXTENSION IF NOT EXISTS postgis;
CREATE EXTENSION IF NOT EXISTS pg_trgm;
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
```

### 6.4 重要数据库规则

系统应该只储存最终被选中的推荐路线，不应该储存 Google 返回的全部 candidate routes。

Candidate routes 可以暂时存在 backend memory 里用来评分，但最后只有选中的路线应该存到：

```text
recommended_routes
route_steps
route_accessibility_annotations
```

---

## 7. 完整建设流程

## Phase 1 — 稳定 Figma 前端外壳

### 目标

把 Figma UI 转成可重复使用的 mobile-first React app shell。

### 需要建设的内容

- `TopBar`
- `BottomNav`
- `AppShell`
- `AppProvider`
- 全局字体大小模式
- 全局语言模式
- chatbot overlay trigger

### 覆盖的 Acceptance Criteria

- Epic 1：字体大小切换
- Epic 1：语言切换
- Epic 1：固定底部导航
- Epic 8：手动打开 AI assistant，同时不丢失当前页面状态

### Cursor / Codex Prompt

```text
Refactor the current React Figma-exported ElderGo KL UI into a reusable mobile-first app shell.

Requirements:
1. Keep the visual style close to the Figma screenshots.
2. Create TopBar, BottomNav, and AppShell components.
3. Keep Planning, Preference, Station, Help, and Chatbot trigger visible from all main pages.
4. The Chatbot button should open AIChatbotSheet as an overlay or bottom sheet, not navigate away from the current page.
5. Implement font size modes: standard, large, extra_large.
6. Implement language mode: en and ms.
7. Store language and font size in AppContext first; API connection will be added later.
8. Ensure no horizontal scrolling or clipped text when font size changes.
```

---

## Phase 2 — 建立后端数据库 schema

### 目标

在连接路线规划和车站搜索之前，先建立 PostgreSQL/PostGIS schema。

### 需要建设的内容

- `sql/001_init_schema.sql`
- FastAPI `/health` endpoint
- database connection setup
- SQLAlchemy 或 SQLModel models
- spatial indexes 和 search indexes

### Cursor / Codex Prompt

```text
Create the FastAPI backend database foundation for ElderGo KL based strictly on DATA_PLAN_EN.md.

Requirements:
1. Use FastAPI, SQLAlchemy or SQLModel, PostgreSQL, and PostGIS.
2. Create sql/001_init_schema.sql.
3. Enable postgis, pg_trgm, and uuid-ossp extensions.
4. Create all business tables and user cache tables from DATA_PLAN_EN.md.
5. Add GIST indexes for geometry columns and GIN trigram indexes for station/search names.
6. Do not add Supabase-specific code.
7. Do not let frontend connect directly to database.
8. Add /health endpoint.
```

---

## Phase 3 — 建立 ETL Pipeline

### 目标

把静态 rail 数据和 accessibility 数据导入 PostgreSQL/PostGIS。

### ETL Workflow

```text
KTMB GTFS + Rapid Rail GTFS
        ↓
rail_agencies
rail_routes
rail_stations
rail_station_routes

accessibility_feature_clean.csv
        ↓
accessibility_points

rail_stations + accessibility_points
        ↓
station_accessibility_profiles

rail_stations + accessibility_points
        ↓
searchable_locations
```

### 重要规则

缺失的 accessibility data 必须显示为：

```text
unknown
```

不要显示成：

```text
not_supported
```

### Cursor / Codex Prompt

```text
Implement the ETL scripts for ElderGo KL.

Requirements:
1. Read KTMB GTFS agency.csv, routes.csv, stops.csv, trips.csv, and stop_times.csv.
2. Read Rapid Rail GTFS agency.csv, routes.csv, stops.csv, trips.csv, and stop_times.csv.
3. Insert agencies, routes, stations, and station-route relationships.
4. Read accessibility_feature_clean.csv.
5. Import only Point geometries into accessibility_points.
6. Convert lat/lon and WKT to PostGIS geometry SRID 4326.
7. Generate station_accessibility_profiles:
   - Rapid Rail isOKU=true => supported, high confidence.
   - wheelchair=yes point within 50m => supported, medium confidence.
   - no explicit data => unknown, low confidence.
8. Sync rail_stations and accessibility_points into searchable_locations.
9. Never create fake stations when stop_times references a missing stop_id.
```

---

## Phase 4 — 建立匿名用户、设置、偏好和 onboarding

### 目标

让 app 记住用户的语言、字体大小、onboarding 状态和出行偏好。

### 后端 Endpoints

```text
POST /users/resolve
GET /users/{anonymous_user_id}/settings
PUT /users/{anonymous_user_id}/ui-settings
PUT /users/{anonymous_user_id}/travel-preferences
```

### 前端流程

```text
First app load
    → read or generate local device_id
    → POST /users/resolve
    → receive anonymous_user_id
    → restore language, font size, onboarding_completed, and preferences
```

### 覆盖的 Acceptance Criteria

- Epic 1：语言和字体状态保存
- Epic 2：偏好保存，并持续生效
- Epic 9：第一次使用 onboarding

### Cursor / Codex Prompt

```text
Implement anonymous user settings for ElderGo KL.

Backend:
1. Add POST /users/resolve.
2. Hash device_id before storing it.
3. Create anonymous_users, user_ui_settings, and user_travel_preferences if missing.
4. Return anonymous_user_id, language_code, font_size_mode, onboarding_completed, and travel preferences.
5. Add PUT endpoints for UI settings and travel preferences.

Frontend:
1. Generate or read device_id from localStorage.
2. Call /users/resolve on app start.
3. Restore language, font size, onboarding status, and preferences.
4. The language switch must not reset current page input values.
5. The font switch must cycle standard → large → extra_large → standard.
6. Preference save should update backend and immediately affect later route recommendations.
```

---

## Phase 5 — 建立 Station 模块

### 为什么要先做 Station，而不是先做路线规划？

Station search 比 route planning 更容易先测试，而且之后 route planning 也需要 station accessibility profiles 来做 route annotation。

### 后端 Endpoints

```text
GET /locations/popular
GET /locations/search?q=KL Sentral
GET /locations/{location_id}
```

### 使用的数据表

```text
searchable_locations
rail_stations
station_accessibility_profiles
accessibility_points
```

### Station Detail 需要显示的字段

Analysis and Design 文件希望 Station Detail 页面显示：

- station name
- accessibility support status
- ticket counter information
- operating hours

但是 DATA_PLAN_EN.md 目前没有定义 ticket counter 和 operating hours 字段。因此 MVP 应该显示：

```text
Ticket counter: Not yet verified
Operating hours: Not yet verified
```

这样仍然符合 acceptance criteria，因为缺失字段应该明确显示，而不是隐藏起来。

### Cursor / Codex Prompt

```text
Build the Stations module.

Backend:
1. Implement GET /locations/popular returning Top 4 popular stations.
2. Implement GET /locations/search?q=... using searchable_locations and trigram search.
3. Implement GET /locations/{location_id}.
4. For rail_station details, return station_name, accessibility_status, confidence, source_list, ticket_counter_info, operating_hours.
5. If ticket_counter_info or operating_hours are not available in the current schema, return "Not yet verified".
6. If no search result, return an empty result with a friendly message.

Frontend:
1. Replace hardcoded popular stations with /locations/popular.
2. Search box calls /locations/search.
3. Clicking a result opens StationDetailPage.
4. Display missing data as "Not yet verified".
5. Add retry/back state for API failure.
```

---

## Phase 6 — 建立 Planning Input 和 Time Selection

### 目标

让 Planning 页面真正可以使用。

### 前端流程

```text
PlanningPage
    ↓ user types origin/destination
Google Places Autocomplete
    ↓ user selects valid places
Search button enabled
    ↓
PlanYourTimePage
    ↓ user selects Now / Morning / Afternoon / Evening
Confirm
    ↓
POST /routes/recommend
```

### 需要准备的 Request Body

```json
{
  "anonymous_user_id": "...",
  "origin_text": "Taman Bahagia",
  "destination_text": "KL Sentral",
  "origin_lat": 3.1100,
  "origin_lon": 101.6000,
  "destination_lat": 3.1340,
  "destination_lon": 101.6869,
  "travel_time": "2026-04-26T09:00:00"
}
```

### Cursor / Codex Prompt

```text
Implement the Planning input flow.

Requirements:
1. Keep the current Figma PlanningPage visual design.
2. Integrate Google Places Autocomplete for origin and destination.
3. Store selected place_id, display text, lat, and lon.
4. Search button must remain disabled until both places are valid.
5. If user clicks search with invalid input, show clear field-level guidance.
6. After valid search, navigate to PlanYourTimePage.
7. PlanYourTimePage must show four options: Now, Morning, Afternoon, Evening.
8. Confirm button should prepare the request body for POST /routes/recommend.
9. Preserve entered origin/destination if user changes language.
```

---

## Phase 7 — 建立 Route Recommendation Engine

### 目标

Google 返回多个 candidate routes，但 ElderGo KL 最终只选择一个推荐路线。

### 后端 Endpoint

```text
POST /routes/recommend
```

### 后端 Workflow

```text
1. Read user_travel_preferences.
2. Insert route_requests.
3. Call Google Maps API.
4. Receive candidate routes.
5. Score candidate routes.
6. Select one final recommended route.
7. Store selected route in recommended_routes.
8. Store selected route steps in route_steps.
9. Generate accessibility annotations.
10. Return route, steps, and annotations to frontend.
```

### 建议评分公式

```text
score =
    total_duration_min * 1.0
  + walking_distance_m * walking_weight
  + transfer_count * transfer_weight
  + accessibility_unknown_penalty
  + accessibility_problem_penalty
```

### 建议 preference weights

```text
Default:
walking_weight = 0.02
transfer_weight = 8

If less_walking = true:
walking_weight = 0.05

If fewer_transfers = true:
transfer_weight = 15

If accessibility_first = true:
unknown station accessibility = +20 penalty
supported station accessibility = -10 bonus
```

### 重要规则

- 不要显示多个 route cards。
- 不要让用户自己比较路线。
- 不要把所有 Google candidate routes 存进数据库。
- 如果没有路线可以完全满足偏好，就返回最接近用户需求的 alternative，并显示友好的说明。
- 如果 preference data invalid，就 fallback 到 default scoring。

### Cursor / Codex Prompt

```text
Implement POST /routes/recommend according to DATA_PLAN_EN.md.

Requirements:
1. Read anonymous_user_id and user_travel_preferences.
2. If preferences are missing, malformed, or unreadable, fall back to default mode.
3. Insert route_requests.
4. Call Google Maps Directions/Routes API with transit mode.
5. Keep Google candidate routes only in memory.
6. Score candidate routes using duration, walking distance, transfer count, and accessibility preference.
7. Return only one final recommended route.
8. Store only the final selected route in recommended_routes.
9. Parse and store step-by-step route data in route_steps.
10. Do not fabricate accessibility data.
11. If no route fully satisfies preferences, return the closest alternative with a friendly message.
```

---

## Phase 8 — 建立 Accessibility Annotation Service

### 目标

在 Route Result 页面显示真实、诚实的无障碍提示。

### 后端 Service

```text
accessibility_annotation_service.py
```

### Transit Step Logic

```text
Google transit step
        ↓
Check Google accessibility hint
        ↓
If available: supported, source = google_accessibility_hint
        ↓
If unavailable: match local station by name and coordinates
        ↓
Read station_accessibility_profiles
        ↓
If supported: show supported
        ↓
If missing: show unknown / limited information
```

### Walking Step Logic

```text
Google walking polyline
        ↓
Convert to PostGIS LineString
        ↓
Query accessibility_points within 30m/50m
        ↓
If shelter=yes or covered=yes: nearby_sheltered_point
        ↓
If wheelchair=yes / lift / accessible_entrance / kerb_ramp: nearby_accessibility_support
        ↓
If no match: unknown / no nearby static accessibility data
```

### Cursor / Codex Prompt

```text
Implement the route accessibility annotation service.

Requirements:
1. For each transit step:
   - First check Google accessibility hint if returned.
   - If present, create annotation with source google_accessibility_hint.
   - If not present, match Google station name/coordinate to rail_stations.
   - Read station_accessibility_profiles.
   - If supported, create supported annotation.
   - If missing, create unknown annotation with low confidence.
2. For each walking step:
   - Convert Google walking polyline to PostGIS LineString.
   - Query accessibility_points within 50m.
   - If shelter=yes or covered=yes, create nearby_sheltered_point annotation.
   - If wheelchair=yes or accessibility_type is lift, accessible_entrance, or kerb_ramp, create nearby_accessibility_support annotation.
   - If no data exists, return unknown or allow frontend to show "Limited information".
3. Store annotations in route_accessibility_annotations.
4. Never convert unknown into not_supported unless official data explicitly says unsupported.
```

---

## Phase 9 — 建立 Route Result Page

### 目标

用简单、适合长者阅读的方式显示最终路线。

### 需要的功能

- 默认显示 Text View
- 可切换 Map View
- Text View 和 Map View 使用同一份 route data
- 顶部显示 route summary
- 显示 step-by-step route cards
- 显示 accessibility labels
- 显示 weather 和 rush-hour reminder card
- 保存成图片
- 支持 WhatsApp 分享和 copy link
- 如果 map 加载失败，要有友好 fallback

### 关于 Weather 的重要规则

Weather 和 rush-hour reminders 只是提醒用户，不应该自动替换已经生成的路线，除非团队更新 acceptance criteria 和 DATA_PLAN。

### Cursor / Codex Prompt

```text
Build RouteResultPage.

Requirements:
1. Display Text View by default.
2. Add Map View toggle without full-page refresh.
3. Both views must use the same recommended route data.
4. Summary card must show origin, destination, total time, transfers, and walking distance.
5. Text View must show each step in order with mode, start/end, duration, and distance.
6. Display accessibility annotations using clear labels:
   - Supported
   - Limited information
   - Not yet verified
7. Show weather and rush-hour reminder cards, but do not auto-change the selected route.
8. If map fails, show friendly error and allow return to Text View.
9. Add Save button to export route result as PNG.
10. Add Share button with WhatsApp and copy-link.
11. Saving or sharing must not reset the route page state.
```

---

## Phase 10 — 建立 Help Module

### 目标

提供稳定、容易阅读的帮助内容。

### 需要的页面

- HelpPage
- UseElderGoPage
- TicketGuidePage
- ConcessionGuidePage
- PrivacyInfoPage

### 实现方式

MVP 阶段，help content 可以放在 frontend JSON 或 markdown：

```text
src/content/help.en.json
src/content/help.ms.json
```

除非团队想要 CMS 风格的可编辑内容，否则暂时不需要数据库。

### Cursor / Codex Prompt

```text
Build Help module based on ElderGo KL Analysis & Design.

Requirements:
1. Keep the Figma HelpPage card layout:
   - Use ElderGo
   - Buy a ticket
   - Apply for Concession
   - Privacy Info
2. Create TicketGuidePage, ConcessionGuidePage, PrivacyInfoPage, and UseElderGoPage.
3. Use simple vertical reading layout.
4. Keep text large and easy to read.
5. Add image enlarge modal for guide images.
6. Privacy content must change according to current language.
7. If content fails to load, show friendly retry message.
8. Do not use external links unless the team has approved them.
```

---

## Phase 11 — 建立 Controlled AI Assistant

### 目标

提供 chatbot 帮助，但不能变成不受控、会乱回答的通用 AI。

### 后端 Endpoints

```text
POST /ai/conversations
POST /ai/conversations/{conversation_id}/messages
```

### 支持的问题范围

- route questions
- weather questions
- station accessibility questions
- ticket guide questions
- concession guide questions
- privacy questions
- app usage questions

### 不支持的问题

- 无关的 general knowledge
- medical advice
- financial advice
- 编造 station information
- 编造 fare information
- 编造 accessibility information

### AI 回答可使用的数据来源

```text
current route result
rail_stations
station_accessibility_profiles
searchable_locations
static help content
weather reminder service
fallback message
```

### Cursor / Codex Prompt

```text
Build the controlled AI assistant for ElderGo KL.

Requirements:
1. The centre Chatbot button opens AIChatbotSheet overlay.
2. Closing the sheet must preserve the current page state.
3. Backend:
   - POST /ai/conversations
   - POST /ai/conversations/{conversation_id}/messages
4. Store conversations and messages in ai_conversations and ai_messages.
5. Implement simple intent detection:
   - route_question
   - weather_question
   - station_accessibility_question
   - ticket_question
   - concession_question
   - privacy_question
   - unclear
   - out_of_scope
6. For supported questions, answer only using database, current route, or static help content.
7. For ambiguous station names, ask clarification or return candidate suggestions.
8. For missing data, clearly say the information is not yet available or not yet verified.
9. For out-of-scope questions, say the assistant only supports ElderGo KL travel-related help.
10. Do not fabricate station, fare, accessibility, or policy information.
```

---

## 8. Epic 对应建设模块

| Epic | 建设模块 | 需要 Backend 吗？ | DATA_PLAN 支持 |
|---|---|---:|---|
| Epic 1：全局长者友好导航 | TopBar, BottomNav, AppContext, i18n | Yes | `user_ui_settings` |
| Epic 2：偏好设置 | PreferencePage, first-time popup | Yes | `user_travel_preferences` |
| Epic 3：路线输入和时间选择 | PlanningPage, Google autocomplete, PlanYourTimePage | Partly | route request format |
| Epic 4：单一路线推荐 | Route scoring engine | Yes | `route_requests`, `recommended_routes` |
| Epic 5：结果、保存、分享 | RouteResultPage, annotations, image export, sharing | Yes | `route_steps`, `route_accessibility_annotations` |
| Epic 6：车站搜索 | StationsHomePage, StationDetailPage | Yes | `searchable_locations`, `rail_stations`, `station_accessibility_profiles` |
| Epic 7：帮助、票务、隐私 | Static help pages | MVP 不一定需要 | static JSON/content files |
| Epic 8：AI 助手 | AIChatbotSheet, controlled backend | Yes | `ai_conversations`, `ai_messages` |
| Epic 9：Onboarding | Onboarding overlay / UseElderGo guide | Yes | `user_ui_settings.onboarding_completed` |

---

## 9. Gap and Decision List

## Gap 1 — Station Ticket Counter 和 Operating Hours

Analysis and Design 文件希望 Station Detail 页面显示 ticket counter information 和 operating hours，但 DATA_PLAN_EN.md 目前没有这些字段。

### MVP 决定

显示：

```text
Ticket counter: Not yet verified
Operating hours: Not yet verified
```

### 未来增强

可以增加新表：

```text
station_service_profiles
- station_id
- ticket_counter_info
- operating_hours
- toilet_info
- service_counter_info
- source_list
- updated_at
```

---

## Gap 2 — Weather Data

设计中提到 weather 和 rush-hour reminders，但 DATA_PLAN_EN.md 没有定义 weather tables。

### MVP 决定

Weather 只作为 runtime reminder 使用。除非团队更新 DATA_PLAN，否则不要把 weather 存到 route result tables。

### 重要规则

不要因为天气自动替换已经选好的路线。只显示 warning 或 reminder card。

---

## Gap 3 — Chatbot Scope

Chatbot 不能变成 general-purpose AI。

### MVP 决定

使用 controlled intent detection，并且只从 approved sources 回答。

Approved sources：

```text
current route result
station database
accessibility profiles
static help content
weather reminder
fallback messages
```

---

## Gap 4 — Figma 底部导航 Chatbot Button

Figma design 把 Chatbot 设计成底部中间导航项。

### 技术决定

保留视觉设计，但技术上实现成 overlay trigger，不是完整页面跳转。

这样更好，因为 AI assistant 关闭后应该保留当前页面状态。

---

## Gap 5 — 不使用 Supabase

当前 DATA_PLAN 是 PostgreSQL/PostGIS + FastAPI。如果团队不允许使用 Supabase，这个架构是可以的。

### MVP 决定

使用本地或云端 PostgreSQL + PostGIS。所有访问都通过 FastAPI。

---

## 10. 最终推荐建设顺序

```text
1. Frontend shell from Figma
2. AppContext: language, font size, page state, preferences
3. Backend schema from DATA_PLAN
4. ETL: GTFS + accessibility data
5. User resolve/settings/preference APIs
6. Station search/detail module
7. Planning input + Google autocomplete
8. Plan Your Time page
9. Route recommendation API
10. Accessibility annotation service
11. Route Result page
12. Save route as image
13. WhatsApp/copy-link sharing
14. Help/static guide pages
15. Controlled AI chatbot
16. Full acceptance criteria testing
```

---

## 11. Acceptance Criteria Testing Checklist

### Epic 1 Checklist

- Font size 可以 standard → large → extra_large → standard 循环。
- Refresh 后可以恢复之前的 font size。
- 大字体模式下不能出现 horizontal scrolling。
- Language switch 不能清空用户已经输入的内容。
- 所有主要页面都可以看到 bottom navigation。

### Epic 2 Checklist

- 第一次需要时显示 preference popup。
- Popup 显示 Accessibility First、Least Walking、Fewest Transfers。
- Save 会保存 preferences。
- Cancel 允许用户继续使用 default mode。
- Preference 页面允许之后修改。
- Route scoring 会使用更新后的 preferences。

### Epic 3 Checklist

- Origin 和 destination 支持 autocomplete。
- 输入不完整时不能继续 search。
- 有效输入会打开 Plan Your Time 页面。
- Time options 包括 Now、Morning、Afternoon、Evening。
- Confirm 会开始 route recommendation。

### Epic 4 Checklist

- 只显示一个 recommended route。
- 用户看不到内部 Google candidate routes。
- Preferences 会影响 scoring。
- 冲突 preferences 由系统内部处理。
- Invalid preference data 会 fallback 到 default mode。

### Epic 5 Checklist

- Route result 默认打开 Text View。
- Map View switch 不会 reload 整页。
- Summary 显示 total time、transfers、walking distance。
- Route steps 按顺序显示。
- Accessibility information 必须真实显示。
- Weather/rush-hour reminders 不会自动替换路线。
- Save 可以 export route image。
- Share 支持 WhatsApp 和 copy link。

### Epic 6 Checklist

- Stations 页面显示 Top 4 popular stations。
- Search 会返回匹配的 station results。
- 没有 exact match 时显示 friendly prompt。
- Station detail 显示 accessibility status。
- 缺失字段显示 “Not yet verified”。
- API failure 显示 retry/back option。

### Epic 7 Checklist

- Help 页面连接到 Use ElderGo、Ticket Guide、Concession Guide、Privacy Info。
- 长内容以 vertical readable format 显示。
- 如果有图片，图片可以 enlarge。
- Privacy content 跟随当前语言。
- Content loading 失败时不能出现 blank page。

### Epic 8 Checklist

- Chatbot 必须手动打开。
- 关闭 chatbot 后保留当前页面状态。
- 支持范围内的问题会返回结构化答案。
- Ambiguous station name 会要求用户确认。
- Missing data 会明确说明。
- Out-of-scope questions 会礼貌拒绝，并引导回交通相关功能。
- 多次失败后切换到 button guidance。

### Epic 9 Checklist

- Onboarding 只在第一次进入时显示。
- 用户可以 skip onboarding。
- Skip 后不影响 app 使用。
- Onboarding 结束后，主要入口仍然清楚可见。
- 如果需要，第一次进入 Planning 时仍然可以显示 preference onboarding。

---

## 12. 给团队的简单解释

目前的 Figma UI 是有用的，不应该丢掉。它已经给了我们适合长者用户的视觉方向。但是 Figma 只是产品的“外表”，DATA_PLAN 才是技术上的“骨架”。我们需要把 Figma 页面转换成可重复使用的 React components，然后连接到 FastAPI 和 PostgreSQL/PostGIS。

Google Maps 负责生成可能的路线，但 ElderGo KL 不应该把所有路线都丢给长者用户选择。我们的 backend 应该根据用户偏好，例如 accessibility first、least walking、fewest transfers，从 Google candidate routes 里面选出一个最适合的路线。

数据库应该储存 rail stations、accessibility points、route requests、最终 recommended routes、route steps 和 accessibility annotations。数据库不应该储存所有 Google candidate routes。

最安全的开发方式是分层建设：先做 frontend shell，再做 database schema，然后做 ETL data、user settings、station search、route planning、route result、help pages，最后才做 controlled AI assistant。

任何缺失或没有验证的信息，都应该诚实显示为：

```text
unknown
limited information
not yet verified
```

系统不应该猜测或编造 accessibility、fare、station 或 route information。

