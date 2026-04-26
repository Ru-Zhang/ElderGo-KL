# ElderGo KL Revised Build Plan

## 1. Purpose of This Revised Build Plan

This revised build plan turns the ElderGo KL Analysis and Design document, the existing `ElderGo_KL_BUILD_PLAN_EN.md`, the `DATA_PLAN_EN.md`, and the current `ElderGo-KL` repository into one practical implementation roadmap.

The main goal is to make the build workflow detailed enough for Cursor, Codex, or another developer to follow phase by phase without guessing how the frontend, backend, database, ETL workflow, route recommendation, accessibility annotation, and AI assistant should connect.

The key project decision is:

```text
The current Figma-based React frontend defines the product UI direction.
DATA_PLAN_EN.md defines the backend, database, and data workflow behavior.
FastAPI connects the React frontend, Google Maps API, PostgreSQL/PostGIS, and AI assistant.
```

This means the current UI should not be discarded. The existing React pages should be preserved, cleaned up, typed, and connected to real APIs over time.

At the same time, the current hardcoded demo data must not be treated as real transport or accessibility truth. Real route generation depends on Google Maps API. Local data supports rail station search, static accessibility facts, station accessibility profiles, route history, route step annotation, and anonymous user settings.

The most important product rule is:

```text
Never fabricate accessibility, ticket, station, weather, or route information.
If data is missing, show it as unknown, limited information, or not yet verified.
```

---

## 2. Source Documents and Repo Alignment

This revised plan is based on four sources.

| Source | Role in this build plan |
|---|---|
| `ElderGo KL-Analysis and Design.pdf` | Defines the problem statement, personas, epics, user stories, and acceptance criteria. |
| `DATA_PLAN_EN.md` | Defines business workflows, database tables, ETL rules, route storage rules, and backend/frontend/database interactions. |
| `ElderGo_KL_BUILD_PLAN_EN.md` | Defines the earlier implementation direction and phase structure. |
| Current `ElderGo-KL` repo | Defines the real starting point for implementation. |

The current repo is not a finished full-stack application yet. It is closer to a frontend prototype plus empty backend/database scaffolding. Therefore, this plan describes how to move from the current repo state to the target DATA_PLAN architecture.

Important alignment decisions:

- The frontend already contains many A&D screens and should be reused.
- The backend folder structure exists but most backend files are empty and must be implemented.
- The database schema file exists but is empty and must be filled from DATA_PLAN.
- The existing `doc/` folder already contains build and data plans, so this revised plan should live there too.
- The current frontend static station data is useful only for fallback/demo mode.
- Google Maps provides runtime routes and bus route information.
- Static GTFS is used for rail data only.
- Accessibility data is static and Point-based at this stage.
- Missing accessibility data must be displayed as unknown, not unsupported.

---

## 3. Current ElderGo-KL Repo Assessment

### 3.1 Current Root Structure

```text
ElderGo-KL/
|
|-- backend/
|-- database/
|-- doc/
|-- frontend/
|-- img/
|-- README.md
|-- .gitignore
```

### 3.2 Current Frontend State

The frontend is a React/Vite application generated or adapted from Figma. It already includes:

- `frontend/src/app/App.tsx`
- `frontend/src/app/AppProvider.tsx`
- `frontend/src/components/layout/TopBar.tsx`
- `frontend/src/components/layout/BottomNav.tsx`
- `frontend/src/components/chatbot/AIChatbotSheet.tsx`
- route planning page
- time selection page
- route result page
- station search and station detail pages
- preference page
- help pages
- EN/BM translation helper
- shadcn/Radix style UI component folder
- image assets and brand assets

The current frontend already matches many A&D epics visually:

| Existing frontend area | Related epic |
|---|---|
| Top language and font controls | Epic 1 |
| Persistent bottom navigation | Epic 1 |
| Preference page and modal | Epic 2 |
| Planning page origin/destination inputs | Epic 3 |
| Time selection page | Epic 3 |
| Route result page | Epic 5 |
| Station search/detail pages | Epic 6 |
| Help/ticket/concession/privacy pages | Epic 7 |
| Chatbot bottom sheet | Epic 8 |

However, the frontend is still mostly static:

- page routing is controlled by local React state, not a router.
- `AppProvider` stores only basic language, font, preferences, and selected station state.
- font size currently has only `normal` and `large`, while the A&D expects standard, large, and extra-large.
- station data comes from `frontend/src/data/stationsData.ts`.
- route result data is hardcoded.
- route planning inputs use static suggestions.
- no real API service layer exists yet.
- no route request/result contract exists yet.
- chatbot UI is local and not connected to a controlled backend service.

### 3.3 Current Backend State

The backend folder exists with a FastAPI-like structure:

```text
backend/
|-- app/
|   |-- main.py
|   |-- api/
|   |   |-- router.py
|   |-- core/
|   |   |-- config.py
|   |-- db/
|   |   |-- base.py
|   |   |-- session.py
|   |-- models/
|   |   |-- orm.py
|   |-- services/
|   |   |-- route_service.py
|   |-- utils/
|       |-- helpers.py
|-- tests/
|   |-- test_route_planning.py
|-- requirements.py
```

Most backend files are currently empty. The backend must be implemented from the ground up.

Important correction:

```text
backend/requirements.py should be replaced by or supplemented with backend/requirements.txt.
```

### 3.4 Current Database State

The database folder contains:

```text
database/schema.sql
```

The schema file is currently empty. It must be filled with PostgreSQL/PostGIS schema definitions based on `DATA_PLAN_EN.md`.

### 3.5 Current Documentation State

The repo already contains:

```text
doc/DATA_PLAN_EN.md
doc/DATA_PLAN_CN.md
doc/ElderGo_KL_BUILD_PLAN_EN.md
doc/ElderGo_KL_BUILD_PLAN_CN.md
doc/Pair Programming.md
```

This revised plan should be treated as the implementation master plan, while the original files remain useful references.

---

## 4. Target Architecture

The target technical architecture is:

```text
React / TypeScript Frontend
        |
        | REST API
        v
FastAPI Backend
        |
        | SQLAlchemy / SQL
        v
PostgreSQL + PostGIS
        |
        | Static data
        v
GTFS rail data + accessibility Point data + user cache + final route records

Google Maps API is called by the backend for:
- autocomplete or place lookup support
- geocoding
- route candidates
- transit steps
- walking steps
- route duration
- route polyline
```

The frontend must not connect directly to PostgreSQL.

The frontend should call the FastAPI backend for:

- anonymous user setup
- UI settings
- travel preferences
- station search
- station detail
- route recommendation
- route result retrieval
- AI assistant messages

The backend should call Google Maps for:

- route candidates
- runtime transit routing
- bus information
- walking segments
- map polylines

The database should store:

- static rail business data
- static accessibility Point data
- station accessibility summaries
- search index rows
- route request records
- final recommended route only
- final route steps
- route step annotations
- anonymous user settings and preferences
- recent place cache
- AI conversation/message records

The database should not store all Google candidate routes.

---

## 5. DATA_PLAN Compatibility Rules

These rules must be followed throughout implementation.

### 5.1 Route Generation Rules

- Google Maps API generates route candidates at runtime.
- The local database does not generate full public transport routes by itself.
- The backend scores Google route candidates and returns one final recommended route.
- The database stores the user request, the final selected route, the final route steps, and annotations.
- The database does not permanently store every rejected Google candidate route.

### 5.2 Rail and Bus Data Rules

- Rail station and route data can be imported from KTMB and Rapid Rail GTFS CSV files.
- Bus routes are not imported from static GTFS in this stage.
- Bus route information comes from Google Maps route results.
- Local rail data is used for station search and station accessibility matching.

### 5.3 Accessibility Data Rules

- Accessibility source data is static and not real-time.
- Accessibility geometry is Point geometry only.
- LineString accessibility features are not used in the current stage.
- Missing data means unknown, not unsupported.
- Unknown status must be visible to users in a calm and clear way.
- AI answers must not invent accessibility facts.

### 5.4 User Cache Rules

