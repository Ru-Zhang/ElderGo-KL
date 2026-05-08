# Data Management Plan Report

## 1. Document Control

| Item | Details |
|---|---|
| Project name | ElderGo KL |
| Team name | Team 01 |
| Iteration | Iteration 2 |
| Document type | Live Data Management Plan Report |
| Last updated date | 29 April 2026 |
| Prepared by | Team 01 |

### Version History

| Version | Date | Description | Author |
|---|---|---|---|
| 1.0 | 29 April 2026 | Formal Iteration 2 Data Management Plan Report. | Team 01 |
| 1.1 | 29 April 2026 | Condensed version with merged sections and embedded figures. | Team 01 |

## 2. Purpose and Product Overview

This Data Management Plan explains how ElderGo KL manages data during Iteration 2. It supports the FIT5120 Project Governance Portfolio by documenting the main data sources, data flow, storage approach, database model, privacy risks, quality limitations, and future data management work.

ElderGo KL is a senior-friendly public transport navigation product for Kuala Lumpur and the Klang Valley. It is designed for older users who may need simpler route guidance, clearer information presentation, fewer decision points, and more accessible travel support.

Data supports the product by enabling public transport route planning, rail station search, accessibility-aware route information, weather-informed travel advice, station detail pages, and anonymous preference storage. The Iteration 2 architecture combines official GTFS transport data, OpenStreetMap-derived accessibility data, Google Maps and Places services, Google Static Map/image services, OpenWeather forecast data, and anonymous user interaction data. The operational database is deployed using Google Cloud SQL with PostgreSQL/PostGIS.

![Figure 1. System architecture](Figure1.png)

## 3. Data Sources and Product Use

| Data source | Access method | Update frequency | Main use in ElderGo KL |
|---|---|---|---|
| KTMB GTFS static data | CSV / GTFS static feed from Malaysia GTFS Static API | Daily at 00:01:00 | Supports KTMB routes, stations, service relationships, and route planning data. |
| Prasarana / Rapid Rail GTFS static data | CSV / GTFS static feed from Malaysia GTFS Static API | As required | Supports Rapid Rail routes, stations, frequencies, shapes, and service relationships. |
| Klang Valley wheelchair accessibility data | Manual OpenStreetMap collection/export | Updated when new accessibility evidence is collected | Supports station accessibility information, nearby facilities, and accessibility route annotations. |
| Google Maps Directions / Transit data | API / JSON | Per user route request | Generates live public transport route options, steps, travel modes, durations, distances, and transit stop references. |
| Google Places data | API / JSON | Per place search or station detail request | Supports place search, station details, addresses, ratings, coordinates, and opening information where available. |
| Google Static Map / station image data | API / image response | Per station or place detail request | Supports station detail pages and gives users visual location context. |
| OpenWeather forecast data | API / JSON | Per weather forecast request | Provides weather prediction, rain/heat/wind indicators, and senior-friendly travel advice. |
| Anonymous user preference and interaction data | Application database records | Per user action, with regular cleanup every 7 days | Stores UI settings, travel preferences, recent places, route requests, and recommended route records without requiring named accounts. |

In Iteration 1, the project mainly used Google APIs and cache tables for user-related data. Iteration 2 expands this by connecting official GTFS datasets, prepared accessibility data, a deployed PostgreSQL/PostGIS database, and a clearer transport/accessibility data model.

## 4. Data Processing, Cleaning and Storage Workflow

The Iteration 2 data workflow is:

1. Collect data from official GTFS feeds, OpenStreetMap accessibility exports, external APIs, and anonymous user interactions.
2. Prepare transport and accessibility data into cleaned project datasets, including station, route, service, coordinate, and accessibility fields.
3. Transform cleaned data into database-ready transport, accessibility, route, weather, and user preference entities.
4. Store operational data in Google Cloud SQL PostgreSQL/PostGIS, with PostGIS supporting spatial station, route, and accessibility queries.
5. Request runtime API data when users search places, view station details, plan routes, or check weather.
6. Combine route, station, weather, and accessibility data to support recommendations and user-facing travel guidance.
7. Archive older raw, cleaned, and database-ready data versions by iteration.

Key cleaning and transformation activities include standardising station names, preparing coordinates, linking stations with routes, filtering accessibility features, converting geographic data into spatial records, and converting API route responses into route requests, recommended routes, route steps, and annotations. Missing accessibility information is treated as `unknown`, not as evidence that a station or facility is unsupported.

ElderGo KL uses three storage layers: raw KTMB/Rapid Rail/accessibility data, cleaned output data for import, and the deployed Google Cloud SQL PostgreSQL/PostGIS operational database. Anonymous user data is stored for operational use and cleaned regularly every seven days.

## 5. Data Model and Database Structure

The current database model uses PostgreSQL/PostGIS on Google Cloud SQL. PostgreSQL stores structured relational data, while PostGIS supports spatial data such as station coordinates, route geometry, accessibility points, and location-based matching.

Figure 2 shows the transport and rail data model.

![Figure 2. Transport and rail ER diagram](figure2.png)

