-- ElderGo KL PostgreSQL/PostGIS schema aligned with DATA_PLAN.md.

CREATE EXTENSION IF NOT EXISTS postgis;
CREATE EXTENSION IF NOT EXISTS pg_trgm;
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

CREATE TABLE IF NOT EXISTS rail_agencies (
    agency_id TEXT PRIMARY KEY,
    source_system TEXT NOT NULL,
    agency_name TEXT,
    agency_url TEXT,
    agency_timezone TEXT
);

CREATE TABLE IF NOT EXISTS rail_routes (
    route_id TEXT PRIMARY KEY,
    agency_id TEXT REFERENCES rail_agencies(agency_id) ON DELETE SET NULL,
    source_system TEXT NOT NULL,
    route_short_name TEXT,
    route_long_name TEXT,
    rail_type TEXT,
    route_color TEXT
);

CREATE TABLE IF NOT EXISTS rail_stations (
    station_id TEXT PRIMARY KEY,
    source_system TEXT NOT NULL,
    stop_id TEXT NOT NULL,
    station_name TEXT NOT NULL,
    lat DOUBLE PRECISION,
    lon DOUBLE PRECISION,
    geom geometry(Point, 4326)
);

CREATE TABLE IF NOT EXISTS rail_station_routes (
    station_route_id TEXT PRIMARY KEY,
    station_id TEXT NOT NULL REFERENCES rail_stations(station_id) ON DELETE CASCADE,
    route_id TEXT NOT NULL REFERENCES rail_routes(route_id) ON DELETE CASCADE,
    stop_sequence INTEGER,
    direction_id TEXT
);

CREATE TABLE IF NOT EXISTS station_groups (
    station_group_id TEXT PRIMARY KEY,
    display_name TEXT NOT NULL,
    geom geometry(Point, 4326),
    accessibility_status TEXT NOT NULL DEFAULT 'unknown',
    confidence TEXT NOT NULL DEFAULT 'low',
    source_systems JSONB NOT NULL DEFAULT '[]'::jsonb,
    CONSTRAINT chk_station_groups_status CHECK (
        accessibility_status IN ('supported', 'not_supported', 'unknown')
    ),
    CONSTRAINT chk_station_groups_confidence CHECK (
        confidence IN ('high', 'medium', 'low')
    )
);

CREATE TABLE IF NOT EXISTS station_group_members (
    station_group_id TEXT NOT NULL REFERENCES station_groups(station_group_id) ON DELETE CASCADE,
    station_id TEXT NOT NULL REFERENCES rail_stations(station_id) ON DELETE CASCADE,
    PRIMARY KEY (station_group_id, station_id)
);

CREATE TABLE IF NOT EXISTS accessibility_points (
    accessibility_point_id TEXT PRIMARY KEY,
    source_id TEXT,
    name TEXT,
    name_en TEXT,
    name_ms TEXT,
    feature_type TEXT,
    accessibility_type TEXT,
    wheelchair TEXT,
    shelter TEXT,
    covered TEXT,
    tactile_paving TEXT,
    kerb TEXT,
    bench TEXT,
    geom geometry(Point, 4326),
    raw_properties JSONB
);

CREATE TABLE IF NOT EXISTS station_accessibility_profiles (
    station_id TEXT PRIMARY KEY REFERENCES rail_stations(station_id) ON DELETE CASCADE,
    accessibility_status TEXT NOT NULL DEFAULT 'unknown',
    confidence TEXT NOT NULL DEFAULT 'low',
    source_list JSONB NOT NULL DEFAULT '[]'::jsonb,
    note TEXT,
    CONSTRAINT chk_station_accessibility_profiles_status CHECK (
        accessibility_status IN ('supported', 'not_supported', 'unknown')
    ),
    CONSTRAINT chk_station_accessibility_profiles_confidence CHECK (
        confidence IN ('high', 'medium', 'low')
    )
);

