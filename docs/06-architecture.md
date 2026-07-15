# Architecture

## Overview

LiturgyBridge is designed as a modular, open-source platform.

The architecture separates different domains to allow independent development, scaling, and adaptation by different communities.

The main architectural areas are:

1. Liturgical Core & Text Library
2. Service Synchronization Engine
3. Integration Layer (Community Connectors)
4. Translation and Language Services
5. Web Applications
6. Infrastructure and Caching

---

# High-Level Architecture

                LiturgyBridge
                      |
    -----------------------------------
    |                |                |
Liturgical      Integration      User Access
Core Layer      Layer (Connect)     Layer
    |                |                |
Text Library    OIDC/SSO Sync    Web Apps
Translations    Calendar Adapter Mobile Browser
Templates       Storage Connect  Admin Portal
Sync Engine     Msg Route Bot    Priest Portal

                     |
              Shared Services
                     |
    -----------------------------------
    |                |                |
Identity       Notifications      Media Cache



```mermaid
graph TD
    subgraph Client Layer (Frontend)
        A[Mobile Web App / PWA] -->|REST & WebSockets| B[FastAPI Gateway]
        A2[Admin Portal] -->|REST| B
    end

    subgraph Logic Layer (Backend)
        B --> C[SQLModel ORM]
        B --> D[Integration Connectors]
    end

    subgraph Data & External Layer
        C --> E[(PostgreSQL + JSONB)]
        D -.->|iCal/ICS| F[ChurchTools / Calendars]
        D -.->|WebDAV| G[Nextcloud / Storage]
        D -.->|Webhooks| H[Telegram / Signal Bots]
        B -.->|OAuth2/OIDC| I[SSO Identity Provider]
    end
```

---

# Technology Stack

LiturgyBridge relies on a standardized, open-source technology stack designed for developer velocity, ease of maintenance, and reliable real-time performance.

## Backend & API Layer
- **Language:** Python
- **Framework:** FastAPI (asynchronous, high-performance web framework)
- **Database ORM:** SQLModel (integrating SQLAlchemy and Pydantic)
- **Protocol:** REST API for static/heavy payload transfers + WebSockets for real-time synchronization updates.

## Database Layer
- **Database:** PostgreSQL
- **Data Models:** Hybrid relational models (users, communities, services) combined with PostgreSQL **JSONB** columns for nesting hierarchical, multilingual liturgical texts.

## Frontend Layer
- **Framework:** Vue.js (Single Page Application, SPA)
- **Build Tool:** Vite
- **Styling:** TailwindCSS (for modern, highly responsive design)

---

# 1. Liturgical Core

## Purpose

The Liturgical Core manages structured worship content.

It is the foundation of LiturgyBridge.

## Responsibilities

- liturgical templates
- service structures
- sections
- original texts
- translations
- terminology
- traditions and variations

Examples:

- Divine Liturgy of St. John Chrysostom
- Divine Liturgy of St. Basil
- Vespers
- Matins
- Feast services

---

# 2. Liturgical Data Library

## Purpose

A structured multilingual collection of liturgical resources.

Possible content:

- Church Slavonic texts
- Greek texts
- German translations
- English translations
- hymn texts
- explanations
- references

## Principles

- structured data instead of formatted documents
- version control
- attribution of sources
- clear licensing information

## Content Metadata and Licensing

Every content item should carry metadata describing:

- source
- author or organization
- language
- version
- license information
- approval status

This applies to:

- liturgical texts
- translations
- hymn resources
- educational materials
- media files

Content management must respect different ownership models.

---

# 3. Service Management

## Purpose

Allows communities or clergy to prepare upcoming services.

A service instance is created from a liturgical template.

Example:
Template:

Sunday Divine Liturgy
St. John Chrysostom

Service Instance:

Sunday 10:00
Parish:
St. Nicholas Church

Languages:
Church Slavonic
German
English

---

# 4. Synchronization Engine

## Purpose

Keeps users synchronized with the current point of the service.

Possible methods:

## Initial approach

Manual control:

- priest assistant selects current section
- users follow automatically

## Future approaches

Automatic recognition:

- speech recognition
- audio analysis
- predefined sequences
- AI assistance

The system should always allow human correction.

---

# 5. Translation Services

## Purpose

Support multilingual access.