- Users do not need login for the current stage.
- The frontend generates a device ID.
- The backend stores only a hashed device ID.
- UI settings and preferences are linked to anonymous users.
- Settings should be restored when the same device/browser returns.

### 5.5 AI Assistant Rules

- AI assistant is controlled and travel-related only.
- It should answer from approved sources:
  - app help content
  - known route result
  - known station records
  - known ticket/concession guidance
  - known accessibility annotations
- It must refuse unrelated medical, financial, legal, unsafe, or non-travel requests.
- It must say when information is unknown.

---

## 6. Detailed Project Structure

The current repo should evolve toward this structure.

```text
ElderGo-KL/
|
|-- frontend/
|   |-- src/
|   |   |-- app/
|   |   |   |-- App.tsx
|   |   |   |-- AppProvider.tsx
|   |   |   |-- types.ts
|   |   |
|   |   |-- components/
|   |   |   |-- layout/
|   |   |   |   |-- TopBar.tsx
|   |   |   |   |-- BottomNav.tsx
|   |   |   |
|   |   |   |-- common/
|   |   |   |-- chatbot/
|   |   |       |-- AIChatbotSheet.tsx
|   |   |
|   |   |-- pages/
|   |   |   |-- PlanningPage.tsx
|   |   |   |-- PlanYourTimePage.tsx
|   |   |   |-- RouteResultPage.tsx
|   |   |   |-- PreferencePage.tsx
|   |   |   |-- StationsHomePage.tsx
|   |   |   |-- StationDetailPage.tsx
|   |   |   |-- HelpPage.tsx
|   |   |   |-- UseElderGoPage.tsx
|   |   |   |-- TicketGuidePage.tsx
|   |   |   |-- ConcessionGuidePage.tsx
|   |   |   |-- PrivacyInfoPage.tsx
|   |   |
|   |   |-- services/
|   |   |   |-- api.ts
|   |   |   |-- usersApi.ts
|   |   |   |-- locationsApi.ts
|   |   |   |-- routesApi.ts
|   |   |   |-- aiApi.ts
|   |   |   |-- googlePlaces.ts
|   |   |
|   |   |-- types/
|   |   |   |-- users.ts
|   |   |   |-- settings.ts
|   |   |   |-- preferences.ts
|   |   |   |-- locations.ts
|   |   |   |-- routes.ts
|   |   |   |-- ai.ts
|   |   |
|   |   |-- utils/
|   |       |-- deviceId.ts
|   |       |-- routeImageExport.ts
|   |       |-- shareRoute.ts
|   |
|   |-- package.json
|
|-- backend/
|   |-- app/
|   |   |-- main.py
|   |   |-- api/
|   |   |   |-- router.py
|   |   |   |-- v1/
|   |   |       |-- endpoints/
|   |   |           |-- health.py
|   |   |           |-- users.py
|   |   |           |-- locations.py
|   |   |           |-- routes.py
|   |   |           |-- ai.py
|   |   |           |-- content.py
|   |   |
|   |   |-- core/
|   |   |   |-- config.py
|   |   |
|   |   |-- db/
|   |   |   |-- base.py
|   |   |   |-- session.py
|   |   |
|   |   |-- models/
|   |   |   |-- orm.py
|   |   |
|   |   |-- schemas/
|   |   |   |-- users.py
|   |   |   |-- locations.py
|   |   |   |-- routes.py
|   |   |   |-- ai.py
|   |   |
|   |   |-- services/
|   |       |-- google_maps_service.py
|   |       |-- route_scoring_service.py
|   |       |-- accessibility_annotation_service.py
|   |       |-- station_matching_service.py
|   |       |-- ai_guardrail_service.py
|   |
|   |-- etl/
|   |   |-- import_gtfs.py
|   |   |-- import_accessibility_points.py
|   |   |-- build_station_accessibility_profiles.py
|   |   |-- sync_searchable_locations.py
|   |
|   |-- sql/
|   |   |-- 001_init_schema.sql
|   |
|   |-- tests/
|   |-- requirements.txt
|
|-- database/
|   |-- schema.sql
|
|-- doc/
|   |-- DATA_PLAN_EN.md
|   |-- ElderGo_KL_BUILD_PLAN_EN.md
|   |-- ElderGo_KL_BUILD_PLAN_REVISED_EN.md
|
|-- docker-compose.yml
|-- .env.example
```

---

## 7. Backend Data Tables Required

The backend database should follow `DATA_PLAN_EN.md`.

### 7.1 Business Tables

| Table | Purpose |
|---|---|
| `rail_agencies` | Stores KTMB, Rapid Rail, and related agency records. |
| `rail_routes` | Stores KTM, LRT, MRT, Monorail, and related rail line records. |
| `rail_stations` | Stores rail station names, source IDs, coordinates, and Point geometry. |
| `rail_station_routes` | Stores many-to-many station-route relationships and stop order. |
| `accessibility_points` | Stores static Point accessibility features such as lifts, ramps, covered areas, and entrances. |
| `station_accessibility_profiles` | Stores station-level accessibility summary, confidence, sources, and notes. |
| `route_requests` | Stores one user route planning request. |
| `recommended_routes` | Stores only the final selected route for a request. |
| `route_steps` | Stores step-by-step details for the final route. |
| `route_accessibility_annotations` | Stores accessibility hints for each final route step. |
| `searchable_locations` | Search index for stations and accessibility points. |

### 7.2 User Cache Tables

| Table | Purpose |
|---|---|
| `anonymous_users` | Stores hashed device identity without requiring login. |
| `user_ui_settings` | Stores language, font size, and onboarding status. |
| `user_travel_preferences` | Stores accessibility-first, least-walking, and fewest-transfer preferences. |
| `recent_place_cache` | Stores recent origins and destinations for easier reuse. |
| `ai_conversations` | Stores AI assistant conversation sessions. |
| `ai_messages` | Stores bounded AI assistant messages. |

### 7.3 Required PostgreSQL Extensions and Indexes

Required extensions:

```sql
CREATE EXTENSION IF NOT EXISTS postgis;
CREATE EXTENSION IF NOT EXISTS pg_trgm;
```

Recommended indexes:

- GIST index on `rail_stations.geom`.
- GIST index on `accessibility_points.geom`.
- trigram or lower-name index for station/searchable location search.
- index on `anonymous_users.hashed_device_id`.
- index on `route_requests.anonymous_user_id`.
- index on `recommended_routes.route_request_id`.
- index on `route_steps.recommended_route_id`.
- index on `route_accessibility_annotations.route_step_id`.

---

## 8. Full Detailed Build Workflow

## Phase 0: Confirm Current Project Baseline

### Goal

Verify the current project state before implementation starts. This phase prevents the team from building against assumptions that do not match the actual repo.

### Current Repo Starting Point

The current repo contains a mostly complete React visual prototype, empty backend files, an empty database schema file, and existing documentation.

### Data Plan Alignment

DATA_PLAN assumes a full stack application with frontend, FastAPI backend, PostgreSQL/PostGIS database, ETL workflow, route recommendation records, and user cache records. This phase confirms which parts already exist and which parts must be built.

### Detailed Workflow

1. Inspect the frontend structure.
2. Confirm `frontend/package.json` uses Vite and React.
3. Confirm existing pages under `frontend/src/pages`.
4. Confirm existing layout components under `frontend/src/components/layout`.
5. Confirm current static station data in `frontend/src/data/stationsData.ts`.
6. Inspect backend files and confirm which files are empty.
7. Inspect `database/schema.sql` and confirm whether it has schema content.
8. Inspect `doc/` and confirm DATA_PLAN and original build plan exist.
9. Inspect `img/` and frontend public assets for logo/background usage.
10. Record all baseline gaps before coding starts.

### Build Items

- Baseline checklist.
- Current repo map.
- Known static/demo data list.
- Known empty backend/database file list.

### Files to Create or Update

No code files should be changed in this phase unless the team creates a short internal checklist.

Optional:

```text
doc/BASELINE_CHECKLIST.md
```

### Acceptance Criteria

