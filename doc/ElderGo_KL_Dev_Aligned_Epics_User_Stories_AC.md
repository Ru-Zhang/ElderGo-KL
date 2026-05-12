# ElderGo KL Dev-Aligned Epics, User Stories, and Acceptance Criteria

## Dev Alignment Notes

This document revises the current Analysis and Design epics, user stories, and acceptance criteria so they align with the current `dev` branch implementation. The existing nine-epic structure is preserved, but unsupported or not-yet-wired behavior has been corrected.

Major corrections:

- Route input uses typed origin and destination fields with Google place suggestions. There is no current-location button in the current implementation.
- Station detail displays routes, accessibility status, known facilities, data source, station imagery, and a Google Maps "More Details" action. It does not display ticket counter or operating hours fields.
- Route saving is implemented as a downloadable PNG image generated in the browser, not as full offline route storage.
- Weather is advisory on the route result page and does not automatically replace or recalculate the route.
- The frontend AI assistant is currently a local chat sheet with quick questions and local replies. Backend AI guardrail endpoints exist, but the frontend sheet is not wired to them.
- Help and guide pages are static in-app content. The current concession guide does not implement image enlargement.

---

# Epics & User Stories

## EPIC 01 | Global Age-Friendly Navigation and Visual Adaptation System

**Description:**  
This epic covers the app-wide interaction layer that helps elderly users read, understand, and move between major functions. It includes the global top bar, font-size switching, English/Bahasa Melayu language switching, and persistent bottom navigation across the main app pages.

**Purpose:**  
The purpose of this epic is to reduce visual and navigation barriers before users interact with route planning, station search, help content, or preferences.

### US1.1 - One-Tap Switching Between Fixed Large-Text Modes

**As** an elderly user with weaker eyesight,  
**I want** to switch text size with one tap,  
**so that** I can read route, station, help, and preference information more comfortably.

**AC1.1.1: Cycle from standard to large text**  
Given the app is using the `standard` font-size mode  
When the user taps the font-size button in the top bar  
Then the app changes the global font-size mode to `large` and enlarges supported page content without navigating away.

**AC1.1.2: Cycle from large to extra-large text**  
Given the app is using the `large` font-size mode  
When the user taps the font-size button again  
Then the app changes the global font-size mode to `extra_large` and applies the larger display to supported headings, body text, inputs, buttons, and route details.

**AC1.1.3: Cycle from extra-large back to standard text**  
Given the app is using the `extra_large` font-size mode  
When the user taps the font-size button again  
Then the app returns to `standard` font-size mode without opening a modal or resetting the current page.

**AC1.1.4: Persist font-size settings locally and remotely when possible**  
Given the user changes the font-size mode  
When the app can access local browser storage  
Then the selected font-size mode is stored in `localStorage`; and when an anonymous user ID is available, the setting is also sent to `/users/{anonymous_user_id}/ui-settings`.

### US1.2 - One-Tap Switching Between English and Bahasa Melayu Interfaces

**As** an elderly user who is more comfortable in a specific language,  
**I want** to switch between English and Bahasa Melayu,  
**so that** I can understand available labels, prompts, and guide content.

**AC1.2.1: Toggle between EN and BM**  
Given the app is currently displayed in `EN` or `BM`  
When the user taps the language button in the top bar  
Then the app toggles the language value between `EN` and `BM` and re-renders translated UI text where translation keys exist.

**AC1.2.2: Preserve active page state during language switching**  
Given the user is on a page with current app state such as selected origin, selected destination, route, station, or preferences  
When the language is switched  
Then the app changes the displayed language without forcing navigation to another page.

**AC1.2.3: Persist language settings locally and remotely when possible**  
Given the user changes the language  
When local storage is available  
Then the selected language is stored in `localStorage`; and when an anonymous user ID is available, the setting is also sent to `/users/{anonymous_user_id}/ui-settings`.

### US1.3 - Persistent Global Bottom Navigation

**As** an elderly user who may get lost between pages,  
**I want** bottom navigation to remain available,  
**so that** I can quickly return to a core function.

