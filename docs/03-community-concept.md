# Community Concept

## Purpose

LiturgyBridge should not only support participation during worship services, but also help communities organize communication, events, and shared resources.

The goal is to provide a structured alternative to fragmented communication channels.

---

## Community spaces

Each parish or community can create its own protected area.

Examples:

- Orthodox parish
- monastery
- choir group
- youth group
- catechism group

Users can join multiple communities.

---

## Community features

### Calendar Integration

Rather than managing a separate database of calendar events, LiturgyBridge integrates with existing calendars:

- Import gottesdienst schedules and events via standard **iCal/ICS feeds** or APIs (e.g., ChurchTools, Google Calendar).
- Link imported calendar events with liturgical templates inside LiturgyBridge.

---

### Notification Routing

Instead of developing an independent notification inbox and push service, LiturgyBridge utilizes popular messaging platforms:

- Configure webhooks to automatically post announcements (e.g., service schedule changes, feast day updates) to **Telegram channels, Signal groups, or WhatsApp**.
- Optional email notification relays.

---

### External Resource Storage

LiturgyBridge acts as a viewer and portal for files stored on existing community storage platforms:

- Integrate with **Nextcloud, WebDAV, or Google Drive** folders.
- Display relevant resources contextually (e.g., choir folders displaying sheet music and lyrics directly linked to the current service sections).
- Avoids the security and storage overhead of self-hosting private files.

---

## Privacy and Access Control

Community integrations must respect privacy boundaries:

- **Single Sign-On (SSO):** Authenticate users using existing community logins (OpenID Connect / OAuth2 via Nextcloud, ChurchTools, or other directory services).
- **Access Delegation:** Permissions to view group-specific files are delegated to the underlying storage provider (e.g., Nextcloud permissions determine who sees choir notes).
- Personal data is kept minimal, storing only external identifiers.

---

## Long-term goal

Provide communities with a seamless integration bridge that connects the liturgical companion with their existing digital infrastructure (calendars, cloud storages, and chat channels), preventing data duplication and reducing system complexity.