- Team can clearly explain what is already implemented.
- Team can clearly explain what is static/demo-only.
- Team can clearly explain which backend/database modules must be created.
- Original documents remain unchanged.

### Cursor / Codex Prompt

```text
Inspect the ElderGo-KL repository without modifying files. Summarise the current frontend, backend, database, docs, and assets. Identify which parts are implemented, which parts are static/demo-only, and which files are empty scaffolds. Use this as the implementation baseline.
```

---

## Phase 1: Stabilise the Current Figma Frontend Shell

### Goal

Preserve the current Figma-derived UI while making it stable enough for real app state and backend data.

### Current Repo Starting Point

The frontend already has page components, `App.tsx`, `AppProvider.tsx`, `TopBar`, `BottomNav`, and chatbot overlay. Page navigation is currently local state in `App.tsx`.

### Data Plan Alignment

DATA_PLAN requires frontend state for:

- anonymous user identity
- UI settings
- travel preferences
- route request input
- selected departure time
- selected station
- route result
- onboarding state

### Detailed Workflow

1. Keep the current page components.
2. Keep the current bottom navigation and chatbot overlay behavior.
3. Extend `AppProvider` into the main client-side app state layer.
4. Add route planning state:
   - origin display name
   - origin coordinates
   - origin Google place ID if available
   - destination display name
   - destination coordinates
   - destination Google place ID if available
5. Add time planning state:
   - leave now
   - selected preset time
   - custom departure datetime for later enhancement
6. Add route result state:
   - loading
   - error
   - current recommended route
7. Add selected station state.
8. Add anonymous user state:
   - anonymous user ID
   - loading/restored status
9. Add UI settings state:
   - language
   - font size
   - onboarding completed
10. Change font size from two modes to three modes:
   - `standard`
   - `large`
   - `extra_large`
11. Persist language and font size in local storage as an immediate fallback.
12. Keep backend persistence for Phase 6.
13. Make sure changing language/font does not reset current route input.
14. Make sure opening chatbot does not replace the current page.

### Build Items

- Expanded app context.
- Three-mode font size state.
- Persistent language/font fallback.
- Route input state.
- Route result state.
- Onboarding state placeholder.

### Files to Create or Update

```text
frontend/src/app/App.tsx
frontend/src/app/AppProvider.tsx
frontend/src/components/layout/TopBar.tsx
frontend/src/components/layout/BottomNav.tsx
frontend/src/i18n/translations.ts
```

### Acceptance Criteria

- User can navigate between planning, time, route result, station, help, and preference pages without losing app state.
- Chatbot opens as a bottom sheet overlay.
- Language switch affects the whole app.
- Font switch cycles through standard, large, and extra-large.
- Large and extra-large modes do not cause horizontal scrolling or clipped key buttons.
- Current route input is not lost when language/font changes.

### Cursor / Codex Prompt

```text
Update the current ElderGo KL React frontend shell without redesigning it. Extend AppProvider to store route input, selected time, route result, selected station, anonymous user placeholder, UI settings, onboarding status, and travel preferences. Change font size from normal/large to standard/large/extra_large. Persist language and font size locally. Keep the chatbot as an overlay and preserve current page navigation.
```

---

## Phase 2: Create Frontend Type and API Service Layer

### Goal

Stop pages from directly depending on permanent hardcoded demo data. Create a typed API layer that can connect to FastAPI while still supporting fallback/demo mode during development.

### Current Repo Starting Point

The frontend currently uses local arrays and component state for station suggestions, station details, and route results.

### Data Plan Alignment

DATA_PLAN expects frontend/backend contracts for:

- anonymous users
- UI settings
- travel preferences
- locations/search
- route requests
- recommended route responses
- route step annotations
- AI conversations and messages

### Detailed Workflow

1. Create shared frontend type files.
2. Define `LanguageCode` as `EN | BM`.
3. Define `FontSizeMode` as `standard | large | extra_large`.
4. Define user settings types.
5. Define travel preference types:
   - accessibility first
   - least walking
   - fewest transfers
6. Define place/location types:
   - local location ID
   - source type
   - display name
   - lat/lon
   - accessibility status
   - confidence
   - notes
7. Define route request type.
8. Define route result type.
9. Define route step type.
10. Define accessibility annotation type.
11. Define AI conversation/message types.
12. Create base API client with:
   - base URL from Vite env
   - JSON headers
   - timeout/error handling
   - consistent error message conversion
13. Create service modules:
   - `usersApi.ts`
   - `locationsApi.ts`
   - `routesApi.ts`
   - `aiApi.ts`
   - `googlePlaces.ts`
14. Move demo station access behind a fallback service path.
15. Do not remove demo data until backend endpoints work.

### Build Items

- TypeScript API contracts.
- API client wrapper.
- User service functions.
- Location service functions.
- Route service functions.
- AI service functions.
- Demo fallback mode.

### Files to Create or Update

```text
frontend/src/types/users.ts
frontend/src/types/settings.ts
frontend/src/types/preferences.ts
frontend/src/types/locations.ts
frontend/src/types/routes.ts
frontend/src/types/ai.ts
frontend/src/services/api.ts
frontend/src/services/usersApi.ts
frontend/src/services/locationsApi.ts
frontend/src/services/routesApi.ts
frontend/src/services/aiApi.ts
frontend/src/services/googlePlaces.ts
frontend/src/data/stationsData.ts
```

### Acceptance Criteria

- Frontend pages can call typed service functions.
- Mock station data is clearly marked as fallback/demo data.
- Route request and route result types match the intended backend contract.
- Missing accessibility values can be represented as `unknown`.
- API errors can be shown to elderly users in simple text.

### Cursor / Codex Prompt

```text
Create a typed frontend service layer for ElderGo KL. Add TypeScript types for users, settings, preferences, locations, route requests, route results, route steps, annotations, and AI messages. Add a base API client and service modules for users, locations, routes, AI, and Google Places. Keep current station data as fallback/demo data only.
```

---

## Phase 3: Build PostgreSQL/PostGIS Database Schema

### Goal

Implement the database schema required by DATA_PLAN.

### Current Repo Starting Point

`database/schema.sql` exists but is empty.

### Data Plan Alignment

This phase directly implements the tables and relationships in DATA_PLAN sections for business objects and user cache objects.

### Detailed Workflow

1. Enable PostGIS.
2. Enable trigram search support.
3. Create `rail_agencies`.
4. Create `rail_routes`.
5. Create `rail_stations` with Point geometry.
6. Create `rail_station_routes`.
7. Create `accessibility_points` with Point geometry only.
8. Create `station_accessibility_profiles`.
9. Create `anonymous_users`.
10. Create `user_ui_settings`.
11. Create `user_travel_preferences`.
12. Create `recent_place_cache`.
13. Create `route_requests`.
14. Create `recommended_routes`.
15. Create `route_steps`.
16. Create `route_accessibility_annotations`.
17. Create `searchable_locations`.
18. Create `ai_conversations`.
19. Create `ai_messages`.
20. Add foreign keys.
21. Add created/updated timestamps where useful.
22. Add geometry indexes.
23. Add search indexes.
24. Add user and route lookup indexes.
25. Add check constraints for important enum-like values where practical.

### Build Items

- Complete database schema.
- PostGIS setup.
- Search indexes.
- Foreign keys and route relationships.
- User cache tables.

### Files to Create or Update

```text
database/schema.sql
backend/sql/001_init_schema.sql
```

The same schema can be duplicated in both places if the team wants `database/` for documentation and `backend/sql/` for backend migrations.

### Acceptance Criteria

- Schema loads into PostgreSQL.
- All DATA_PLAN business tables exist.
- All DATA_PLAN user cache tables exist.
- Geometry columns are Point-based.
- Accessibility data can represent unknown values.
- Final route storage is separated from route requests.
- No table is designed to store every rejected Google route candidate permanently.

### Cursor / Codex Prompt

