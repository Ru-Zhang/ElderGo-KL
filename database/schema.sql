CREATE EXTENSION IF NOT EXISTS postgis;
CREATE EXTENSION IF NOT EXISTS pg_trgm;

CREATE TABLE IF NOT EXISTS rail_agencies (
    agency_id TEXT PRIMARY KEY,
    source_system TEXT NOT NULL,
    agency_name TEXT NOT NULL,
    agency_url TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS rail_routes (
    route_id TEXT PRIMARY KEY,
    agency_id TEXT REFERENCES rail_agencies(agency_id),
    source_system TEXT NOT NULL,
    route_short_name TEXT,
    route_long_name TEXT,
    rail_type TEXT,
    route_color TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS rail_stations (
    station_id TEXT PRIMARY KEY,
    source_system TEXT NOT NULL,
    stop_id TEXT,
    station_name TEXT NOT NULL,
    lat DOUBLE PRECISION,
    lon DOUBLE PRECISION,
    geom GEOMETRY(Point, 4326),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS rail_station_routes (
    station_route_id TEXT PRIMARY KEY,
    station_id TEXT NOT NULL REFERENCES rail_stations(station_id) ON DELETE CASCADE,
    route_id TEXT NOT NULL REFERENCES rail_routes(route_id) ON DELETE CASCADE,
    stop_sequence INTEGER,
    direction_id TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS accessibility_points (
    accessibility_point_id TEXT PRIMARY KEY,
    source_id TEXT,
    source_system TEXT,
    name TEXT,
    name_en TEXT,
    feature_type TEXT,
    wheelchair TEXT,
    lift TEXT,
    ramp TEXT,
    shelter TEXT,
    covered TEXT,
    accessible_entrance TEXT,
    kerb_ramp TEXT,
    tags JSONB NOT NULL DEFAULT '{}'::jsonb,
    confidence TEXT NOT NULL DEFAULT 'unknown',
    lat DOUBLE PRECISION,
    lon DOUBLE PRECISION,
    geom GEOMETRY(Point, 4326),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT accessibility_points_confidence_check
        CHECK (confidence IN ('high', 'medium', 'low', 'unknown'))
);

CREATE TABLE IF NOT EXISTS station_accessibility_profiles (
    station_id TEXT PRIMARY KEY REFERENCES rail_stations(station_id) ON DELETE CASCADE,
    accessibility_status TEXT NOT NULL DEFAULT 'unknown',
    confidence TEXT NOT NULL DEFAULT 'unknown',
    source_list JSONB NOT NULL DEFAULT '[]'::jsonb,
    note TEXT,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT station_accessibility_status_check
        CHECK (accessibility_status IN ('supported', 'limited', 'unknown', 'not_verified')),
    CONSTRAINT station_accessibility_confidence_check
        CHECK (confidence IN ('high', 'medium', 'low', 'unknown'))
);

CREATE TABLE IF NOT EXISTS anonymous_users (
    anonymous_user_id TEXT PRIMARY KEY,
    hashed_device_id TEXT NOT NULL UNIQUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    last_seen_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS user_ui_settings (
    anonymous_user_id TEXT PRIMARY KEY REFERENCES anonymous_users(anonymous_user_id) ON DELETE CASCADE,
    language TEXT NOT NULL DEFAULT 'EN',
    font_size TEXT NOT NULL DEFAULT 'standard',
    onboarding_completed BOOLEAN NOT NULL DEFAULT FALSE,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT user_ui_language_check CHECK (language IN ('EN', 'BM')),
    CONSTRAINT user_ui_font_size_check CHECK (font_size IN ('standard', 'large', 'extra_large'))
);

CREATE TABLE IF NOT EXISTS user_travel_preferences (
    anonymous_user_id TEXT PRIMARY KEY REFERENCES anonymous_users(anonymous_user_id) ON DELETE CASCADE,
    accessibility_first BOOLEAN NOT NULL DEFAULT FALSE,
    least_walk BOOLEAN NOT NULL DEFAULT FALSE,
    fewest_transfers BOOLEAN NOT NULL DEFAULT FALSE,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS recent_place_cache (
    recent_place_id TEXT PRIMARY KEY,
    anonymous_user_id TEXT NOT NULL REFERENCES anonymous_users(anonymous_user_id) ON DELETE CASCADE,
    place_role TEXT NOT NULL,
    display_name TEXT NOT NULL,
    google_place_id TEXT,
    lat DOUBLE PRECISION,
    lon DOUBLE PRECISION,
    used_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT recent_place_role_check CHECK (place_role IN ('origin', 'destination'))
);

CREATE TABLE IF NOT EXISTS route_requests (
    route_request_id TEXT PRIMARY KEY,
    anonymous_user_id TEXT REFERENCES anonymous_users(anonymous_user_id) ON DELETE SET NULL,
    origin_name TEXT NOT NULL,
    origin_google_place_id TEXT,
    origin_lat DOUBLE PRECISION,
    origin_lon DOUBLE PRECISION,
    destination_name TEXT NOT NULL,
    destination_google_place_id TEXT,
    destination_lat DOUBLE PRECISION,
    destination_lon DOUBLE PRECISION,
    departure_time TEXT NOT NULL DEFAULT 'now',
    preferences_snapshot JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS recommended_routes (
    recommended_route_id TEXT PRIMARY KEY,
    route_request_id TEXT NOT NULL REFERENCES route_requests(route_request_id) ON DELETE CASCADE,
    duration_minutes INTEGER,
    transfers INTEGER,
    walking_distance_meters INTEGER,
    recommendation_reason TEXT,
    map_polyline TEXT,
    google_route_summary JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS route_steps (
    route_step_id TEXT PRIMARY KEY,
    recommended_route_id TEXT NOT NULL REFERENCES recommended_routes(recommended_route_id) ON DELETE CASCADE,
    step_number INTEGER NOT NULL,
    step_type TEXT NOT NULL,
    instruction TEXT NOT NULL,
    duration_minutes INTEGER,
    distance_meters INTEGER,
    transit_line TEXT,
    from_station_name TEXT,
    to_station_name TEXT,
    google_step_json JSONB NOT NULL DEFAULT '{}'::jsonb,
    CONSTRAINT route_step_type_check CHECK (step_type IN ('walking', 'transit', 'arrival'))
);

CREATE TABLE IF NOT EXISTS route_accessibility_annotations (
    route_accessibility_annotation_id TEXT PRIMARY KEY,
    route_step_id TEXT NOT NULL REFERENCES route_steps(route_step_id) ON DELETE CASCADE,
    accessibility_status TEXT NOT NULL DEFAULT 'unknown',
    message TEXT NOT NULL,
    source TEXT NOT NULL,
    supporting_data JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT route_annotation_status_check
        CHECK (accessibility_status IN ('supported', 'limited', 'unknown', 'not_verified'))
);

CREATE TABLE IF NOT EXISTS searchable_locations (
    searchable_location_id TEXT PRIMARY KEY,
    source_table TEXT NOT NULL,
    source_id TEXT NOT NULL,
    display_name TEXT NOT NULL,
    location_type TEXT NOT NULL,
    accessibility_status TEXT NOT NULL DEFAULT 'unknown',
    confidence TEXT NOT NULL DEFAULT 'unknown',
    lat DOUBLE PRECISION,
    lon DOUBLE PRECISION,
    geom GEOMETRY(Point, 4326),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT searchable_location_type_check
        CHECK (location_type IN ('rail_station', 'accessibility_point', 'place')),
    CONSTRAINT searchable_location_status_check
        CHECK (accessibility_status IN ('supported', 'limited', 'unknown', 'not_verified'))
);

CREATE TABLE IF NOT EXISTS ai_conversations (
    conversation_id TEXT PRIMARY KEY,
    anonymous_user_id TEXT REFERENCES anonymous_users(anonymous_user_id) ON DELETE SET NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS ai_messages (
    ai_message_id TEXT PRIMARY KEY,
    conversation_id TEXT NOT NULL REFERENCES ai_conversations(conversation_id) ON DELETE CASCADE,
    role TEXT NOT NULL,
    message TEXT NOT NULL,
    in_scope BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT ai_message_role_check CHECK (role IN ('user', 'assistant', 'system'))
);

CREATE INDEX IF NOT EXISTS idx_rail_stations_geom ON rail_stations USING GIST (geom);
CREATE INDEX IF NOT EXISTS idx_rail_stations_name_trgm ON rail_stations USING GIN (station_name gin_trgm_ops);
CREATE INDEX IF NOT EXISTS idx_accessibility_points_geom ON accessibility_points USING GIST (geom);
CREATE INDEX IF NOT EXISTS idx_searchable_locations_geom ON searchable_locations USING GIST (geom);
CREATE INDEX IF NOT EXISTS idx_searchable_locations_name_trgm ON searchable_locations USING GIN (display_name gin_trgm_ops);
CREATE INDEX IF NOT EXISTS idx_anonymous_users_hashed_device_id ON anonymous_users (hashed_device_id);
CREATE INDEX IF NOT EXISTS idx_route_requests_user ON route_requests (anonymous_user_id);
CREATE INDEX IF NOT EXISTS idx_recommended_routes_request ON recommended_routes (route_request_id);
CREATE INDEX IF NOT EXISTS idx_route_steps_route ON route_steps (recommended_route_id);
CREATE INDEX IF NOT EXISTS idx_route_annotations_step ON route_accessibility_annotations (route_step_id);
CREATE INDEX IF NOT EXISTS idx_ai_messages_conversation ON ai_messages (conversation_id);
