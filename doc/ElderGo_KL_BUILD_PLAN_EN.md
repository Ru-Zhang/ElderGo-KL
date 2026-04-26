# ElderGo KL Build Plan

## 1. Purpose of This Document

This build plan translates the ElderGo KL Analysis and Design document and the DATA_PLAN_EN.md file into a practical development workflow for Cursor, Codex, and the project team.

The main goal is to make sure the product can fulfil the designed epics, user stories, and acceptance criteria while staying aligned with the agreed data architecture.

The key decision is:

```text
Figma defines how ElderGo KL should look.
DATA_PLAN defines how ElderGo KL should work.
FastAPI connects the frontend, Google Maps, and PostgreSQL/PostGIS.
```

This means the team does not need to throw away the Figma UI. The Figma design should be converted into reusable React components and then connected to the backend and database workflows described in DATA_PLAN_EN.md.

---

## 2. Product Direction Summary

ElderGo KL is an elderly-friendly public transport route planning web system for Klang Valley. The intended users are elderly people with weaker eyesight, slower mobility, lower digital literacy, and possible language barriers. The product should reduce anxiety by showing simple screens, large text, clear navigation, fewer steps, and only one recommended route instead of many confusing route options.

The product should support:

- Large text switching.
- English and Bahasa Melayu switching.
- Persistent bottom navigation.
- Personal travel preferences.
- Origin and destination input with autocomplete.
- Time selection before route recommendation.
- One final recommended route.
- Accessibility annotations for route steps and stations.
- Station search and station detail pages.
- Help pages for using the system, tickets, concession, and privacy.
- Save route as image.
- Share route with family, especially via WhatsApp.
- Controlled AI assistant for travel-related support only.
- First-time onboarding for elderly users.

The most important rule is that the system must not fabricate accessibility, ticket, station, or route information. Missing accessibility data should be displayed as `unknown`, `limited information`, or `not yet verified`, not as unsupported.

---

## 3. Technical Architecture

The recommended architecture is:

```text
React / TypeScript Frontend
        ↓ REST API
FastAPI Backend
        ↓ SQL / ORM
PostgreSQL + PostGIS
        ↓
Static rail data + accessibility data + route result records

Google Maps API is used at runtime for:
- autocomplete
- place details
- geocoding
- candidate routes
- transit steps
- walking steps
- map polyline
```

The frontend must not connect directly to PostgreSQL. All database reads and writes should go through FastAPI.

---

## 4. Relationship Between Figma and DATA_PLAN

### 4.1 Current Figma Strengths

The provided Figma screens already match many of the designed epics:

| Figma Screen | Matching Epic / Function |
|---|---|
| Planning page with origin, destination, and search | Epic 3: Route Planning Input and Time Selection |
| Preference page with accessibility, least walk, and fewest transfers | Epic 2: Personalized Travel Preference Configuration |
| Chatbot bottom sheet | Epic 8: Controlled Conversational AI Travel Assistant |
| Help page with Use ElderGo, Buy Ticket, Apply for Concession, Privacy Info | Epic 7: Help and Senior Fare Benefit Information |
| Station page with search and popular stations | Epic 6: Station Information Search and Discovery |
| Top BM and A+ controls | Epic 1: Language and Font Adaptation |
| Bottom navigation | Epic 1: Persistent Global Bottom Navigation |

The visual direction is good and should be reused.

### 4.2 Required Technical Shift

The current Figma-based implementation should not remain as static pages. It should be shifted into a data-driven structure:

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

For example:

- The Station page should not permanently hardcode “KL Sentral”, “Pasar Seni”, “Bukit Bintang”, and “SunU-Monash”. It can use them as temporary fallback data, but the real version should call `/locations/popular` and `/locations/search`.
- The Preference page should not only store toggles in React state. It should save preferences to `/users/{anonymous_user_id}/travel-preferences`.
- The Chatbot button should visually stay in the centre bottom navigation, but technically it should open an overlay or bottom sheet instead of replacing the current page. This preserves the current page state.
- The language and font buttons should update the whole app without resetting current inputs.

