# Roadmap

## Overview

LiturgyBridge will be developed incrementally.

The project starts with the foundation of multilingual liturgical access and gradually expands into a complete digital platform for Orthodox communities.

Each phase should provide practical value while creating the foundation for future capabilities.

---

# Phase 0 – Foundation and Concept

## Goal

Create a clear foundation for the project.

## Tasks

- define project vision
- document architecture
- define user roles
- define data model
- research existing resources
- review licensing requirements
- establish contribution guidelines

Status:

✅ Completed

---

# Phase 1 – Digital Liturgical Library

## Goal

Create a structured multilingual liturgical text platform.

## Features

- liturgical service templates
- structured text storage
- original language support
- translation management
- parallel language display

Examples:

- Church Slavonic
- German
- English
- Greek
- Romanian

Outcome:

Users can read and compare liturgical texts digitally.

Status: ✅ Completed

---

# Phase 2 – Service Companion

## Goal

Help visitors follow a live service.

## Features

- service preparation by authorized users
- QR-code access
- language selection
- synchronized text display
- manual service progression

Example:

A visitor enters a church, scans a QR code, selects German, and follows the current service section.

Status: ✅ Completed

---

# Phase 3 – Synchronization and Accessibility

## Goal

Improve the live experience.

## Features

- automatic section recognition
- audio assistance
- accessibility improvements
- larger text modes
- offline/local network support

Possible technologies:

- speech recognition
- audio processing
- local WiFi deployment

Human control remains available.

Status: ✅ Completed

---

# Phase 4 – Translation Support

## Goal

Support multilingual worship beyond fixed texts.

## Features

Fixed liturgical content:

- verified translations
- community-reviewed language resources

Dynamic content:

- sermons
- announcements
- explanations

Possible assistance:

- speech-to-text
- machine translation
- text-to-speech

Status: ✅ Completed

---

# Phase 5 – Integration Connectors

## Goal

Provide interfaces and adapters to connect LiturgyBridge with existing digital infrastructure of Orthodox parishes.

## Features

SSO & Directory Sync:
- Single Sign-On (OAuth2/OIDC) for parish members (via Nextcloud, ChurchTools).
- Synchronize group memberships (e.g., choir lists) to define access permissions.

Calendar Adapter:
- iCal/ICS feeds integration to fetch worship schedules from parish calendars.
- Link local Liturgical Services to imported events automatically.

Storage Connection:
- Contextual folder mapping (Nextcloud/WebDAV) for shared assets (sheet music, rehearsal audios, documents).
- File list visualization inside the web interface without hosting files locally.

Notification Router:
- Dispatch schedule updates and announcements to Telegram channels, Signal groups, or WhatsApp chat bots using simple webhooks.

Status: 🚧 Current phase

---

# Phase 6 – Knowledge and Tradition Preservation

## Goal

Create a collaborative archive of Orthodox resources.

## Features

- hymn libraries
- choir materials
- educational content
- historical documents
- explanations
- multilingual resources

The platform becomes a living repository of community knowledge.

---

# Phase 7 – International Community Network

## Goal

Enable collaboration between Orthodox communities worldwide.

## Features

- multiple traditions
- shared standards
- translation collaboration
- community contributions
- regional adaptations

Possible areas:

- Greek Orthodox
- Slavic Orthodox
- Romanian Orthodox
- Serbian Orthodox
- other traditions

---

# Development Principles

## Build from real community needs

Features should be developed together with communities.

---

## Start simple

A working solution with manual support is more valuable than a complex automated system that is unreliable.

---

## Preserve human responsibility

Technology assists priests, administrators, and communities.

---

## Open collaboration

The project should allow contributions from:

- developers
- translators
- clergy
- musicians
- community members