```text
Implement the ElderGo KL PostgreSQL/PostGIS schema based on DATA_PLAN_EN.md. Fill database/schema.sql and backend/sql/001_init_schema.sql with tables for rail agencies, routes, stations, station-route relationships, accessibility points, station accessibility profiles, route requests, recommended routes, route steps, route annotations, searchable locations, anonymous users, UI settings, travel preferences, recent places, AI conversations, and AI messages. Add PostGIS, indexes, foreign keys, and support for unknown accessibility data.
```

---

## Phase 4: Build FastAPI Backend Foundation

### Goal

Create a working FastAPI backend foundation that can later host all ElderGo APIs.

### Current Repo Starting Point

The backend folder exists but most files are empty.

### Data Plan Alignment

DATA_PLAN requires the backend to sit between frontend, Google Maps, PostgreSQL/PostGIS, and AI.

### Detailed Workflow

1. Replace or supplement `requirements.py` with `requirements.txt`.
2. Add backend dependencies:
   - FastAPI
   - Uvicorn
   - SQLAlchemy
   - psycopg
   - pydantic-settings
   - python-dotenv
   - httpx
   - pytest
3. Implement `app/core/config.py`.
4. Load:
   - app name
   - environment
   - database URL
   - CORS origins
   - Google Maps API key
   - AI provider settings if used later
5. Implement database session in `app/db/session.py`.
6. Implement ORM base in `app/db/base.py`.
7. Implement FastAPI app in `app/main.py`.
8. Add CORS middleware.
9. Add root endpoint or health endpoint.
10. Implement API router in `app/api/router.py`.
11. Create endpoint modules for:
   - health
   - users
   - locations
   - routes
   - AI
   - content
12. Include routers in the app.
13. Confirm OpenAPI docs render.

### Build Items

- Working FastAPI app.
- Settings loader.
- DB session setup.
- Router structure.
- Health endpoint.
- Requirements file.

### Files to Create or Update

```text
backend/requirements.txt
backend/app/main.py
backend/app/core/config.py
backend/app/db/session.py
backend/app/db/base.py
backend/app/api/router.py
backend/app/api/v1/endpoints/health.py
backend/app/api/v1/endpoints/users.py
backend/app/api/v1/endpoints/locations.py
backend/app/api/v1/endpoints/routes.py
backend/app/api/v1/endpoints/ai.py
backend/app/api/v1/endpoints/content.py
.env.example
```

### Acceptance Criteria

- Backend starts with Uvicorn.
- `GET /health` returns OK.
- OpenAPI docs show the endpoint groups.
- CORS allows local frontend development.
- Config values are loaded from environment variables.

### Cursor / Codex Prompt

```text
Build the FastAPI backend foundation for ElderGo KL. Add requirements.txt, settings, DB session, ORM base, main app, CORS, API router, and endpoint files for health, users, locations, routes, AI, and content. Make sure GET /health works and OpenAPI docs show all endpoint groups.
```

---

## Phase 5: Build ORM Models and Pydantic Schemas

### Goal

Make backend data contracts match DATA_PLAN and provide stable API response shapes for the frontend.

### Current Repo Starting Point

`backend/app/models/orm.py` exists but is empty. There is no schema folder yet.

### Data Plan Alignment

DATA_PLAN defines the business objects, user cache objects, and route annotation objects that backend models must represent.

### Detailed Workflow

1. Define SQLAlchemy ORM models for all database tables.
2. Keep ORM model names close to table names.
3. Add relationships for:
   - agency to routes
   - routes to station route links
   - station to station route links
   - station to accessibility profile
   - route request to recommended route
   - recommended route to route steps
   - route step to annotations
   - anonymous user to settings/preferences/recent places/routes
4. Create `schemas/` folder.
5. Add Pydantic schemas for users.
6. Add Pydantic schemas for settings.
7. Add Pydantic schemas for preferences.
8. Add Pydantic schemas for locations.
9. Add Pydantic schemas for route request.
10. Add Pydantic schemas for route result.
11. Add Pydantic schemas for route steps.
12. Add Pydantic schemas for route annotations.
13. Add Pydantic schemas for AI conversations/messages.
14. Use `unknown` as a valid accessibility status.
15. Avoid boolean-only accessibility fields when unknown is possible.

### Build Items

- ORM model layer.
- Pydantic API contracts.
- Shared enums or literal values for statuses.
- Route result response contract.

### Files to Create or Update

```text
backend/app/models/orm.py
backend/app/schemas/users.py
backend/app/schemas/settings.py
backend/app/schemas/preferences.py
backend/app/schemas/locations.py
backend/app/schemas/routes.py
backend/app/schemas/ai.py
```

### Acceptance Criteria

- Backend schemas support every frontend service contract.
- Unknown accessibility can be represented without converting it to false.
- Route recommendation response includes:
  - route ID
  - summary
  - duration
  - walking distance
  - transfers
  - steps
  - annotations
  - map polyline if available
- Location response includes accessibility status, confidence, and note.

### Cursor / Codex Prompt

```text
Create SQLAlchemy ORM models and Pydantic schemas for the ElderGo KL DATA_PLAN. Include all rail, accessibility, route, user cache, search, and AI tables. Make unknown accessibility a first-class value and avoid schemas that force missing support into false.
```

---

## Phase 6: Anonymous User, UI Settings, Preferences, and Onboarding

### Goal

Implement the DATA_PLAN user cache workflow so elderly users can return to the app and keep their language, font size, onboarding status, and route preferences.

### Current Repo Starting Point

The frontend stores language, font size, and preferences in React state only.

### Data Plan Alignment

DATA_PLAN section 2.4 and 8.2 describe the user cache workflow:

```text
User opens app
    -> frontend generates device_id
    -> backend hashes device_id
    -> backend creates or reads anonymous_users
    -> backend reads settings and preferences
    -> frontend restores language, font size, preferences, onboarding status
```

### Detailed Workflow

1. Add frontend `deviceId.ts`.
2. Generate a stable browser/device ID.
3. Store raw device ID only in frontend local storage.
4. Send raw device ID to backend only for hashing.
5. Backend hashes device ID.
6. Backend creates or finds `anonymous_users`.
7. Backend creates default `user_ui_settings` if missing.
8. Backend creates default `user_travel_preferences` if missing.
9. Frontend loads settings after anonymous user creation.
10. Frontend applies language and font size.
11. Frontend loads preferences.
12. Frontend connects `PreferencePage` and `PreferencesModal` to backend save.
13. Frontend stores onboarding completed state.
14. If backend is unavailable, frontend uses local fallback and retries later.

### Build Items

- Anonymous user endpoint.
- UI settings endpoints.
- Travel preferences endpoints.
- Frontend device ID utility.
- App startup restore flow.
- Preference save flow.

### Endpoints

```text
POST  /users/anonymous
GET   /users/{anonymous_user_id}/ui-settings
PATCH /users/{anonymous_user_id}/ui-settings
GET   /users/{anonymous_user_id}/travel-preferences
PATCH /users/{anonymous_user_id}/travel-preferences
```

### Files to Create or Update

```text
frontend/src/utils/deviceId.ts
frontend/src/services/usersApi.ts
frontend/src/app/AppProvider.tsx
frontend/src/pages/PreferencePage.tsx
frontend/src/components/common/PreferencesModal.tsx
backend/app/api/v1/endpoints/users.py
backend/app/schemas/users.py
backend/app/schemas/settings.py
backend/app/schemas/preferences.py
```

### Acceptance Criteria

- First-time user receives an anonymous user ID.
- Returning user restores language, font size, onboarding status, and preferences.
- Preferences are saved after user changes them.
- Raw device ID is not stored in the database.
- UI still works in local fallback mode if backend is temporarily unavailable.

### Cursor / Codex Prompt

```text
Implement the anonymous user cache workflow for ElderGo KL. Add frontend device ID generation and backend hashing. Add endpoints for anonymous user creation, UI settings, and travel preferences. Connect AppProvider, TopBar, PreferencePage, and PreferencesModal so language, font size, onboarding status, and travel preferences are restored and saved.
```

---

## Phase 7: Static Rail and Accessibility ETL Pipeline

### Goal