---

## 5. Recommended Project Structure

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

## 6. Backend Data Tables Required

The backend database should follow DATA_PLAN_EN.md.

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

### 6.3 Required PostgreSQL Extensions

```sql
CREATE EXTENSION IF NOT EXISTS postgis;
CREATE EXTENSION IF NOT EXISTS pg_trgm;
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
```

### 6.4 Important Database Rule

The system should store only the final recommended route, not every Google candidate route. Candidate routes can be kept temporarily in backend memory for scoring, but only the selected final route should be saved into `recommended_routes`, `route_steps`, and `route_accessibility_annotations`.

---

## 7. Full Build Workflow

## Phase 1 — Stabilise the Figma Frontend Shell

### Goal

Convert the Figma UI into a reusable mobile-first React shell.

### Build Items

- `TopBar`
- `BottomNav`
- `AppShell`
- `AppProvider`
- global font size mode
- global language mode
- chatbot overlay trigger

### Acceptance Criteria Covered

- Epic 1: font size switching.
- Epic 1: language switching.
- Epic 1: persistent bottom navigation.
- Epic 8: manually open AI assistant without losing page state.

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

## Phase 2 — Create Backend Database Schema

### Goal

Create the PostgreSQL/PostGIS schema before connecting route planning and station search.

### Build Items

- `sql/001_init_schema.sql`
- FastAPI `/health` endpoint
- database connection setup
- SQLAlchemy or SQLModel models
- required spatial and search indexes

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

## Phase 3 — Build ETL Pipeline

### Goal

Import static rail and accessibility data into PostgreSQL/PostGIS.

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

### Important Rule

Missing accessibility data must be shown as `unknown`, not `not_supported`.

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

## Phase 4 — Build Anonymous User, Settings, Preferences, and Onboarding

### Goal

Allow the app to remember language, font size, onboarding status, and travel preferences.

### Backend Endpoints

```text
POST /users/resolve
GET /users/{anonymous_user_id}/settings
PUT /users/{anonymous_user_id}/ui-settings
PUT /users/{anonymous_user_id}/travel-preferences
```

### Frontend Flow

```text
First app load
    → read or generate local device_id
    → POST /users/resolve
    → receive anonymous_user_id
    → restore language, font size, onboarding_completed, and preferences
```

### Acceptance Criteria Covered

- Epic 1: language and font size state persistence.
- Epic 2: preference saving and continued effectiveness.
- Epic 9: first-time onboarding.

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

## Phase 5 — Build Station Module

### Why This Should Be Built Before Route Planning

Station search is easier to test first, and route planning later needs station accessibility profiles for annotation.

### Backend Endpoints

```text
GET /locations/popular
GET /locations/search?q=KL Sentral
GET /locations/{location_id}
```

### Data Tables Used

```text
searchable_locations
rail_stations
station_accessibility_profiles
accessibility_points
```

### Station Detail Fields

The Analysis and Design document expects the station detail page to show:

- station name
- accessibility support status
- ticket counter information
- operating hours

However, DATA_PLAN_EN.md currently does not include ticket counter and operating hours fields. Therefore, the MVP should display:

```text
Ticket counter: Not yet verified
Operating hours: Not yet verified
```

This still satisfies the acceptance criteria because missing fields should be explicitly shown instead of being hidden.

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

## Phase 6 — Build Planning Input and Time Selection

### Goal

Make the Planning screen functional.

### Frontend Flow

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

### Required Request Body

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

## Phase 7 — Build Route Recommendation Engine

### Goal

Google returns candidate routes. ElderGo KL selects only one final recommended route.

### Backend Endpoint

```text
POST /routes/recommend
```

### Backend Workflow

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

### Suggested Scoring Formula

```text
score =
    total_duration_min * 1.0
  + walking_distance_m * walking_weight
  + transfer_count * transfer_weight
  + accessibility_unknown_penalty
  + accessibility_problem_penalty
```

### Suggested Preference Weights

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

### Important Rules