**AC1.3.1: Navigate to core modules from supported pages**  
Given the user is on a supported app page  
When the user taps Planning, Stations, Preference, Help, or the central AI button in the bottom navigation  
Then the app opens the selected module or AI sheet using the current single-page app navigation.

**AC1.3.2: Show active module state**  
Given the user is viewing Planning, Stations, Preference, or Help content  
When the bottom navigation is visible  
Then the corresponding module icon and label are visually highlighted as active.

---

## EPIC 02 | Personalized Travel Preference Configuration System

**Description:**  
This epic supports simple travel preferences that influence route recommendation: Accessibility First, Least Walk, and Fewest Transfers. Preferences can be set from a first-use modal or the Preference page and are cached locally, with backend persistence when an anonymous user is available.

**Purpose:**  
The purpose of this epic is to let users express mobility-related priorities once and have the route recommendation logic use those priorities later.

### US2.1 - First-Time Preference Setup Guidance

**As** an elderly user who is not familiar with settings,  
**I want** a simple preference prompt when I first start planning,  
**so that** I can set route priorities without searching for the settings page.

**AC2.1.1: Show preference modal before first planning interaction**  
Given onboarding is not completed and no travel preference is enabled  
When the user first clicks an origin or destination input on the Planning page  
Then the app opens the preference modal with the three editable preference switches.

**AC2.1.2: Save preferences from the modal**  
Given the preference modal is open  
When the user changes any preference and taps Save  
Then the app saves the selected preferences, marks onboarding as completed, shows a saved hint, closes the modal after a short delay, and keeps the Planning page usable.

**AC2.1.3: Close modal without blocking route planning**  
Given the preference modal is open  
When the user closes it without saving  
Then the modal closes and the user can continue entering origin and destination in default preference mode.

### US2.2 - Preference Saving and Continued Effectiveness

**As** an elderly user with recurring travel needs,  
**I want** my travel preferences to be remembered,  
**so that** future route searches use the same priorities.

**AC2.2.1: Store preferences locally**  
Given the user saves preferences from the modal or Preference page  
When browser storage is available  
Then the app stores the values under the local ElderGo preference key.

**AC2.2.2: Restore preferences on app load**  
Given saved local preferences exist  
When the app starts before remote settings are restored  
Then the app initializes preference state from local storage.

**AC2.2.3: Sync preferences with backend when an anonymous user exists**  
Given the app has resolved an anonymous user ID through `/users/anonymous`  
When preferences are saved  
Then the frontend sends the preferences to `/users/{anonymous_user_id}/travel-preferences`.

**AC2.2.4: Continue working when remote restore fails**  
Given the backend restore request for settings or preferences fails  
When the app loads  
Then the app continues using local defaults or local cached values instead of blocking the interface.

### US2.3 - Preference Modification Entry

**As** an elderly user whose needs may change,  
**I want** to modify my preferences later,  
**so that** route recommendations continue to match my current needs.

**AC2.3.1: Open preference settings from bottom navigation**  
Given the user is on a supported page  
When the user taps Preference in the bottom navigation  
Then the app opens the Preference page and displays the three preference switches.

**AC2.3.2: Save changed preferences from the Preference page**  
Given the user changes one or more preference switches  
When the user taps Save  
Then the app updates global preference state, persists it locally, attempts backend sync when possible, and shows a saved hint.

**AC2.3.3: Cancel unsaved preference changes**  
Given the user has changed switches on the Preference page but has not saved  
When the user taps Cancel  
Then the local page switches return to the currently saved preference values.

---

## EPIC 03 | Route Planning Input and Time Selection System

**Description:**  
This epic covers the route-planning entry flow: entering origin and destination, selecting valid Google place suggestions, validating input, and choosing a travel time label before route recommendation starts.

**Purpose:**  
The purpose of this epic is to keep the planning process simple and explicit, while ensuring the backend receives enough structured data to request and score candidate routes.

### US3.1 - Simplified Origin and Destination Input

**As** an elderly user who may not remember full place names,  
**I want** the app to suggest places while I type,  
**so that** I can select a valid origin and destination more easily.

