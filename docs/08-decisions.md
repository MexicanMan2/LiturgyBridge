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

# Future Decisions

Future decisions should be documented when they affect:

- architecture
- data ownership
- security
- user experience
- licensing
- technology choices
