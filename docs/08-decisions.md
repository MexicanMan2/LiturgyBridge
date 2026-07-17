# Project Decisions

## Overview

This document records important decisions about the direction, principles, and architecture of LiturgyBridge.

Decisions are documented to preserve the reasoning behind the project and help future contributors understand the intended direction.

---

# Decision 001 - Project Name

## Decision

The project name is:

LiturgyBridge

## Reason

The name represents the main purpose of the project:

Building bridges between:

- tradition and modern accessibility
- languages and communities
- worship and understanding

The name is internationally understandable and does not favor a specific Orthodox tradition.

---

# Decision 002 - Open Source Project

## Decision

LiturgyBridge is developed as an open-source project.

## Reason

The project benefits from collaboration between:

- developers
- translators
- clergy
- musicians
- communities

Transparency and shared development are important for long-term sustainability.

---

# Decision 003 - Software License

## Decision

The software is licensed under:

Apache License 2.0

## Reason

Apache 2.0 provides:

- open collaboration
- reuse possibilities
- contributor protection
- suitability for community and professional adoption

Software licensing is separated from content licensing.

---

# Decision 004 - Separation of Software and Content

## Decision

Software and content are treated as separate domains.

## Reason

LiturgyBridge contains different types of assets:

- software code
- liturgical texts
- translations
- music
- images
- community resources

Each may have different ownership and licensing requirements.

---

# Decision 005 - Tradition First

## Decision

Technology supports the liturgical tradition but does not modify it.

## Reason

The purpose of LiturgyBridge is understanding and accessibility.

The platform should not:

- replace liturgical practice
- introduce unauthorized changes
- prioritize automation over tradition

---

# Decision 006 - Verified Content Before AI Translation

## Decision

Structured and approved content has priority over automated translation.

## Reason

Many Orthodox services contain fixed and recurring texts.

Prepared translations are usually more reliable than real-time AI translation.

AI assistance is mainly intended for:

- sermons
- announcements
- explanations
- spontaneous speech

---

# Decision 007 - Human Oversight

## Decision

Important decisions require responsible human review.

## Reason

Automation can assist but should not replace:

- clergy
- translators
- community leaders
- content experts

---

# Decision 008 - Liturgical Templates

## Decision

Services are modeled using reusable liturgical templates.

## Reason

Orthodox services follow structured patterns.

A template-based approach enables:

- consistency
- multilingual support
- synchronization
- easier maintenance

Examples:

- Divine Liturgy of St. John Chrysostom
- Divine Liturgy of St. Basil
- Vespers
- Matins

---

# Decision 009 - Community Separation

## Decision

Each community operates in its own protected digital space.

## Reason

Communities need control over:

- members
- documents
- events
- internal communication
- shared resources

Public liturgical resources and private community data must remain separated.

---

# Decision 010 - Multiple Community Membership

## Decision

A user can belong to multiple communities.

## Reason

Modern users often participate in several groups:

Examples:

- home parish
- choir
- monastery community
- youth group
- regional organization

The system should reflect real community relationships.

---

# Decision 011 - Privacy First

## Decision

Privacy is a core architectural principle.

## Reason

Community data may contain personal or sensitive information.

The system should follow:

- least privilege access
- clear ownership
- controlled sharing
- minimal data collection

---

# Decision 012 - Modular Architecture

## Decision

LiturgyBridge is designed as a modular platform.

## Reason

Different communities may need different capabilities.

Modules may include:

- Liturgical Core
- Community Platform
- Translation Services
- Notification System
- Knowledge Archive

Modules should evolve independently where possible.

---

# Decision 013 - Offline and Local Network Support

## Decision

Local deployment scenarios should remain possible.

## Reason

Some communities may have:

- unreliable internet access
- privacy requirements
- local events

The architecture should support:

- local WiFi networks
- local servers
- offline-capable usage where possible

---

# Decision 014 - No Advertising-Based Model

## Decision

LiturgyBridge should not depend on advertising.

## Reason

The project serves communities and should prioritize:

- trust
- privacy
- accessibility
- sustainability

---

# Decision 015 - Community as a Core Element