Populate PostgreSQL/PostGIS with rail stations, rail routes, accessibility Points, station accessibility profiles, and searchable locations.

### Current Repo Starting Point

No ETL scripts exist yet.

### Data Plan Alignment

DATA_PLAN defines this static data preparation workflow:

```text
KTMB GTFS CSV
+ Rapid Rail GTFS CSV
+ cleaned accessibility Point CSV
        -> Python ETL cleaning and standardisation
        -> PostgreSQL/PostGIS
        -> rail stations, rail routes, accessibility points,
           station accessibility profiles, and search index
```

### Detailed Workflow

1. Create `backend/etl/`.
2. Create shared ETL database connection helper if needed.
3. Define expected input folders:
   - `data/raw/gtfs/ktmb/`
   - `data/raw/gtfs/rapid_rail/`
   - `data/raw/accessibility/`
   - `data/processed/`
4. Import GTFS agencies into `rail_agencies`.
5. Import GTFS routes into `rail_routes`.
6. Import GTFS stops/stations into `rail_stations`.
7. Import station-route relationships into `rail_station_routes`.
8. Normalize station names.
9. Deduplicate stations where source files overlap.
10. Import cleaned accessibility CSV as Point geometries.
11. Store feature type, source, source confidence, and tags where available.
12. Build station accessibility profiles by matching nearby accessibility Points.
13. Assign profile status:
   - supported
   - limited
   - unknown
   - not_verified
14. Record confidence and source list.
15. Sync stations and accessibility points into `searchable_locations`.
16. Add dry-run and row count output to ETL scripts.
17. Add sample-data mode for development if real datasets are not available.

### Build Items

- GTFS import script.
- Accessibility Point import script.
- Station profile builder.
- Search index sync script.
- ETL documentation comments.

### Files to Create or Update

```text
backend/etl/import_gtfs.py
backend/etl/import_accessibility_points.py
backend/etl/build_station_accessibility_profiles.py
backend/etl/sync_searchable_locations.py
backend/etl/README.md
```

### Acceptance Criteria

- Rail agencies are imported.
- Rail routes are imported.
- Rail stations are imported with coordinates and Point geometry.
- Station-route relationships are imported.
- Accessibility points use Point geometry only.
- Station accessibility profiles are generated.
- Searchable locations are synced.
- Missing accessibility data creates `unknown`, not `unsupported`.

### Cursor / Codex Prompt

```text
Create the ElderGo KL ETL pipeline for static rail and accessibility data. Add scripts to import KTMB and Rapid Rail GTFS CSVs, import cleaned accessibility Point CSVs, build station accessibility profiles, and sync searchable_locations. Follow DATA_PLAN rules: bus routes are not imported, accessibility geometry is Point only, and missing accessibility data is unknown.
```

---

## Phase 8: Station Search and Station Detail Module

### Goal

Replace permanent dependency on static station mock data with backend location search and station detail APIs.

### Current Repo Starting Point

`StationsHomePage` and `StationDetailPage` use local station data from `frontend/src/data/stationsData.ts`.

### Data Plan Alignment

DATA_PLAN defines this Epic 6 workflow:

```text
rail_stations
+ accessibility_points
        -> searchable_locations
        -> Frontend searches station / accessibility point
        -> FastAPI queries searchable_locations
        -> Return search results with basic accessibility status
```

### Detailed Workflow

1. Implement backend location endpoints.
2. `GET /locations/popular` returns popular stations or configured high-use locations.
3. `GET /locations/search?q=...` searches `searchable_locations`.
4. `GET /locations/{location_id}` returns detail for station or accessibility point.
5. Include accessibility status and confidence in responses.
6. Include `unknown` when station accessibility profile is missing.
7. Frontend `StationsHomePage` calls `locationsApi.getPopularLocations`.
8. Frontend search input calls `locationsApi.searchLocations`.
9. Frontend selected location state stores full location object.
10. Frontend `StationDetailPage` calls `locationsApi.getLocationDetail`.
11. Keep current `stationsData.ts` only as fallback/demo data.
12. Remove unverified operating hours and ticket counter claims from primary UI.
13. If those fields remain in UI, label them `not yet verified`.

### Build Items

- Location search endpoint.
- Popular locations endpoint.
- Location detail endpoint.
- Frontend location service integration.
- Station data fallback mode.
- Unknown accessibility display states.

### Endpoints

```text
GET /locations/popular
GET /locations/search?q=...
GET /locations/{location_id}
```

### Files to Create or Update

```text
backend/app/api/v1/endpoints/locations.py
backend/app/schemas/locations.py
frontend/src/services/locationsApi.ts
frontend/src/pages/StationsHomePage.tsx
frontend/src/pages/StationDetailPage.tsx
frontend/src/data/stationsData.ts
```

### Acceptance Criteria

- Station list can load from backend.
- Station search can load from backend.
- Station detail can load from backend.
- Unknown accessibility is displayed honestly.
- Static data is used only when backend is unavailable or demo mode is enabled.
- Ticket counter and operating hours are not shown as confirmed facts without verified data.

### Cursor / Codex Prompt

```text
Implement the ElderGo KL station search and station detail module. Add FastAPI location endpoints for popular locations, search, and detail using searchable_locations, rail_stations, accessibility_points, and station_accessibility_profiles. Connect StationsHomePage and StationDetailPage to locationsApi. Keep current station mock data as fallback only and show unknown accessibility honestly.
```

---

## Phase 9: Planning Input and Time Selection

### Goal

Connect the planning and time selection screens to real route request data.

### Current Repo Starting Point

`PlanningPage` uses static popular location suggestions. `PlanYourTimePage` stores selected time locally. Route result navigation does not send a real route request yet.

### Data Plan Alignment

DATA_PLAN expects:

```text
User enters origin, destination, and travel time
        -> Frontend calls FastAPI
        -> FastAPI stores route_request
        -> FastAPI calls Google Maps API
```

### Detailed Workflow

1. Replace static planning suggestions with Google Places autocomplete.
2. Use backend proxy or frontend helper depending on API key decision.
3. Preferred MVP decision: backend owns Google API calls to avoid exposing secret keys.
4. For each selected place, store:
   - display name
   - formatted address if available
   - lat
   - lon
   - Google place ID if available
5. Keep manual text input as fallback.
6. Store origin and destination in `AppProvider`.
7. Store departure choice in `AppProvider`.
8. Support `leave_now` for MVP.
9. Support preset time labels as frontend convenience.
10. Convert selected time to backend request fields.
11. Validate required fields before route request.
12. Save recent places after successful route request.
13. Navigate to route result only after recommendation succeeds or after route loading state starts.

### Build Items

- Planning input API integration.
- Selected place model.
- Time selection state.
- Route request body builder.
- Recent place save call.

### Files to Create or Update

```text
frontend/src/pages/PlanningPage.tsx
frontend/src/pages/PlanYourTimePage.tsx
frontend/src/services/googlePlaces.ts
frontend/src/services/routesApi.ts
frontend/src/app/AppProvider.tsx
backend/app/api/v1/endpoints/routes.py
backend/app/services/google_maps_service.py
```

### Acceptance Criteria

- User can enter or select origin.
- User can enter or select destination.
- User can choose travel time.
- Search button is disabled until required input exists.
- Request body contains origin, destination, time, preferences, and anonymous user ID when available.
- Recent places can be saved after request.

### Cursor / Codex Prompt

```text
Connect ElderGo KL planning input and time selection to real route request state. Replace static suggestions with a Google Places-backed service or backend proxy, store selected origin/destination/time in AppProvider, validate required fields, build the route recommendation request body, and call routesApi when the user asks to show the route.
```

---

## Phase 10: Google Maps Route Candidate Retrieval

### Goal

Retrieve runtime route candidates from Google Maps through the backend.

### Current Repo Starting Point

No Google Maps backend service exists yet. The frontend currently embeds static Google map iframes.

### Data Plan Alignment

DATA_PLAN says Google Maps is used at runtime for:

- autocomplete
- place details
- geocoding
- candidate routes
- transit steps
- walking steps
- map polyline