Figure 3 shows the accessibility and searchable location data model.

![Figure 3. Accessibility and searchable location ER diagram](figure3.png)

Figure 4 shows the route planning and route annotation data model.

![Figure 4. Route planning and route annotation ER diagram](figure4.png)

Figure 5 shows the anonymous user, preference, cache, and interaction data model.

![Figure 5. Anonymous user and preference ER diagram](figure5.png)

The main entity groups are:

| Entity group | Main entities | Relationship summary |
|---|---|---|
| Transport network | Rail operators, routes, stations, calendars, trips, stop times | Operators provide routes; routes contain stations; trips and stop times describe service movement. |
| Accessibility information | Accessibility points, station accessibility summaries, searchable locations | Accessibility points and station summaries support accessibility search and route annotation. |
| Route planning | Route requests, recommended routes, route steps, route annotations | A route request produces a recommended route; route steps can receive accessibility annotations. |
| User preference and cache | Anonymous users, UI settings, travel preferences, recent places | Anonymous users can store settings, accessibility preferences, walking/transfer preferences, and recent places. |
| Future support entities | AI conversation and message records, if used later | Reserved for future interaction support and not treated as core Iteration 2 AI model evidence. |

## 6. Ethical, Privacy and Bias Considerations

ElderGo KL does not require named user accounts in Iteration 2. However, anonymous device-level records, route requests, recent places, and travel preferences are still privacy-relevant because they may reveal movement patterns or accessibility needs. The current retention approach is regular cleanup every seven days.

The product also relies on third-party services. Route, place, map/image, and weather requests may disclose location-related queries to service providers. The team should therefore keep data collection limited to operational needs and avoid storing unnecessary personal or location history.

Accessibility information requires careful presentation because older users may rely on it for mobility and safety decisions. Missing accessibility data must remain visible as `unknown`, not be converted into unsupported or safe assumptions. This is especially important because the current accessibility dataset is incomplete and based on OpenStreetMap manual collection/export.

The project does not need to claim a production AI model for Iteration 2 route decision-making. The main fairness and bias risks come from uneven data coverage, route APIs that may prioritise speed over accessibility, and incomplete accessibility mapping across different stations or neighbourhoods. Risk reduction actions include preserving source confidence, expanding accessibility data in Iteration 3, testing with older-user scenarios, and explaining when information is based on official data, OpenStreetMap data, API data, or missing data.

## 7. Data Quality and Limitations

| Quality dimension | Current consideration |
|---|---|
| Completeness | GTFS rail data is structured, but accessibility data remains incomplete because official accessibility datasets are not available. |
| Accuracy | Official GTFS data is expected to be more reliable than manually collected accessibility data, but all datasets still require validation and source-date tracking. |
| Consistency | Data preparation should maintain consistent station identifiers, route relationships, accessibility statuses, and geographic coordinates. |
| Timeliness | KTMB GTFS updates daily at 00:01:00, while Prasarana / Rapid Rail updates as required. Project refreshes should occur when source data changes or new evidence is collected. |
| Relevance | The current datasets are relevant to route planning, station search, accessibility information, weather advice, and senior-friendly travel support. |
| Limitations | External APIs may be incomplete or delayed, and missing accessibility data should not be treated as a confirmed lack of accessibility support. |

## 8. Iteration 2 Updates and Future Plan

Iteration 2 expands the project data foundation beyond Iteration 1. Iteration 1 mainly used Google APIs and cache tables for user data. Iteration 2 introduces official KTMB GTFS static data, official Prasarana / Rapid Rail GTFS static data, manually exported OpenStreetMap accessibility data, cleaned transport and accessibility data outputs, Google Cloud SQL PostgreSQL/PostGIS deployment, database ER diagrams, and regular anonymous user data cleanup.

Iteration 3 should extend station detail and accessibility data. Planned future improvements include operating hours, peak-hour information, station maps, ticket fare information, and additional accessibility-related data sources. These items are planned future work and should not be presented as completed Iteration 2 functionality.

Further data management improvements should include clearer data refresh schedules, validation records for cleaned datasets and database imports, stronger accessibility confidence evidence, documentation of the seven-day user data cleanup process, and updates to Figures 1 to 5 when the architecture or database model changes.

## 9. References

- Malaysia GTFS Static API, Data.gov.my: https://developer.data.gov.my/realtime-api/gtfs-static
- OpenStreetMap Official Copyright Page: https://www.openstreetmap.org/copyright
- Google Maps Platform Directions API Documentation: https://developers.google.com/maps/documentation/directions
- Google Places API Documentation: https://developers.google.com/maps/documentation/places/web-service/overview
- Google Maps Static API Documentation: https://developers.google.com/maps/documentation/maps-static
- Google Cloud SQL for PostgreSQL Documentation: https://cloud.google.com/sql/docs/postgres
- PostgreSQL Documentation: https://www.postgresql.org/docs/
- PostGIS Documentation: https://postgis.net/documentation/
- OpenWeather API Documentation: https://openweathermap.org/api