## Decision

Community features are a fundamental part of the long-term vision.

## Reason

The project is not only about translating worship.

Communities need digital spaces for:

- communication
- organization
- shared knowledge
- cooperation

The liturgy is the foundation, and community life grows from it.

---

# Decision 016 - Integration-First Community Approach

## Decision

Instead of developing a full-featured, self-hosted community platform containing calendar database structures, messaging/chat interfaces, and private file hosting, LiturgyBridge utilizes an integration-first approach. It connects to existing tools (e.g., ChurchTools, Nextcloud, WebDAV, Telegram, Signal) via standard APIs, iCal feeds, and SSO/OIDC.

## Reason

A custom full-stack community management platform significantly increases scope, hosting requirements (storage/security for private documents), and user adoption friction. Integrating with existing tools:

- Prevents data duplication (parishes keep using their existing calendar/member databases).
- Minimizes security and legal overhead (private documents are hosted on the parish's Nextcloud instance, not LiturgyBridge).
- Keeps the core LiturgyBridge application lean, highly performant, and easy to host (even on a local Raspberry Pi in offline scenarios).
- Lowers adoption barriers for parishes that already have digital infrastructure.

---

# Decision 017 - Backend Language and Framework (Python & FastAPI)

## Decision

The backend of LiturgyBridge will be built using Python, utilizing the FastAPI web framework alongside SQLModel and Pydantic.

## Reason

Python is already a primary language for the core developers, ensuring high productivity and developer velocity. Furthermore, Python boasts the best ecosystem for future speech-to-text, machine translation, and AI capabilities (Phase 4). FastAPI provides native asynchronous execution, enabling high-performance WebSocket connections required by the synchronization engine, while SQLModel integrates Pydantic and SQLAlchemy for seamless data validation and database models.

---

# Decision 018 - Database System (PostgreSQL with JSONB)

## Decision

LiturgyBridge will use PostgreSQL as its primary database. It will employ a hybrid design: standard relational tables for structured models (Users, Communities, Services) combined with **JSONB** columns to store the deeply nested, hierarchical, and multilingual structures of liturgical texts.

## Reason

PostgreSQL is a robust, production-grade relational database with excellent JSONB querying capabilities. Liturgical texts are naturally hierarchical and multilingual (parallel translation trees), making standard relational normalization highly complex. Storing them as JSONB documents allows clean retrieval and flexible updates, while standard relations ensure integrity for user and configuration data.

---

# Decision 019 - API and Realtime Protocol (REST & WebSockets)

## Decision

The communications between client applications (visitor smartphones, admin portals) and the backend will be conducted using a hybrid API approach: a REST API for heavy static data retrieval, and WebSockets for real-time synchronization updates.

## Reason

REST is the industry standard for traditional request-response operations, such as loading static liturgical texts. WebSockets provide a persistent, low-overhead bi-directional channel ideal for pushing small, real-time synchronization packets (e.g., active section changes) to all connected clients during a worship service without overloading mobile data connections in churches.

---

# Decision 020 - Frontend Stack (Vue.js, Vite & TailwindCSS)

## Decision

The user interface of LiturgyBridge will be developed as a Single Page Application (SPA) using Vue.js, built with Vite, and styled using TailwindCSS.

## Reason

Vue.js offers a gentle learning curve for Python developers due to its clean separation of HTML, JS, and CSS within Single File Components (`.vue`). Combined with Vite, it provides extremely fast compilation and a rapid feedback loop. TailwindCSS allows rapid creation of custom, premium, responsive mobile layouts with dark mode optimization, while the SPA architecture allows wrapping the application using Capacitor for native Android/iOS distribution later.

---

# Decision 021 - Database Security and Network Isolation

## Decision

LiturgyBridge will enforce database security using environment-based credentials (stored in local `.env` files ignored by Git) coupled with private Docker network isolation. The PostgreSQL database port (5432) will not be exposed to the public internet in production; only the FastAPI backend container will have access to the database container within an isolated bridge network.

## Reason

Hardcoding default database credentials or exposing database ports to the public internet presents severe security risks. By isolating the database container within a private virtual network and mapping the port only to `127.0.0.1` locally (for development), we ensure that the database is completely inaccessible from the outside world. Using environment variables dynamically loaded by both Docker and Python ensures that credentials can be easily customized and rotated in production without code changes.

---

# Decision 022 - Dynamic Liturgical Calendar and Texts Resolution

## Decision

LiturgyBridge will resolve the variable components of liturgical services (propria, such as scripture readings, Troparia, Kontakia, and weekly Tones) dynamically at runtime. The system will calculate the liturgical day based on the scheduled date using Orthodox calendar algorithms (Julian/Gregorian conversions and Pascha cycles). Templates will reference placeholders (e.g., `dynamic.tonal_troparion`) that are replaced by concrete database text keys (e.g., `oktoechos.tone_4.troparion`) on retrieval.

## Reason

Hardcoding all possible daily text permutations into service templates is unmanageable. Calculating the Tone cycle and readings programmatically keeps templates reusable, lightweight, and database-driven.

---

# Decision 023 - LiturgyWiki and AI Chatbot Companion with Cost Control

## Decision

The application will integrate an educational LiturgyWiki for terms lookups, and a Gemini-powered AI Liturgical Chatbot companion (`/api/v1/wiki/chat`) to explain services dynamically to visitors. To prevent API abuse and control token costs:
1. The backend will intercept and answer standard terminology queries directly using local Wiki articles before calling the Gemini API.
2. The system will apply IP/session rate limiting.
3. The context payload sent to Gemini will be truncated to the active liturgy segment and relevant wiki snippets.

## Reason

An AI chatbot provides a welcoming, interactive interface for visitors to understand Orthodox worship. Combining it with local Wiki-first interception and rate limits ensures the solution remains cost-effective (free or negligible operational cost) and safe from request floods.

---

# Decision 024 - Audio Accessibility and Simultaneous Translation

## Decision

LiturgyBridge will support simultaneous translation via audio guides. Visitors can listen to the translated liturgy in their preferred language using headphones. The application will synchronize the audio track playback with the active liturgy section controlled by the priest. 

## Reason

Many churchgoers prefer not to look at their phone screens during a worship service. An audio track allows visitors to follow the service meditatively while keeping their eyes on the altar and iconostasis.

---

# Decision 025 - Cloud-Based Text-to-Speech (TTS) Integration

## Decision

The application will integrate cloud-based Text-to-Speech (TTS) services to generate high-quality neural voices. We will abstract the TTS API calls (supporting Google Cloud TTS and OpenAI TTS) in the backend services layer. For dynamic/custom texts (like the priest's sermon or the daily scripture readings), the backend will call the active cloud TTS provider dynamically and stream the synthesized audio back to the client.

## Reason

Built-in browser voices (Web Speech API) are highly robotic and inconsistent across different devices. Using neural, human-sounding cloud voices provides a professional, reverent liturgical experience.

---

# Decision 026 - Parish Audio Sharing and Choral Track Marketplace

## Decision

LiturgyBridge will introduce an `AudioTrack` model to store multiple recorded and shared audio versions of liturgical prayers. Parishes can upload high-quality audio files of their own choir singing standard prayers in their language (e.g. German Byzantine chants). If a parish marks a track as shared (`is_shared = True`), it becomes globally available in the database, allowing any other parish to adopt and play it during their services. The system will use cloud TTS to generate default spoken fallback tracks (marked as `is_system_default`) to guarantee 100% audio coverage immediately.

## Reason

Orthodox worship is almost exclusively sung or chanted. Standard spoken TTS cannot capture the beauty of liturgical choral music. Allowing parishes to upload, share, and cross-adopt real choir recordings creates a collaborative community marketplace while maintaining a fallback system.

---

# Decision 027 - Database-Stored Audio Blobs & Nextcloud Integration Path

## Decision

Audio tracks (MP3 data generated via TTS or uploaded by parishes) will be stored directly inside the PostgreSQL database as binary data (`LargeBinary` / BLOB) on the `AudioTrack` table. The backend will expose a streaming endpoint `/api/v1/liturgy/audio-tracks/{track_id}/stream` to serve the raw audio files. 

For future scaling, the storage engine will be abstracted so that audio files can be transparently routed to an external Nextcloud instance (via WebDAV API), while keeping the public streaming route and database metadata schema unchanged.

## Reason

Storing files directly in the database ensures the application is 100% self-contained and state-free, avoiding container file storage persistence and synchronization issues in Docker environments. Designing it with an abstract stream route ensures we can easily swap backend storage to Nextcloud in the future without breaking any client app code.

---

# Decision 028 - Dynamic Sermon Translation and Audio Synthesis

## Decision

The application will support dynamic sermon editing by priests in any source language. The backend will expose a dedicated endpoint `PUT /api/v1/liturgy/services/{service_id}/sermon` that accepts the raw sermon text and source language. The system will:
1. Generate unique service-specific text keys (`sermon.service_{service_id}`).
2. Translate the text into all other active service languages (excluding Church Slavonic, `cu`) using a swappable Translation Service (supporting DeepL API and LLM-fallback).
3. Automatically trigger the active Text-to-Speech (TTS) provider to synthesize and store MP3 audio tracks directly in the database (`AudioTrack`) for each translated text.

## Reason

A priest must be free to preach in their preferred language. To make the sermon instantly accessible to international visitors without forcing them to read screens during the liturgy, translating the text and synthesizing the audio files immediately allows visitors to follow along via their audio guide headphones in real-time. Excluding Church Slavonic is required because it is a sacred liturgical language not used for contemporary sermons.

---

# Decision 029 - OIDC SSO with Nextcloud Group-to-Role Mapping

## Decision

LiturgyBridge delegates user authentication to a parish's Nextcloud instance using the OpenID Connect (OIDC) / OAuth 2.0 protocol. The backend OIDC callback endpoint:
1. Dynamically handles the authorization code exchange via standard POST parameters (for maximum PHP library compatibility).
2. Dynamically queries Nextcloud's OCS API (`/ocs/v2.php/cloud/user`) to retrieve the user's details and group memberships.
3. Automatically maps Nextcloud groups to local LiturgyBridge roles (e.g., Nextcloud group `admin` -> `admin`/`editor`, group `clergy`/`priests` -> `priest`, group `choir` -> `choir`).
4. Generates a local JWT token (HS256, signed using `JWT_SECRET`) containing the user's name, email, and mapped roles to secure downstream API endpoints.

## Reason

Delegating authentication to Nextcloud ensures LiturgyBridge doesn't store sensitive password hashes or manage user registrations directly, complying with GDPR/data privacy guidelines. Automatically mapping Nextcloud groups to LiturgyBridge roles ensures that parish secretaries can manage all user permissions directly in their pre-existing Nextcloud Admin interface without needing a separate user panel in LiturgyBridge.

---

# Decision 030 - Native Direct Authentication & Onboarding Flow

## Decision

To support a seamless user experience where new parishioners can register and log in directly inside the LiturgyBridge Vue client without being redirected away to Nextcloud's login page, the system will support a *Direct Credential Verification* fallback. 
1. **Direct Login**: The Vue client collects username/password in a native modal. The LiturgyBridge backend verifies these credentials by sending an authenticated request to Nextcloud's OCS API. If Nextcloud validates the credentials, LiturgyBridge generates the local session JWT.
2. **Onboarding / Self-Registration**: New users can submit a registration form in the Vue client. The backend will use Nextcloud's Provisioning API to create a new user account in Nextcloud in a disabled/pending state. Parish administrators can approve the user directly inside the LiturgyBridge dashboard, which enables the Nextcloud account and assigns them to the default `members` group.

## Reason

Redirecting users to Nextcloud's default login screen disrupts the user experience, especially on mobile devices. Allowing native credentials inputs and self-registration forms inside the LiturgyBridge interface keeps the experience unified and professional while maintaining Nextcloud as the single source of truth for passwords and groups.

---

# Future Decisions

Future decisions should be documented when they affect:

- architecture
- data ownership
- security
- user experience
- licensing
- technology choices