### Detailed Workflow

1. Add Google Maps API key to backend environment.
2. Implement `google_maps_service.py`.
3. Receive normalized origin, destination, and departure time from route endpoint.
4. If coordinates are missing, geocode or resolve place details.
5. Call Google Maps route/directions API for transit routes.
6. Request alternative route candidates if API supports it.
7. Extract candidate route summary.
8. Extract duration.
9. Extract walking distance.
10. Count transfers.
11. Extract transit steps.
12. Extract walking steps.
13. Extract station names from transit steps where available.
14. Extract polyline.
15. Return normalized candidate route objects to scoring service.
16. Do not store all candidate route objects permanently.
17. Convert Google API errors into friendly backend errors.

### Build Items

- Google Maps service.
- Candidate route normalizer.
- Error handling.
- Route candidate DTO for internal use.

### Service

```text
backend/app/services/google_maps_service.py
```

### Acceptance Criteria

- Backend can call Google Maps for candidate routes.
- Candidate route objects contain duration, walking distance, transfers, steps, and polyline where available.
- Backend handles missing API key gracefully in development.
- Backend does not store rejected route candidates permanently.

### Cursor / Codex Prompt

```text
Implement backend Google Maps route candidate retrieval for ElderGo KL. Add google_maps_service.py to call Google Maps with origin, destination, and departure time, normalize candidate routes into internal objects with duration, walking distance, transfers, steps, station names, and polyline, and return friendly errors. Do not permanently store all candidates.
```

---

## Phase 11: Single Route Recommendation and Scoring

### Goal

Select one elderly-friendly route from Google Maps candidates using user preferences and simple explainable scoring.

### Current Repo Starting Point

There is an empty `backend/app/services/route_service.py` but no route scoring implementation.

### Data Plan Alignment

DATA_PLAN requires the backend to:

```text
Google returns candidate routes
        -> FastAPI selects the final recommended route based on user preferences
        -> FastAPI stores recommended_route and route_steps
```

### Detailed Workflow

1. Receive candidate route list from Google Maps service.
2. Receive user travel preferences.
3. Calculate candidate metrics:
   - total duration
   - total walking distance
   - number of transfers
   - transit step count
   - accessibility hints if available
4. Apply default elderly-friendly scoring.
5. If `accessibility_first` is true, prefer routes with stronger accessibility hints and fewer unknown station risks.
6. If `least_walk` is true, reduce score for routes with long walking distance.
7. If `fewest_transfers` is true, reduce score for transfers.
8. Keep duration as a secondary factor.
9. Choose one final route.
10. Create clear `recommendation_reason`.
11. Store request in `route_requests`.
12. Store selected route in `recommended_routes`.
13. Store selected route steps in `route_steps`.
14. Send selected route to annotation service.
15. Return final route to frontend.

### Suggested Scoring Direction

```text
score =
  duration_minutes * duration_weight
  + walking_meters * walking_weight
  + transfers * transfer_weight
  + accessibility_risk_score * accessibility_weight
```

Preference weights should change based on user preference toggles, but the formula should remain understandable.

### Build Items

- Route scoring service.
- Route persistence logic.
- Recommendation reason.
- Route endpoint integration.

### Files to Create or Update

```text
backend/app/services/route_scoring_service.py
backend/app/services/route_service.py
backend/app/api/v1/endpoints/routes.py
backend/app/schemas/routes.py
```

### Acceptance Criteria

- Backend returns exactly one recommended route.
- Recommended route is persisted.
- Route steps are persisted.
- Scoring is explainable.
- User preferences affect route choice.
- Duration does not override accessibility and walking needs when preferences strongly indicate otherwise.

### Cursor / Codex Prompt

```text
Implement ElderGo KL single-route recommendation. Score Google Maps route candidates using duration, walking distance, transfers, accessibility hints, and user preferences. Select exactly one final route, explain the recommendation, store route_requests, recommended_routes, and route_steps, then return the final route to the frontend.
```

---

## Phase 12: Accessibility Annotation Service

### Goal

Generate accessibility annotations for each final route step according to DATA_PLAN.

### Current Repo Starting Point

No accessibility annotation service exists yet.

### Data Plan Alignment

DATA_PLAN defines two annotation workflows:

- transit step annotation
- walking step annotation

### Detailed Workflow: Transit Step

1. Receive final route steps.
2. Identify transit steps.
3. Check whether Google explicitly provided wheelchair/accessibility support.
4. If Google support is present:
   - mark annotation as supported or hinted
   - set source to `google_accessibility_hint`
5. If Google support is missing:
   - extract station names from step.
   - extract station coordinates if available.
   - match station against `rail_stations`.
6. Read `station_accessibility_profiles`.
7. If profile has support data:
   - create annotation from local profile.
   - set source to `local_station_accessibility_profile`.
8. If profile is missing:
   - create unknown annotation.
   - set source to `no_verified_local_data`.
9. Store annotation in `route_accessibility_annotations`.

### Detailed Workflow: Walking Step

1. Identify walking steps.
2. Read or decode walking polyline.
3. Query `accessibility_points` within 30m/50m.
4. Look for known features:
   - shelter
   - covered path
   - wheelchair support
   - lift
   - accessible entrance
   - kerb ramp
5. Create annotation if nearby support exists.
6. If no support point is found:
   - create unknown annotation.
   - avoid saying route is unsupported.
7. Store annotation in `route_accessibility_annotations`.

### Build Items

- Accessibility annotation service.
- Station matching service.
- Walking polyline proximity query.
- Annotation persistence.
- Unknown data handling.

### Files to Create or Update

```text
backend/app/services/accessibility_annotation_service.py
backend/app/services/station_matching_service.py
backend/app/services/route_service.py
backend/app/schemas/routes.py
```

### Acceptance Criteria

- Every route step has annotation output.
- Transit steps use Google hints when available.
- Transit steps fallback to local station profiles when Google hints are unavailable.
- Walking steps use nearby accessibility Points when available.
- Missing data is marked unknown.
- Annotation source is visible in backend response.
- No annotation claims unsupported unless verified data explicitly says so.

### Cursor / Codex Prompt

```text
Implement ElderGo KL accessibility annotation service. For transit steps, use Google accessibility hints first, then match local rail stations and station accessibility profiles, otherwise return unknown. For walking steps, query nearby accessibility_points within 30m/50m and annotate shelter, covered path, ramps, lifts, entrances, or wheelchair support where known. Store all annotations and never convert missing data into unsupported.
```

---

## Phase 13: Route Result Page Integration

### Goal

Replace hardcoded route result content with real backend route recommendation data.

### Current Repo Starting Point

`RouteResultPage.tsx` currently displays hardcoded route summary, hardcoded steps, hardcoded accessibility text, fake weather warning, and static Google map iframe.

### Data Plan Alignment

DATA_PLAN requires frontend to display the final recommended route, route steps, and accessibility annotations generated from backend workflows.

### Detailed Workflow

1. Read current route result from `AppProvider`.
2. If no route result exists, show a friendly empty state and button back to planning.
3. Show route summary:
   - origin
   - destination
   - duration
   - transfers
   - walking distance
   - recommendation reason
4. Show step-by-step route instructions from backend `route_steps`.
5. Show accessibility annotations from backend.
6. Use clear labels:
   - supported
   - limited information
   - unknown
   - not yet verified
7. Replace fake weather card.
8. If weather remains, label it as future feature and hide from normal route result.
9. Implement save-as-image utility.
10. Implement route sharing utility.
11. Prefer WhatsApp-friendly sharing text for elderly/caregiver flow.
12. If map polyline is available, show map view from route data.
13. If map polyline is unavailable, show text route only with a gentle notice.

### Build Items

- Dynamic route result page.
- Route summary component if useful.
- Route step component if useful.
- Accessibility annotation display.
- Save route as image.
- Share route helper.
- Empty/error states.

### Files to Create or Update

```text
frontend/src/pages/RouteResultPage.tsx
frontend/src/utils/routeImageExport.ts
frontend/src/utils/shareRoute.ts
frontend/src/types/routes.ts
frontend/src/app/AppProvider.tsx
```