## Fixed liturgical texts

Priority:

1. approved translations
2. community-reviewed translations
3. automated translation assistance

## Free speech

Examples:

- sermons
- announcements
- spontaneous explanations

Possible technologies:

- **AI Chatbot Interface (`LLMProvider`):** An abstracted Strategy Pattern interface that decouples the backend chatbot controller from specific LLM providers. Supports hot-swapping between Google Gemini and Anthropic Claude via environment variables, utilizing a Mock engine for test runs. Includes local Wiki-first interception for terminology lookups to prevent API costs.
- **Audio Translations (`TTSProvider`):** An abstracted Strategy Pattern interface for neural speech synthesis. Supports Google Cloud TTS, OpenAI TTS, and Mock providers to read translated sermons and readings in the listener's headphones.
- **Database BLOB Audio Streaming:** Raw audio bytes (MP3) are stored directly inside the PostgreSQL database (`BYTEA` column) to maintain state-free application hosting. The backend serves them via a unified streaming route (`/api/v1/liturgy/audio-tracks/{id}/stream`), which is architected to allow transparent redirection to Nextcloud WebDAV storage in future phases without client changes.
- **YouTube Audio Importer:** A backend service that uses `yt-dlp` to extract MP3 audio streams from YouTube links (e.g. parish choir recordings) and registers them as database BLOBs.

External AI and media storage services remain fully replaceable.

---

# 6. Integration Layer & Community Connectors

## Purpose

Integrates LiturgyBridge with existing community infrastructure instead of self-hosting redundant data.

Connectors:

- **Identity (OIDC/OAuth2):** Delegates authentication to community systems (e.g., Nextcloud, ChurchTools).
- **Calendar (iCal/ICS):** Periodically pulls events from parish calendars, mapping them to Liturgical Services.
- **Storage (Nextcloud/WebDAV):** Serves resource directories (like choir sheet music) directly from external cloud folders.
- **Notification Router:** Relays platform announcements and schedule changes via external chat channels (Telegram, Signal, WhatsApp bots).

Examples of integrated workflow:

Parish Calendar (ChurchTools)
       |
       v (iCal Adapter)
LiturgyBridge (Link template)
       |
       +--> Link to Nextcloud folder (Choir sheet music)
       +--> Notify Telegram channel (Service started)

## Data Ownership

LiturgyBridge does not store primary community files or user database directories. 

- LiturgyBridge only retains minimal references (e.g., Nextcloud directory IDs, calendar event IDs, external user hashes).
- Access control permissions and files remain under the ownership of the parish's external systems.

---

# 7. User Interface Layer

## Visitor Interface

Designed for people attending services.

Features:

- QR-code access
- language selection
- synchronized texts
- simple controls
- no required account

---

## Member Interface

Features:

- community information
- calendar
- notifications
- groups
- resources

---

## Priest / Administrator Interface

Features:

- prepare services
- select liturgical templates
- manage community information
- coordinate resources

---

# 8. Infrastructure

## Design Goals

The platform should support:

- cloud deployment
- local network deployment
- offline-capable scenarios

Possible environments:

- public hosting
- parish server
- local WiFi network

---

# 9. Privacy, Security and Ownership

## Principles

- communities control their own data
- users control their personal information
- content ownership is preserved
- permissions follow responsibilities

Technical administrators should not automatically have access to private community content.

The architecture must support separation between:

- public liturgical resources
- community-owned resources
- personal user data

---

# 10. Modular Design

LiturgyBridge should consist of replaceable components.

Example:

LiturgyBridge

├── Web Applications
├── API Layer (GraphQL/REST)
├── Auth Layer (OIDC/SSO)
├── Liturgical Engine
├── Integration Adapters (Calendar, Nextcloud, Messengers)
├── Translation Connectors
├── Notification Service
└── Caching & Cache Storage


---

# Future Extensions

Possible future modules:

- choir and music library
- educational materials
- catechism resources
- digital archives
- multilingual Bible references
- monastery support
- diocesan administration

---

# Architectural Principles

## Tradition First

Technology supports the liturgical tradition.

---

## Open Standards

Data formats should allow exchange and community contribution.

---

## Modular Development

Features should be independently maintainable.

---

## Human Oversight

Automation assists people but does not replace responsible decisions.