**AC3.1.1: Display Google place suggestions while typing**  
Given the user is on the Planning page  
When the user types into the origin or destination input  
Then the frontend calls the Google place suggestion service and displays returned suggestions in a tappable dropdown.

**AC3.1.2: Store selected suggestion as the route point**  
Given place suggestions are visible  
When the user taps a suggestion  
Then the app stores the selected place object, including display name and available coordinates/place ID, for route planning.

**AC3.1.3: Block search when input is missing**  
Given the origin field, destination field, or both fields are empty  
When the user attempts to search  
Then the app shows a clear validation message and does not navigate to the time-selection page.

**AC3.1.4: Block search when text was typed but no suggestion was selected**  
Given the user typed text in an input but did not select a recognized suggestion  
When the user attempts to search  
Then the app shows an invalid origin or destination message and remains on the Planning page.

**AC3.1.5: Show service-unavailable feedback for place lookup errors**  
Given Google place suggestions cannot be loaded  
When the user types into a route input  
Then the app shows an unavailable message and prevents invalid unconfirmed place text from being used as a route point.

### US3.2 - Select Travel Time After Search

**As** an elderly user who wants to choose when to travel,  
**I want** to select a simple time option before route calculation,  
**so that** the route request includes my intended travel time.

**AC3.2.1: Navigate to time selection after valid place input**  
Given both origin and destination have been selected from valid suggestions  
When the user taps Search  
Then the app stores the selected route points and opens the Plan Your Time page.

**AC3.2.2: Provide four time labels**  
Given the Plan Your Time page is open  
When the user views the available choices  
Then the page displays Now, Morning, Afternoon, and Evening options with icons and short descriptions.

**AC3.2.3: Submit route recommendation request after time selection**  
Given the user has selected a time option  
When the user taps Show Route  
Then the frontend sends origin, destination, departure time, anonymous user ID when available, and current preferences to `/routes/recommend`.

**AC3.2.4: Return to Planning when required route points are missing**  
Given the Plan Your Time page is opened without stored origin or destination  
When the user attempts to show a route  
Then the app records a route error and navigates back to the Planning page.

---

## EPIC 04 | Single-Route Recommendation and Rule-Based Scoring System

**Description:**  
This epic covers the backend route recommendation behavior. The backend requests Google Maps transit candidates, scores them using ElderGo priorities, and returns one recommended route with summary, steps, and accessibility annotations.

**Purpose:**  
The purpose of this epic is to reduce decision burden by selecting one route for the user instead of asking them to compare multiple candidate routes.

### US4.1 - Output Only One Optimal Route

**As** an elderly user who may be overwhelmed by many route choices,  
**I want** the system to return one recommended route,  
**so that** I can focus on understanding the journey.

**AC4.1.1: Return one RecommendedRoute object**  
Given `/routes/recommend` receives a valid route recommendation request  
When Google Maps returns usable transit candidates  
Then the backend selects one candidate and returns a single `RecommendedRoute` response.

**AC4.1.2: Include route summary fields**  
Given a route is recommended  
When the response is returned  
Then it includes route ID, origin name, destination name, total duration, transfer count, total walking distance, recommendation reason, optional map polyline, and ordered steps.

**AC4.1.3: Surface an error when no usable candidate exists**  
Given Google Maps returns no usable candidate routes  
When the backend attempts to recommend a route  
Then the route service raises an error instead of returning a misleading empty recommendation.

### US4.2 - Preferences and Time Participate in Route Selection

**As** an elderly user with specific mobility preferences,  
**I want** my saved preferences and selected time to be used during route recommendation,  
**so that** the returned route better reflects my needs.

**AC4.2.1: Use preference flags in scoring**  
Given a route request includes `accessibility_first`, `least_walk`, and `fewest_transfers` values  
When candidate routes are scored  
Then the scoring logic applies the selected priorities before returning the best candidate.

**AC4.2.2: Prioritize walking and transfers for accessibility-first mode**  
Given `accessibility_first` is enabled  
When candidate routes are compared  
Then the route scoring logic prioritizes lower walking distance and fewer transfers before using the weighted score as a tie-breaker.