### Acceptance Criteria

- Route result page does not use hardcoded route content.
- User sees only one recommended route.
- Route steps match backend response.
- Accessibility annotations match backend response.
- Unknown accessibility is visible and calm.
- Save route as image works.
- Share route creates useful route summary.
- Fake weather recommendation is removed or hidden.

### Cursor / Codex Prompt

```text
Update RouteResultPage to render the current backend route recommendation instead of hardcoded data. Show route summary, recommendation reason, route steps, accessibility annotations, text/map modes, empty/error states, save-as-image, and WhatsApp-friendly sharing. Remove or hide the fake weather warning unless a real weather source is implemented.
```

---

## Phase 14: Help, Ticket, Concession, and Privacy Content

### Goal

Preserve the current help pages and make content structured, bilingual, and safe from unverified dynamic claims.

### Current Repo Starting Point

The frontend already has:

- `HelpPage.tsx`
- `UseElderGoPage.tsx`
- `TicketGuidePage.tsx`
- `ConcessionGuidePage.tsx`
- `PrivacyInfoPage.tsx`

### Data Plan Alignment

DATA_PLAN does not require complex database tables for help content at this stage, but AI assistant answers should be able to use approved help content later.

### Detailed Workflow

1. Keep existing help page routes and UI.
2. Review all text for clarity and elderly readability.
3. Move repeated content into structured content files if useful.
4. Ensure EN/BM text exists for key help labels.
5. Make ticket and concession content general unless verified source data is added.
6. Avoid real-time fare or counter-hour claims unless backed by source.
7. Make privacy page explain anonymous device ID and stored preferences clearly.
8. Ensure large and extra-large font modes do not break help pages.
9. Prepare approved content snippets for AI assistant use.

### Build Items

- Structured help content.
- Bilingual labels.
- Privacy text aligned with anonymous user workflow.
- AI-approved content source.

### Files to Create or Update

```text
frontend/src/pages/HelpPage.tsx
frontend/src/pages/UseElderGoPage.tsx
frontend/src/pages/TicketGuidePage.tsx
frontend/src/pages/ConcessionGuidePage.tsx
frontend/src/pages/PrivacyInfoPage.tsx
frontend/src/i18n/translations.ts
frontend/src/content/helpContent.ts
```

### Acceptance Criteria

- Help pages remain easy to read.
- Help content supports EN/BM where required.
- Large and extra-large text modes remain usable.
- Privacy content matches anonymous user workflow.
- Ticket/concession pages do not claim unverified real-time facts.

### Cursor / Codex Prompt

```text
Refine the ElderGo KL help module. Keep the current help pages, structure reusable content, improve EN/BM support, ensure large font modes do not break layout, update privacy content to explain anonymous device ID and preferences, and avoid unverified dynamic ticket, concession, fare, or operating-hour claims.
```

---

## Phase 15: Controlled AI Assistant

### Goal

Connect the existing chatbot bottom sheet to a controlled backend AI workflow that only answers approved ElderGo KL travel support questions.

### Current Repo Starting Point

`AIChatbotSheet.tsx` exists visually, but there is no backend AI endpoint or guardrail service yet.

### Data Plan Alignment

DATA_PLAN includes future Epic 8 AI assistant interaction and AI conversation/message tables.

### Detailed Workflow

1. Keep chatbot entry in the center bottom navigation.
2. Keep chatbot as overlay/bottom sheet.
3. Add AI conversation endpoint.
4. Add AI message endpoint.
5. Store conversation in `ai_conversations`.
6. Store messages in `ai_messages`.
7. Add guardrail service.
8. Classify user message as in-scope or out-of-scope.
9. In-scope topics:
   - how to use ElderGo
   - current route explanation
   - station accessibility explanation
   - ticket guide
   - concession guide
   - privacy explanation
   - route sharing and saving
10. Out-of-scope topics:
   - medical advice
   - legal advice
   - financial advice
   - unsafe requests
   - unrelated general chat
   - fabricated real-time transport status
11. For in-scope answers, use approved sources only.
12. If data is missing, answer with unknown or not verified.
13. Include current route context if user asks about current route.
14. Include selected station context if user asks about station detail.
15. Return short, elderly-friendly answers.

### Build Items

- AI conversation endpoint.
- AI message endpoint.
- Guardrail service.
- Approved context builder.
- Frontend chatbot API integration.
- Unknown answer handling.

### Endpoints

```text
POST /ai/conversations
POST /ai/conversations/{conversation_id}/messages
```

### Files to Create or Update

```text
frontend/src/components/chatbot/AIChatbotSheet.tsx
frontend/src/services/aiApi.ts
frontend/src/types/ai.ts
backend/app/api/v1/endpoints/ai.py
backend/app/schemas/ai.py
backend/app/services/ai_guardrail_service.py
```

### Acceptance Criteria

- Chatbot still opens from bottom navigation.
- Chatbot does not replace current page.
- In-scope travel questions receive useful answers.
- Out-of-scope questions are politely refused.
- AI does not invent station, ticket, route, or accessibility facts.
- Unknown data is stated as unknown.
- Messages can be stored in backend.

### Cursor / Codex Prompt

```text
Connect the ElderGo KL chatbot sheet to a controlled backend AI assistant. Add AI conversation and message endpoints, store messages, add guardrails, restrict answers to ElderGo travel/app/station/accessibility/ticket/concession/privacy topics, use approved app and route context only, and make the assistant say unknown when data is missing.
```

---

## Phase 16: Final Testing and Acceptance

### Goal

Verify that the completed application satisfies the A&D epics and DATA_PLAN workflows.

### Current Repo Starting Point

There is a placeholder backend test file and no complete full-stack test workflow yet.

### Data Plan Alignment

Testing must prove that the data workflows work:

- user cache workflow
- static data ETL workflow
- station search workflow
- route recommendation workflow
- accessibility annotation workflow
- AI assistant workflow

### Detailed Workflow

1. Add frontend build check.
2. Add frontend manual UI acceptance checklist.
3. Add backend endpoint tests.
4. Add route scoring unit tests.
5. Add station matching tests.
6. Add accessibility annotation tests.
7. Add database schema load test.
8. Add ETL sample import test.
9. Add AI guardrail tests.
10. Add end-to-end manual route planning scenario.
11. Test language switching.
12. Test standard, large, and extra-large fonts.
13. Test station search with known data.
14. Test station search with unknown data.
15. Test route request with preferences.
16. Test route result save/share.
17. Test chatbot in-scope response.
18. Test chatbot out-of-scope refusal.

### Build Items

- Frontend build verification.
- Backend tests.
- Database/ETL checks.
- Manual acceptance checklist.
- Epic coverage checklist.

### Files to Create or Update

```text
backend/tests/test_health.py
backend/tests/test_users.py
backend/tests/test_locations.py
backend/tests/test_route_scoring.py
backend/tests/test_accessibility_annotations.py
backend/tests/test_ai_guardrails.py
doc/ACCEPTANCE_CHECKLIST.md
```

### Acceptance Criteria

- Frontend builds.
- Backend tests pass.
- Database schema loads.
- ETL can import sample data.
- Route scoring returns one route.
- Accessibility annotation returns supported/limited/unknown correctly.
- All A&D epics have at least manual acceptance coverage.
- All unresolved data gaps are documented.

### Cursor / Codex Prompt

```text
Add final testing and acceptance checks for ElderGo KL. Cover frontend build, backend endpoints, user cache, location search, route scoring, accessibility annotations, ETL sample import, AI guardrails, language switching, three font modes, save/share route, and epic-level manual acceptance criteria.
```

---

## 9. Epic-to-Build Mapping

