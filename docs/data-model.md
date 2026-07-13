# Data Model

## Overview

LiturgyBridge consists of several interconnected domains:

1. Identity and Users
2. Communities
3. Liturgical Content
4. Services and Events
5. Groups and Resources
6. Notifications

The data model should remain flexible to support different Orthodox traditions, languages, and community structures.

---

# 1. User

## Description

A User represents a person using LiturgyBridge.

A user may participate in multiple communities.

## Attributes

Possible attributes:

- User ID
- Name
- Email (optional depending on account type)
- Preferred language
- Notification preferences
- Joined communities
- Roles

## Relationships

A User can:

- belong to multiple Communities
- belong to multiple Groups
- receive Notifications
- manage personal preferences

---

# 2. Community

## Description

A Community represents an independent parish, monastery, or organization.

Examples:

- Orthodox parish
- monastery
- mission community
- choir organization

## Attributes

Possible attributes:

- Community ID
- Name
- Description
- Location
- Contact information
- Public visibility settings
- Opening hours

## Relationships

A Community has:

- Members
- Groups
- Events
- Documents
- Media
- Announcements

---

# 3. Membership

## Description

Membership connects Users with Communities.

A user may belong to multiple communities.

## Attributes

Possible attributes:

- User
- Community
- Membership status
- Joined date
- Community role

Examples:

- member
- administrator
- editor
- volunteer

---

# 4. Group

## Description

A Group is a smaller area inside a Community.

Examples:

- choir
- youth group
- volunteers
- catechism group

## Attributes

Possible attributes:

- Group ID
- Name
- Description
- Access level

## Relationships

A Group has:

- Members
- Resources
- Events
- Messages

---

# 5. Liturgical Service

## Description

A Service represents a specific worship event.

Examples:

- Divine Liturgy of St. John Chrysostom
- Vespers
- Matins
- Feast Day Service

## Attributes

Possible attributes:

- Service ID
- Date and time
- Service type
- Language
- Community
- Liturgical template

## Relationships

A Service contains:

- Sections
- Texts
- Translations
- Participants

---

# 6. Liturgical Template

## Description

A Liturgical Template defines the structure of a recurring service.

Examples:

- Sunday Divine Liturgy
- Paschal Service
- Funeral Service

## Attributes

Possible attributes:

- Template ID
- Name
- Tradition
- Structure
- Required sections

## Relationships

A Template contains:

- Liturgical Sections

---

# 7. Liturgical Section

## Description

A Section represents a part of a service.

Examples:

- Great Litany
- Little Entrance
- Gospel Reading
- Cherubic Hymn
- Anaphora

## Attributes

Possible attributes:

- Section ID
- Name
- Order number
- Speaker
- Text references

---

# 8. Text and Translation

## Description

A Text represents liturgical content in a specific language.

## Attributes

Possible attributes:

- Text ID
- Language
- Original/source
- Translation status
- Approval status

Examples:

Languages:

- Church Slavonic
- German
- English
- Greek
- Romanian

## Relationships

A Text can have:

- multiple translations
- references to sections
- contributors

---

# 9. Event

## Description

An Event represents a community activity.

Examples:

- worship service
- choir rehearsal
- parish meeting
- feast celebration

## Attributes

Possible attributes:

- Event ID
- Title
- Date/time
- Location
- Visibility
- Organizer

---

# 10. Resource

## Description

A Resource represents shared community material.

Examples:

- PDF
- image
- audio recording
- document
- hymn text

## Attributes

Possible attributes:

- Resource ID
- Type
- Owner
- Access permissions
- Related group/community

---

# 11. Notification

## Description

A Notification informs users about relevant updates.

Examples:

- service time changed
- new document available
- event reminder

## Attributes

Possible attributes:

- Notification ID
- Recipient
- Type
- Message
- Timestamp

---

# 12. Relationships Overview