**AC4.2.3: Pass departure time to Google Maps route lookup**  
Given the frontend submits a departure time label  
When the backend fetches route candidates  
Then the selected departure time is passed into the route-candidate lookup flow.

**AC4.2.4: Persist route recommendations when database is available**  
Given demo mode is off and the database is available  
When a route is recommended  
Then the backend persists the route request, recommended route, steps, and accessibility annotations; otherwise it returns an ephemeral route ID while keeping route planning usable.

---

## EPIC 05 | Route Result Visualization, Weather, Saving, and Sharing System

**Description:**  
This epic covers how a recommended route is shown and reused after generation. The current implementation provides text and map views, route summary, step cards, accessibility messages, weather advice, downloadable PNG saving, WhatsApp sharing, and copy-link sharing.

**Purpose:**  
The purpose of this epic is to help elderly users understand the route, prepare for weather and accessibility uncertainty, and share or save the journey in a practical way.

### US5.1 - Switch Between Text View and Map View

**As** an elderly user who may prefer text over maps,  
**I want** to switch between route text and map view,  
**so that** I can use whichever format is easier for me.

**AC5.1.1: Open route result in text view by default**  
Given a route has been successfully generated  
When the Route Result page opens  
Then the app shows Text View as the default result mode.

**AC5.1.2: Switch route display without changing the selected route**  
Given the route result page is open  
When the user switches between Text View and Map View  
Then the app changes the display mode while keeping the same current route in state.

**AC5.1.3: Display Google Maps embed when route data exists**  
Given a current route exists  
When the user selects Map View  
Then the app displays a Google Maps directions embed using the route origin and destination.

**AC5.1.4: Show empty map fallback when no route exists**  
Given no route is currently selected  
When the user opens Map View  
Then the page displays a non-route fallback instead of crashing.

### US5.2 - View Route Summary and Step-by-Step Information

**As** an elderly user who needs clear travel instructions,  
**I want** a summary and step-by-step route cards,  
**so that** I can understand the journey before leaving.

**AC5.2.1: Show summary information**  
Given the Route Result page has a current route  
When the route summary renders  
Then it displays origin, destination, total time, transfers, and total walking distance.

**AC5.2.2: Show ordered route step cards**  
Given the current route includes ordered steps  
When Text View is active  
Then each step is shown with step number, localized instruction, duration, walking distance when applicable, mode icon, and accessibility message.

**AC5.2.3: Navigate between step cards**  
Given more than one route step exists  
When the user taps the left or right step controls  
Then the step carousel moves to the previous or next step without leaving the result page.

**AC5.2.4: Provide a no-route recovery state**  
Given the route result page opens without a current route  
When the page renders  
Then it shows a message and a Plan Route button that returns the user to Planning.

### US5.3 - Transparent Display of Accessibility and Weather Information

**As** an elderly user who needs to judge route suitability,  
**I want** accessibility and weather information to be visible,  
**so that** I can prepare for uncertainty before travel.

**AC5.3.1: Show accessibility messages per step**  
Given each route step contains an accessibility annotation  
When the step card renders  
Then the annotation message is displayed clearly on that step.

**AC5.3.2: Label unknown accessibility instead of assuming support**  
Given a route step annotation is unknown or not verified  
When the route result is displayed  
Then the app displays an unknown or fallback accessibility message instead of claiming verified support.

**AC5.3.3: Load destination weather advice**  
Given a current route and destination are available  
When the result page loads  
Then the frontend requests destination weather using destination name/coordinates and departure time.

**AC5.3.4: Display weather as advisory information only**  
Given weather data is ready, loading, or unavailable  
When the route result page renders  
Then the page shows senior-friendly weather guidance without automatically replacing the route.

### US5.4 - Save Route as an Image

**As** an elderly user who may need to view the route later,  
**I want** to save a route image,  
**so that** I can keep the key route instructions on my device.

**AC5.4.1: Generate downloadable PNG from current route**  
Given a current route exists and Text View has route steps  
When the user taps the save button  
Then the browser generates a PNG image containing the route summary and step-by-step instructions.

**AC5.4.2: Preserve current page after saving**  
Given route image generation succeeds  
When the download action is triggered  
Then the user remains on the Route Result page and the current route state is preserved.