| Epic | Build phases |
|---|---|
| Epic 1: Global age-friendly navigation and visual adaptation | Phase 1, Phase 6, Phase 16 |
| Epic 2: Personalized travel preference configuration | Phase 1, Phase 2, Phase 6, Phase 11 |
| Epic 3: Route planning input and time selection | Phase 2, Phase 9, Phase 10 |
| Epic 4: Single-route recommendation and scoring | Phase 10, Phase 11 |
| Epic 5: Route result, save/share, accessibility annotation | Phase 11, Phase 12, Phase 13 |
| Epic 6: Station information search and discovery | Phase 7, Phase 8 |
| Epic 7: Help and senior fare benefit information | Phase 14, Phase 15 |
| Epic 8: Controlled conversational AI assistant | Phase 15 |
| Epic 9: First-time onboarding and low-barrier start | Phase 1, Phase 6 |

---

## 10. Gap and Decision List

## Gap 1: Backend and Database Are Empty

### Current Situation

The backend and database folders exist, but the implementation is not complete.

### Decision

Build backend and database from DATA_PLAN rather than trying to infer behavior from the current frontend mock data.

---

## Gap 2: Static Frontend Data Is Not Real Transport Truth

### Current Situation

Station and route result data are hardcoded in the frontend.

### Decision

Keep frontend static data only as fallback/demo mode. Real station search and route result data must come from backend APIs.

---

## Gap 3: Supabase Is Not Used

### Current Situation

The target plan uses FastAPI and PostgreSQL/PostGIS.

### Decision

Do not introduce Supabase. All database operations go through FastAPI.

---

## Gap 4: Bus Data Source

### Current Situation

DATA_PLAN states bus routes do not use static GTFS at this stage.

### Decision

Use Google Maps for bus routing and bus route steps. Use static GTFS for rail data only.

---

## Gap 5: Accessibility Geometry

### Current Situation

DATA_PLAN uses Point geometry only for accessibility data.

### Decision

Do not implement LineString accessibility features in MVP. Walking-step annotation uses proximity queries against Point data.

---

## Gap 6: Missing Accessibility Data

### Current Situation

Some stations or walking paths may not have verified accessibility data.

### Decision

Display unknown, limited information, or not yet verified. Never convert missing data into unsupported.

---

## Gap 7: Weather Recommendation

### Current Situation

The current route result page contains a hardcoded rain warning.

### Decision

Remove or hide fake weather recommendation unless a real weather API is added later.

---

## Gap 8: Ticket Counter and Operating Hours

### Current Situation

Current frontend mock stations include ticket counter and operating hour fields.

### Decision

Do not show ticket counter or operating hours as verified facts unless a reliable source is added. If shown, label as not yet verified.

---

## Gap 9: Chatbot Scope

### Current Situation

The chatbot UI exists, but the backend scope is not implemented.

### Decision

Build a controlled assistant. It should answer only ElderGo KL travel, route, station, ticket, concession, accessibility, privacy, and app usage questions.

---

## Gap 10: App Routing

### Current Situation

The frontend uses local state for page navigation.

### Decision

Keep local state navigation for MVP unless URL deep linking becomes required. Stabilize app state first before introducing React Router.

---

## 11. Final Recommended Build Order

The recommended build order is:

1. Confirm current project baseline.
2. Stabilise frontend app state and shell.
3. Add frontend types and service layer.
4. Implement database schema.
5. Implement FastAPI foundation.
6. Add ORM models and Pydantic schemas.
7. Implement anonymous user, settings, preferences, and onboarding.
8. Build static rail/accessibility ETL.
9. Build station search and station detail.
10. Build planning input and time selection integration.
11. Build Google Maps route candidate retrieval.
12. Build single-route scoring and persistence.
13. Build accessibility annotation service.
14. Connect route result page to backend data.
15. Refine help/ticket/concession/privacy content.
16. Connect controlled AI assistant.
17. Run final testing and acceptance.

This order is recommended because station and accessibility data should exist before route annotation, and app settings/preferences should exist before final route scoring is connected to user choices.

---

## 12. Acceptance Criteria Testing Checklist

### Epic 1 Checklist

- [ ] User can switch from standard font to large font.
- [ ] User can switch from large font to extra-large font.
- [ ] User can cycle back to standard font.
- [ ] No key screen has horizontal scrolling in large or extra-large mode.
- [ ] User can switch between English and Bahasa Melayu.
- [ ] Bottom navigation remains visible and usable.
- [ ] Chatbot opens as overlay without losing page state.

### Epic 2 Checklist

- [ ] User can enable accessibility-first preference.
- [ ] User can enable least-walking preference.
- [ ] User can enable fewest-transfers preference.
- [ ] Preferences are saved.
- [ ] Preferences are restored for returning user.
- [ ] Preferences influence route scoring.

### Epic 3 Checklist

- [ ] User can enter or select origin.
- [ ] User can enter or select destination.
- [ ] User can select departure time.
- [ ] Route request is not submitted when required fields are missing.
- [ ] Frontend sends valid route request body.
- [ ] Recent places are stored when available.

### Epic 4 Checklist

- [ ] Backend calls Google Maps for route candidates.
- [ ] Backend scores route candidates.
- [ ] Backend returns one recommended route only.
- [ ] Recommendation includes an understandable reason.
- [ ] Final route is stored in `recommended_routes`.
- [ ] Final route steps are stored in `route_steps`.

### Epic 5 Checklist

- [ ] Route result page shows backend route summary.
- [ ] Route result page shows backend steps.
- [ ] Each route step has accessibility annotation.
- [ ] Unknown data is shown as unknown.
- [ ] User can save route as image.
- [ ] User can share route summary.
- [ ] Fake weather warning is removed or hidden unless real weather source exists.

### Epic 6 Checklist

- [ ] Station search uses backend `/locations/search`.
- [ ] Popular stations use backend `/locations/popular`.
- [ ] Station detail uses backend `/locations/{location_id}`.
- [ ] Station accessibility status is shown.
- [ ] Missing station accessibility data is shown as unknown.
- [ ] Static station data is fallback/demo only.

### Epic 7 Checklist

- [ ] Help page is available.
- [ ] Use ElderGo guide is available.
- [ ] Ticket guide is available.
- [ ] Concession guide is available.
- [ ] Privacy page is available.
- [ ] Content is readable in large and extra-large modes.
- [ ] Unverified fare/counter/hour claims are not shown as confirmed facts.

### Epic 8 Checklist

- [ ] Chatbot opens from bottom navigation.
- [ ] Chatbot sends messages to backend.
- [ ] Backend stores AI conversation and messages.
- [ ] Guardrail allows in-scope travel/app questions.
- [ ] Guardrail refuses out-of-scope questions.
- [ ] AI says unknown when data is missing.
- [ ] AI does not fabricate route, station, or accessibility facts.

### Epic 9 Checklist

- [ ] First-time user sees onboarding or low-barrier getting started help.
- [ ] User can complete onboarding.
- [ ] Onboarding completion is saved.
- [ ] Returning user does not see onboarding repeatedly.
- [ ] Onboarding remains usable in large and extra-large modes.

### Technical Checklist

- [ ] Frontend build passes.
- [ ] Backend starts.
- [ ] `/health` endpoint passes.
- [ ] Database schema loads.
- [ ] ETL scripts can run with sample data.
- [ ] Route scoring tests pass.
- [ ] Accessibility annotation tests pass.
- [ ] AI guardrail tests pass.

---

## 13. Simple Team Explanation

ElderGo KL should be built by keeping the current Figma-based React frontend and slowly replacing its static demo behavior with real backend data.

The frontend is the elderly-friendly interface. The backend is the trusted middle layer. PostgreSQL/PostGIS stores local rail, accessibility, route result, and user cache data. Google Maps gives live route candidates. The backend chooses only one best route and annotates that route with accessibility information.

The team should not invent missing transport facts. If accessibility, ticket, operating hour, weather, or station data is not verified, the app should say it is unknown or not yet verified.

The safest implementation path is:

```text
Stabilise frontend
    -> add API contracts
    -> build database
    -> build backend
    -> load static rail/accessibility data
    -> connect station search
    -> connect route planning
    -> add route scoring
    -> add accessibility annotations
    -> connect route result
    -> add controlled AI
    -> test against all epics
```

This approach lets the team keep the existing visual progress while making the product technically correct and aligned with DATA_PLAN.