- Do not show multiple route cards.
- Do not ask the user to compare routes.
- Do not store all Google candidate routes in the database.
- If no route fully satisfies preferences, return the closest alternative with a friendly explanation.
- If preference data is invalid, fall back to default scoring.

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

## Phase 8 — Build Accessibility Annotation Service

### Goal

Show truthful accessibility hints on the route result page.

### Backend Service

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

## Phase 9 — Build Route Result Page

### Goal

Show the final route in a simple, elderly-friendly way.

### Required Features

- Text View by default.
- Map View switch.
- Same route data in both views.
- Route summary at the top.
- Step-by-step route cards.
- Accessibility labels.
- Weather and rush-hour reminder card.
- Save as image.
- Share by WhatsApp and copy link.
- Friendly fallback if map fails.

### Important Rule About Weather

Weather and rush-hour reminders should inform the user, but they should not automatically replace the generated route unless the team updates the acceptance criteria and DATA_PLAN.

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

## Phase 10 — Build Help Module

### Goal

Provide stable, easy-to-read help content.

### Pages Required

- HelpPage
- UseElderGoPage
- TicketGuidePage
- ConcessionGuidePage
- PrivacyInfoPage

### Implementation Choice

For MVP, help content can be stored as frontend JSON or markdown:

```text
src/content/help.en.json
src/content/help.ms.json
```

A database is not required unless the team wants editable CMS-style content.

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

## Phase 11 — Build Controlled AI Assistant

### Goal

Provide chatbot help without becoming an unreliable open-ended AI.

### Backend Endpoints

```text
POST /ai/conversations
POST /ai/conversations/{conversation_id}/messages
```

### Supported Question Areas

- route questions
- weather questions
- station accessibility questions
- ticket guide questions
- concession guide questions
- privacy questions
- app usage questions

### Not Supported

- unrelated general knowledge
- medical advice
- financial advice
- fabricated station information
- fabricated fare information
- fabricated accessibility information

### Data Sources for AI Answers

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

## 8. Epic-to-Build Mapping

| Epic | Build Module | Backend Needed? | DATA_PLAN Support |
|---|---|---:|---|
| Epic 1: Global age-friendly navigation | TopBar, BottomNav, AppContext, i18n | Yes | `user_ui_settings` |
| Epic 2: Preferences | PreferencePage, first-time popup | Yes | `user_travel_preferences` |
| Epic 3: Planning input and time | PlanningPage, Google autocomplete, PlanYourTimePage | Partly | route request format |
| Epic 4: One-route recommendation | Route scoring engine | Yes | `route_requests`, `recommended_routes` |
| Epic 5: Result, save, share | RouteResultPage, annotations, image export, sharing | Yes | `route_steps`, `route_accessibility_annotations` |
| Epic 6: Station search | StationsHomePage, StationDetailPage | Yes | `searchable_locations`, `rail_stations`, `station_accessibility_profiles` |
| Epic 7: Help, fare, privacy | Static help pages | Not necessary for MVP | static JSON/content files |
| Epic 8: AI assistant | AIChatbotSheet, controlled backend | Yes | `ai_conversations`, `ai_messages` |
| Epic 9: Onboarding | Onboarding overlay / UseElderGo guide | Yes | `user_ui_settings.onboarding_completed` |

---

## 9. Gap and Decision List

## Gap 1 — Station Ticket Counter and Operating Hours

The Analysis and Design document expects station details to show ticket counter information and operating hours, but DATA_PLAN_EN.md does not currently define these fields.

### MVP Decision

Show:

```text
Ticket counter: Not yet verified
Operating hours: Not yet verified
```

### Future Enhancement

Add a table:

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

The design mentions weather and rush-hour reminders, but DATA_PLAN_EN.md does not define weather tables.

### MVP Decision

Use weather as a runtime reminder only. Do not store it in route result tables unless the team updates the data plan.

### Important Rule

Do not automatically replace the selected route because of weather. Show a warning or reminder card instead.

---

## Gap 3 — Chatbot Scope

The chatbot must not become a general-purpose AI.