**AC5.4.3: Show save failure hint**  
Given the route image cannot be generated or no route exists  
When the user taps the save button  
Then the app shows a user-facing hint and does not crash or clear the route.

### US5.5 - Family Safety Sharing

**As** an elderly user or family member,  
**I want** to share the current route,  
**so that** family can see the planned journey.

**AC5.5.1: Open sharing options for the current route**  
Given a current route exists  
When the user taps the share button  
Then the app opens a small share menu with WhatsApp and copy-link actions.

**AC5.5.2: Share through WhatsApp**  
Given the share menu is open  
When the user chooses WhatsApp  
Then the app opens a WhatsApp share URL containing a Google Maps directions link for the current origin and destination.

**AC5.5.3: Copy route link**  
Given the share menu is open  
When the user chooses copy link  
Then the app copies the Google Maps directions link to the clipboard and shows a success hint when copying succeeds.

**AC5.5.4: Keep route visible when sharing fails**  
Given clipboard access or sharing cannot complete  
When the share action fails  
Then the app shows a failure hint while keeping the route visible.

---

## EPIC 06 | Station Information Search and Discovery System

**Description:**  
This epic provides station search and detail discovery. The current implementation includes popular station loading, keyword search, duplicate station cleanup, station detail lookup, accessibility labels, known facilities, routes, source information, station imagery, and a Google Maps "More Details" action.

**Purpose:**  
The purpose of this epic is to help users check station suitability before travel without needing to interpret a complex map.

### US6.1 - Popular Station Recommendations and Search

**As** an elderly user who may not remember the exact station name,  
**I want** popular stations and keyword search,  
**so that** I can find station information quickly.

**AC6.1.1: Load popular stations**  
Given the user opens the Stations page  
When the page loads successfully  
Then the frontend requests `/locations/popular` and displays returned stations as tappable cards.

**AC6.1.2: Deduplicate station variants**  
Given popular or search results contain duplicate station names such as spacing variants or `REDONE` variants  
When the results are displayed  
Then the frontend and backend deduplication rules prevent duplicate station cards from appearing.

**AC6.1.3: Search locations by keyword**  
Given the user enters text in the station search box  
When the query is not blank  
Then the frontend requests `/locations/search?q={query}` and displays matching results.

**AC6.1.4: Show no-result or unavailable feedback**  
Given search returns no results or the station database request fails  
When the Stations page processes the response  
Then the page displays a clear no-results or data-unavailable message.

**AC6.1.5: Open station details from a result card**  
Given a station card is visible  
When the user taps the card  
Then the frontend fetches `/locations/{location_id}`, stores the selected station, and opens the Station Detail page.

### US6.2 - View Station Detail Information

**As** an elderly user checking a station before travel,  
**I want** clear station detail information,  
**so that** I can judge whether the station is suitable for me.

**AC6.2.1: Display implemented station detail fields**  
Given a selected station exists  
When the Station Detail page renders  
Then it displays station name, served routes, accessibility status, known facilities, and data source list.

**AC6.2.2: Show placeholders for unverified detail fields**  
Given routes, known facilities, or source data are unavailable  
When the Station Detail page renders  
Then it displays the app's not-yet-verified text rather than leaving the field blank.

**AC6.2.3: Show station image or fallback**  
Given station name and coordinates are available  
When the Station Detail page renders  
Then it uses the Google static image URL for the station; otherwise it uses the default ElderGo background image.

**AC6.2.4: Open Google Maps more details**  
Given a selected station exists  
When the user taps More Details  
Then the app looks up Google place details and opens a Google Maps search URL in a new browser tab.

**AC6.2.5: Provide recovery when no station is selected**  
Given the Station Detail page opens without a selected station  
When the page renders  
Then it shows a station-not-found message and a button back to Stations.

---

## EPIC 07 | Help and Senior Fare Benefit Information System

**Description:**  
This epic provides static in-app help content for app usage, ticket purchase guidance, concession benefits, privacy information, and troubleshooting through app reset.

