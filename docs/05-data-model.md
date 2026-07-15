# Data Model (SQLModel Database Schema)

## Overview

LiturgyBridge consists of several interconnected domains. All primary keys are UUIDs (except for `TextItem` which uses a unique string key) to allow seamless distributed/local-first sync between local parish servers and the central cloud.

---

# 1. User

## Description

A User represents an account in the system, supporting Single Sign-On (SSO) and global roles.

## Attributes

- **User ID:** UUID (Primary Key)
- **Name:** String
- **Email:** String (Unique, Indexed)
- **SSO Provider:** String (Optional, e.g., "nextcloud", "churchtools")
- **External User ID:** String (Optional, ID from the SSO provider)
- **Preferred Language:** String (Default: "de")
- **Global Roles:** JSON array of strings (e.g., `["translator", "platform_admin"]`)

## Relationships

- **Communities:** Linked to `Community` via the `Membership` table.
- **Bookmarks:** Has many `Bookmark` records.
- **Notes:** Has many `UserNote` records.

---

# 2. Community

## Description

A Community represents an independent parish, monastery, or choir organization.

## Attributes

- **Community ID:** UUID (Primary Key)
- **Name:** String
- **Description:** String (Optional)
- **Location:** String (Optional)
- **External Calendar Feed:** String (Optional, URL to ICS/iCal feed)
- **External Storage Root:** String (Optional, Nextcloud directory reference)

## Relationships

- **Members:** Linked to `User` via the `Membership` table.
- **Services:** Has many `LiturgicalService` instances.
- **Events:** Has many `Event` instances imported from external calendars.
- **Resources:** Has many `Resource` references to Nextcloud folders/files.

---

# 3. Membership

## Description

A join model connecting Users with Communities, specifying community-level roles. A user can hold multiple roles in a single community.

## Attributes

- **User ID:** UUID (Foreign Key to User, Compound Primary Key)
- **Community ID:** UUID (Foreign Key to Community, Compound Primary Key)
- **Community Roles:** JSON array of strings (e.g., `["priest", "administrator", "member"]`)

---

# 4. Group (Community Adaption)

## Description

Groups (like youth groups or choir groups) are defined on external systems (e.g., Nextcloud groups or ChurchTools groups). LiturgyBridge accesses them via SSO directory mapping rather than managing a duplicate relational database of groups.

---

# 5. Liturgical Template

## Description

Outlines the structure of a worship service. It is designed using a hybrid model: standard relational metadata combined with a nested JSON structure that outlines the sequence of sections.

## Attributes

- **Template ID:** UUID (Primary Key)
- **Name:** String
- **Tradition:** String (e.g., "Byzantine", "Slavic")
- **Structure:** JSON tree structure containing nested service sections, where each section references unique `TextItem` keys.

---

# 6. Liturgical Service

## Description

A scheduled or running instance of a template, tracking active synchronization state for visitors.

## Attributes

- **Service ID:** UUID (Primary Key)
- **Template ID:** UUID (Foreign Key to LiturgicalTemplate)
- **Community ID:** UUID (Foreign Key to Community)
- **Scheduled Time:** DateTime (Timezone-aware)
- **Status:** String (e.g., "draft", "active", "completed")
- **Current Section Key:** String (Optional, tracks the active section index for WebSockets sync)
- **Active Languages:** JSON array of language code strings (e.g., `["cu", "de"]`)

## Relationships

- **Events:** Linked to `Event` records associated with this service.
- **Bookmarks:** Has many `Bookmark` records from readers.

---

# 7. Event

## Description

A calendar activity imported from an external calendar system.

## Attributes

- **Event ID:** UUID (Primary Key)
- **Title:** String
- **Start Time:** DateTime (Timezone-aware)
- **Location:** String (Optional)
- **External Source Type:** String (e.g., "ical", "churchtools")
- **External ID:** String
- **Community ID:** UUID (Foreign Key to Community)
- **Associated Service ID:** UUID (Optional, Foreign Key to LiturgicalService)

---

# 8. TextItem

## Description

Stores base liturgical text metadata. A `TextItem` can be global (visible to all communities, e.g. standard litanies) or local/community-specific (e.g. local sermons, announcements, or custom prayers).

## Attributes

- **Key:** String (Primary Key, unique human-readable identifier like `liturgy.chrysostom.great_litany`, or auto-generated local key like `local.community_id.text_name`)
- **Category:** String (e.g., "litany", "hymn", "announcement", "sermon")
- **Default Text:** String (The base original language text)
- **Community ID:** UUID (Optional, Foreign Key to Community. Null if global)

## Relationships

- **Translations:** Has many `TranslationItem` records.
- **Notes:** Has many `UserNote` records.

---

# 9. TranslationItem

## Description

Stores translations in different languages mapped to a specific `TextItem` key.

## Attributes

- **Translation ID:** UUID (Primary Key)
- **Text Key:** String (Foreign Key to TextItem)
- **Language:** String (e.g., "de", "en", "ru", "el")
- **Translation Text:** String
- **Approved:** Boolean (Indicates if the translation is verified by a liturgical editor)
- **Author ID:** UUID (Optional, Foreign Key to User who authored the translation)

---

# 10. Resource

## Description

Stores a reference to files stored on an external cloud (Nextcloud, WebDAV, Google Drive) associated with a parish.

## Attributes

- **Resource ID:** UUID (Primary Key)
- **External URL:** String
- **Storage Provider:** String (e.g., "nextcloud", "webdav", "gdrive")
- **File Type:** String (e.g., "sheet_music", "audio", "document")
- **Group ID:** String (Optional, restricts file access to specific external group IDs)
- **Community ID:** UUID (Foreign Key to Community)

---

# 11. Notification

## Description

Logs outgoing notifications triggered via webhook and sent to Telegram, Signal, or WhatsApp.

## Attributes

- **Notification ID:** UUID (Primary Key)
- **Event Type:** String (e.g., "service_started", "service_time_changed")
- **Target Channel ID:** String (Channel ID or Webhook URL)
- **Routing Channel:** String (e.g., "telegram", "signal", "whatsapp")
- **Status:** String (e.g., "pending", "sent", "failed")
- **Error Message:** String (Optional)
- **Timestamp:** DateTime (Timezone-aware)

---

# 12. Reader Features (Bookmarks & User Notes)

## Bookmark

Tracks a user's bookmarked section key inside an active service, allowing them to save progress.

- **Bookmark ID:** UUID (Primary Key)
- **User ID:** UUID (Foreign Key to User)
- **Service ID:** UUID (Foreign Key to LiturgicalService)
- **Section Key:** String
- **Created At:** DateTime (Timezone-aware)

## UserNote

Stores private notes or annotations written by a user for a specific `TextItem`.

- **Note ID:** UUID (Primary Key)
- **User ID:** UUID (Foreign Key to User)
- **Text Key:** String (Foreign Key to TextItem)
- **Content:** String
- **Created At:** DateTime (Timezone-aware)
- **Updated At:** DateTime (Timezone-aware)