CREATE TABLE IF NOT EXISTS anonymous_users (
    anonymous_user_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    device_id_hash TEXT NOT NULL UNIQUE,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    last_seen_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS user_ui_settings (
    anonymous_user_id UUID PRIMARY KEY REFERENCES anonymous_users(anonymous_user_id) ON DELETE CASCADE,
    language_code TEXT NOT NULL DEFAULT 'en',
    font_size_mode TEXT NOT NULL DEFAULT 'standard',
    onboarding_completed BOOLEAN NOT NULL DEFAULT FALSE,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT chk_user_ui_settings_language CHECK (language_code IN ('en', 'ms')),
    CONSTRAINT chk_user_ui_settings_font CHECK (font_size_mode IN ('standard', 'large', 'extra_large'))
);

CREATE TABLE IF NOT EXISTS user_travel_preferences (
    anonymous_user_id UUID PRIMARY KEY REFERENCES anonymous_users(anonymous_user_id) ON DELETE CASCADE,
    accessibility_first BOOLEAN NOT NULL DEFAULT TRUE,
    less_walking BOOLEAN NOT NULL DEFAULT TRUE,
    fewer_transfers BOOLEAN NOT NULL DEFAULT TRUE,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS recent_place_cache (
    recent_place_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    anonymous_user_id UUID NOT NULL REFERENCES anonymous_users(anonymous_user_id) ON DELETE CASCADE,
    place_role TEXT NOT NULL,
    place_name TEXT NOT NULL,
    google_place_id TEXT,
    lat DOUBLE PRECISION,
    lon DOUBLE PRECISION,
    geom geometry(Point, 4326),
    last_used_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT chk_recent_place_cache_role CHECK (place_role IN ('origin', 'destination'))
);

CREATE TABLE IF NOT EXISTS route_requests (
    route_request_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    anonymous_user_id UUID REFERENCES anonymous_users(anonymous_user_id) ON DELETE SET NULL,
    origin_text TEXT,
    destination_text TEXT,
    origin_geom geometry(Point, 4326),
    destination_geom geometry(Point, 4326),
    travel_time TIMESTAMP,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS recommended_routes (
    recommended_route_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    route_request_id UUID NOT NULL REFERENCES route_requests(route_request_id) ON DELETE CASCADE,
    total_duration_min INTEGER,
    walking_distance_m INTEGER,
    transfer_count INTEGER,
    summary_text TEXT,
    map_polyline TEXT,
    expires_at TIMESTAMP,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS route_steps (
    route_step_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    recommended_route_id UUID NOT NULL REFERENCES recommended_routes(recommended_route_id) ON DELETE CASCADE,
    step_order INTEGER NOT NULL,
    travel_mode TEXT,
    instruction_text TEXT,
    google_transit_line TEXT,
    from_station_id TEXT REFERENCES rail_stations(station_id) ON DELETE SET NULL,
    to_station_id TEXT REFERENCES rail_stations(station_id) ON DELETE SET NULL,
    start_geom geometry(Point, 4326),
    end_geom geometry(Point, 4326),
    path_geom geometry(LineString, 4326),
    duration_min INTEGER,
    walking_distance_m INTEGER,
    CONSTRAINT uq_route_steps_order UNIQUE (recommended_route_id, step_order)
);

CREATE TABLE IF NOT EXISTS route_accessibility_annotations (
    annotation_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    route_step_id UUID NOT NULL REFERENCES route_steps(route_step_id) ON DELETE CASCADE,
    target_type TEXT,
    target_id TEXT,
    annotation_type TEXT,
    accessibility_status TEXT NOT NULL DEFAULT 'unknown',
    confidence TEXT NOT NULL DEFAULT 'low',
    source_list JSONB NOT NULL DEFAULT '[]'::jsonb,
    message TEXT,
    distance_m INTEGER,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT chk_route_annotations_status CHECK (
        accessibility_status IN ('supported', 'not_supported', 'unknown')
    ),
    CONSTRAINT chk_route_annotations_confidence CHECK (
        confidence IN ('high', 'medium', 'low')
    )
);

CREATE TABLE IF NOT EXISTS searchable_locations (
    location_id TEXT PRIMARY KEY,
    location_type TEXT NOT NULL,
    source_id TEXT,
    display_name TEXT NOT NULL,
    geom geometry(Geometry, 4326),
    accessibility_status TEXT NOT NULL DEFAULT 'unknown',
    confidence TEXT NOT NULL DEFAULT 'low',
    CONSTRAINT chk_searchable_locations_status CHECK (
        accessibility_status IN ('supported', 'not_supported', 'unknown')
    ),
    CONSTRAINT chk_searchable_locations_confidence CHECK (
        confidence IN ('high', 'medium', 'low')
    )
);

CREATE TABLE IF NOT EXISTS ai_conversations (
    conversation_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    anonymous_user_id UUID REFERENCES anonymous_users(anonymous_user_id) ON DELETE SET NULL,
    entry_page TEXT,
    related_route_id UUID REFERENCES recommended_routes(recommended_route_id) ON DELETE SET NULL,
    related_station_id TEXT REFERENCES rail_stations(station_id) ON DELETE SET NULL,
    started_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    ended_at TIMESTAMP,
    status TEXT NOT NULL DEFAULT 'active',
    CONSTRAINT chk_ai_conversations_status CHECK (status IN ('active', 'closed', 'failed'))
);

CREATE TABLE IF NOT EXISTS ai_messages (
    message_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    conversation_id UUID NOT NULL REFERENCES ai_conversations(conversation_id) ON DELETE CASCADE,
    sender TEXT NOT NULL,
    message_text TEXT,
    detected_intent TEXT,
    scope_status TEXT,
    response_source TEXT,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT chk_ai_messages_sender CHECK (sender IN ('user', 'assistant', 'system')),
    CONSTRAINT chk_ai_messages_scope CHECK (
        scope_status IS NULL OR scope_status IN ('supported', 'out_of_scope', 'unclear', 'missing_data')
    ),
    CONSTRAINT chk_ai_messages_response_source CHECK (
        response_source IS NULL OR response_source IN ('database', 'google', 'static_help', 'mixed', 'fallback')
    )
);

CREATE INDEX IF NOT EXISTS idx_rail_routes_agency ON rail_routes (agency_id);
CREATE INDEX IF NOT EXISTS idx_rail_routes_source ON rail_routes (source_system);
CREATE INDEX IF NOT EXISTS idx_rail_stations_geom ON rail_stations USING GIST (geom);
CREATE INDEX IF NOT EXISTS idx_rail_stations_source ON rail_stations (source_system);
CREATE INDEX IF NOT EXISTS idx_rail_stations_name_trgm ON rail_stations USING GIN (station_name gin_trgm_ops);
CREATE INDEX IF NOT EXISTS idx_station_groups_geom ON station_groups USING GIST (geom);
CREATE INDEX IF NOT EXISTS idx_station_groups_name_trgm ON station_groups USING GIN (display_name gin_trgm_ops);
CREATE INDEX IF NOT EXISTS idx_station_group_members_station ON station_group_members (station_id);
CREATE INDEX IF NOT EXISTS idx_rail_station_routes_station ON rail_station_routes (station_id);
CREATE INDEX IF NOT EXISTS idx_rail_station_routes_route ON rail_station_routes (route_id, direction_id, stop_sequence);

CREATE INDEX IF NOT EXISTS idx_accessibility_points_geom ON accessibility_points USING GIST (geom);
CREATE INDEX IF NOT EXISTS idx_accessibility_points_type ON accessibility_points (feature_type, accessibility_type);

CREATE INDEX IF NOT EXISTS idx_station_accessibility_profiles_status
    ON station_accessibility_profiles (accessibility_status, confidence);

CREATE INDEX IF NOT EXISTS idx_recent_place_cache_geom ON recent_place_cache USING GIST (geom);
CREATE INDEX IF NOT EXISTS idx_recent_place_cache_user
    ON recent_place_cache (anonymous_user_id, place_role, last_used_at DESC);

CREATE INDEX IF NOT EXISTS idx_route_requests_user_created
    ON route_requests (anonymous_user_id, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_recommended_routes_request ON recommended_routes (route_request_id);
CREATE INDEX IF NOT EXISTS idx_recommended_routes_expires ON recommended_routes (expires_at);
CREATE INDEX IF NOT EXISTS idx_route_steps_route ON route_steps (recommended_route_id, step_order);
CREATE INDEX IF NOT EXISTS idx_route_steps_path_geom ON route_steps USING GIST (path_geom);
CREATE INDEX IF NOT EXISTS idx_route_annotations_step ON route_accessibility_annotations (route_step_id);

CREATE INDEX IF NOT EXISTS idx_searchable_locations_geom ON searchable_locations USING GIST (geom);
CREATE INDEX IF NOT EXISTS idx_searchable_locations_type ON searchable_locations (location_type);
CREATE INDEX IF NOT EXISTS idx_searchable_locations_name_trgm
    ON searchable_locations USING GIN (display_name gin_trgm_ops);

CREATE INDEX IF NOT EXISTS idx_ai_conversations_user ON ai_conversations (anonymous_user_id, started_at DESC);
CREATE INDEX IF NOT EXISTS idx_ai_messages_conversation ON ai_messages (conversation_id, created_at);