**Purpose:**  
The purpose of this epic is to give elderly users and caregivers a simple place to learn how to use ElderGo KL and prepare for public transport travel.

### US7.1 - View Ticket Guide

**As** an elderly user who is unfamiliar with ticket purchasing,  
**I want** a clear ticket guide,  
**so that** I can prepare for train travel.

**AC7.1.1: Open Ticket Guide from Help**  
Given the user is on the Help page  
When the user taps the ticket guide card  
Then the app opens the Ticket Guide page.

**AC7.1.2: Present ticket options as readable content**  
Given the Ticket Guide page is open  
When the user reads the content  
Then the page shows token purchase steps and Touch 'n Go guidance in a vertical reading layout.

**AC7.1.3: Link to official source**  
Given the Ticket Guide page is open  
When the user reaches the information source section  
Then the page provides a link to the MyRapid website.

### US7.2 - View Concession Guide

**As** a senior user seeking fare benefits,  
**I want** a concession guide,  
**so that** I understand the available discount and application flow.

**AC7.2.1: Open Concession Guide from Help**  
Given the user is on the Help page  
When the user taps the concession guide card  
Then the app opens the Concession Guide page.

**AC7.2.2: Show benefit and required document**  
Given the Concession Guide page is open  
When the user views the top content  
Then the page shows the senior concession benefit and the MyKad preparation requirement.

**AC7.2.3: Show application steps in order**  
Given the Concession Guide page is open  
When the user reads the guide  
Then the page displays the concession process as ordered step cards ending with card collection.

### US7.3 - View Privacy Information

**As** a user who cares about data use,  
**I want** privacy information in the app,  
**so that** I understand the app's basic privacy approach.

**AC7.3.1: Open Privacy Info from Help**  
Given the user is on the Help page  
When the user taps the privacy card  
Then the app opens the Privacy Info page.

**AC7.3.2: Display privacy promises**  
Given the Privacy Info page is open  
When the user reads the content  
Then the page presents the privacy promise, no-location-tracking message, no-history message, no-ads message, and footer explanation.

**AC7.3.3: Respect current app language where translations exist**  
Given the app language is `EN` or `BM`  
When the user opens Privacy Info  
Then the page displays privacy text through the translation system.

### US7.4 - Reset App Data from Help

**As** a user troubleshooting the app,  
**I want** a reset option,  
**so that** I can clear cached ElderGo state if the app behaves unexpectedly.

**AC7.4.1: Show reset action on Help page**  
Given the Help page is open  
When the user views the app issues section  
Then the page displays a clear cache/reset button and warning text.

**AC7.4.2: Confirm before clearing local data**  
Given the user taps the reset button  
When the browser confirmation is shown  
Then local ElderGo keys are removed only if the user confirms.

**AC7.4.3: Reload after reset**  
Given the user confirms reset  
When local ElderGo keys and session storage are cleared  
Then the app shows a success alert and reloads the page.

---

## EPIC 08 | Controlled Conversational AI Travel Assistant System

**Description:**  
This epic covers the AI assistant entry and the current implemented chat behavior. The frontend currently provides a manually opened chat sheet with quick questions and local placeholder replies. The backend includes endpoints for AI conversations and guarded messages, but the frontend sheet is not currently wired to those endpoints.

**Purpose:**  
The purpose of this epic is to provide a low-barrier help entry while clearly limiting the current implementation to local assistant UI behavior and backend guardrail readiness.

### US8.1 - Manually Open the AI Assistant

**As** an elderly user who wants quick help,  
**I want** to open the assistant from the bottom navigation,  
**so that** I can ask or choose a simple question.

**AC8.1.1: Open chat sheet from bottom navigation**  
Given the user is on a supported page with bottom navigation  
When the user taps the central AI button  
Then the app opens the AI chatbot sheet over the current page.

**AC8.1.2: Close chat sheet without leaving the current page**  
Given the AI chatbot sheet is open  
When the user taps outside the sheet or closes it  
Then the sheet is dismissed and the underlying page remains selected.

**AC8.1.3: Show quick question entries on first open**  
Given the AI chatbot sheet opens with no messages  
When the sheet content is displayed  
Then it shows quick question buttons for hospital, rain, and station staff topics.