### MVP Decision

Use controlled intent detection and answer only from approved sources.

Approved sources:

```text
current route result
station database
accessibility profiles
static help content
weather reminder
fallback messages
```

---

## Gap 4 — Figma Bottom Navigation Chatbot Button

The Figma design shows Chatbot as a centre bottom navigation item.

### Technical Decision

Keep the visual design, but implement it as an overlay trigger, not as a full page navigation.

This is better because the AI assistant should preserve the current page state.

---

## Gap 5 — Supabase Is Not Used

The current DATA_PLAN is PostgreSQL/PostGIS + FastAPI. If the team is not allowed to use Supabase, this is fine.

### MVP Decision

Use local or hosted PostgreSQL with PostGIS. All access goes through FastAPI.

---

## 10. Final Recommended Build Order

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

- Font size cycles standard → large → extra_large → standard.
- Font size is restored after refresh.
- No horizontal scrolling in large text mode.
- Language switch does not clear typed input.
- Bottom navigation is available from all major pages.

### Epic 2 Checklist

- First-time preference popup appears only when needed.
- Popup shows Accessibility First, Least Walking, and Fewest Transfers.
- Save stores preferences.
- Cancel allows planning in default mode.
- Preference page allows later modification.
- Route scoring uses updated preferences.

### Epic 3 Checklist

- Origin and destination support autocomplete.
- Search is blocked when input is incomplete.
- Valid input opens Plan Your Time page.
- Time options include Now, Morning, Afternoon, Evening.
- Confirm starts route recommendation.

### Epic 4 Checklist

- Only one recommended route is displayed.
- Internal Google candidates are hidden from user.
- Preferences affect scoring.
- Conflicting preferences are handled internally.
- Invalid preference data falls back to default mode.

### Epic 5 Checklist

- Route result opens in Text View by default.
- Map View switch does not reload the full page.
- Summary shows total time, transfers, and walking distance.
- Route steps are shown in order.
- Accessibility information is shown honestly.
- Weather/rush-hour reminders do not automatically replace the route.
- Save exports route image.
- Share supports WhatsApp and copy link.

### Epic 6 Checklist

- Stations page shows Top 4 popular stations.
- Search returns matching station results.
- No exact match shows friendly prompt.
- Station detail shows accessibility status.
- Missing detail fields show “Not yet verified”.
- API failure shows retry/back option.

### Epic 7 Checklist

- Help page links to Use ElderGo, Ticket Guide, Concession Guide, and Privacy Info.
- Long content is vertical and readable.
- Images can be enlarged if used.
- Privacy content follows current language.
- Failed content loading does not show a blank page.

### Epic 8 Checklist

- Chatbot opens manually.
- Closing chatbot preserves current page state.
- Supported questions return structured answers.
- Ambiguous station names trigger clarification.
- Missing data is clearly stated.
- Out-of-scope questions are rejected politely.
- Repeated failures switch to button guidance.

### Epic 9 Checklist

- Onboarding appears only on first entry.
- User can skip onboarding.
- Skipping does not block app usage.
- Main entries remain visible after onboarding.
- Preference onboarding still appears when entering Planning if needed.

---

## 12. Simple Team Explanation

The current Figma UI is useful and should not be discarded. It already gives us the correct visual direction for elderly users. However, Figma is only the face of the product. The DATA_PLAN is the real technical backbone. We need to convert the Figma screens into reusable React components, then connect them to FastAPI and PostgreSQL/PostGIS.

Google Maps should generate possible routes, but ElderGo KL should select only one route based on the user’s preferences. The database should store rail stations, accessibility points, route requests, final recommended routes, route steps, and accessibility annotations. It should not store every Google candidate route.

The safest development approach is to build the product in layers: first the frontend shell, then database schema, then ETL data, then user settings, station search, route planning, route result, help pages, and finally the controlled AI assistant.

Any information that is missing or unverified should be shown honestly as “unknown”, “limited information”, or “not yet verified”. The system should not guess or fabricate accessibility, fare, station, or route information.