### US8.2 - Ask Travel Questions Within Current Frontend Assistant

**As** a user who prefers typing a question,  
**I want** to enter a message in the assistant sheet,  
**so that** I receive a simple local reply in the current prototype.

**AC8.2.1: Send typed message locally**  
Given the AI chatbot sheet is open and the input contains text  
When the user sends the message  
Then the sheet appends the user message and a local assistant reply, then clears the input.

**AC8.2.2: Use quick question buttons**  
Given no chat messages are currently displayed  
When the user taps a quick question  
Then the sheet displays the selected question as a user message and a local assistant reply.

**AC8.2.3: Do not call backend AI from the current sheet**  
Given the current frontend implementation  
When a message is sent from the AI chatbot sheet  
Then the response is generated locally by the component and no frontend call is made to `aiApi.ts`.

### US8.3 - Backend Guardrail Readiness

**As** a project team member,  
**I want** backend AI guardrail endpoints available,  
**so that** future frontend integration can restrict assistant answers to ElderGo topics.

**AC8.3.1: Create backend conversation ID**  
Given a client calls `POST /ai/conversations`  
When the request succeeds  
Then the backend returns a generated conversation ID.

**AC8.3.2: Reject out-of-scope backend messages**  
Given a client sends an out-of-scope message to `/ai/conversations/{conversation_id}/messages`  
When the guardrail service marks it out of scope  
Then the backend returns `in_scope: false` and a response explaining the supported ElderGo KL topics.

**AC8.3.3: Return guarded placeholder for in-scope backend messages**  
Given a client sends an in-scope message to the backend AI message endpoint  
When the guardrail service accepts it  
Then the backend returns `in_scope: true` and a bounded placeholder answer that avoids claiming unverified live data.

---

## EPIC 09 | First-Time Onboarding and Low-Barrier Getting Started

**Description:**  
This epic covers the current onboarding and guidance behavior: a first-use preference modal triggered from Planning, and a Help-accessible Use ElderGo guide with example flow cards and navigation actions.

**Purpose:**  
The purpose of this epic is to help first-time users understand the app's main flow without adding a separate mandatory onboarding page.

### US9.1 - First-Time Preference Onboarding

**As** a first-time user,  
**I want** the app to guide me into setting simple preferences,  
**so that** my first route search can reflect my mobility needs.

**AC9.1.1: Detect incomplete onboarding from settings state**  
Given `onboardingCompleted` is false and all preference switches are disabled  
When the user enters Planning and first clicks a route input  
Then the app treats the user as eligible for the first-time preference prompt.

**AC9.1.2: Mark onboarding complete after saving modal preferences**  
Given the first-time preference modal is open  
When the user taps Save  
Then the app saves preferences and sets `onboardingCompleted` to true in UI settings.

**AC9.1.3: Persist onboarding setting locally and remotely when possible**  
Given onboarding is marked completed  
When local storage is available  
Then the app saves the UI setting locally; and when an anonymous user ID exists, it sends the setting to `/users/{anonymous_user_id}/ui-settings`.

### US9.2 - Explain Key Functions and Example Inputs

**As** a new user or caregiver,  
**I want** a simple guide explaining ElderGo's main functions,  
**so that** I can learn how to start using the app.

**AC9.2.1: Open Use ElderGo guide from Planning or Help**  
Given the user is on Planning or Help  
When the user chooses the Use ElderGo guide entry  
Then the app opens the Use ElderGo page.

**AC9.2.2: Explain the main app flow in cards**  
Given the Use ElderGo page is open  
When the user reads the content  
Then the page explains preference setup, route planning, help use, and station information with large cards and icons.

**AC9.2.3: Provide direct actions from the guide**  
Given the Use ElderGo guide is open  
When the user taps the guide action buttons  
Then the app can navigate to Preference, Planning, or Stations from the relevant guide sections.

**AC9.2.4: Keep guide content within normal app navigation**  
Given the user is reading the Use ElderGo page  
When the user uses the top back button or bottom navigation  
Then the app returns to Help or switches to the chosen core module without leaving the single-page app.

