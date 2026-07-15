import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from sqlalchemy import Column, JSON
from sqlmodel import Field, Relationship, SQLModel

class Membership(SQLModel, table=True):
    """
    Connects Users to Communities with specific community-level roles.
    A user can have multiple roles in a single community.
    """
    user_id: uuid.UUID = Field(foreign_key="user.id", primary_key=True)
    community_id: uuid.UUID = Field(foreign_key="community.id", primary_key=True)
    community_roles: List[str] = Field(default=[], sa_column=Column(JSON))

class User(SQLModel, table=True):
    """
    Represents a user account in the system, supporting Single Sign-On (SSO)
    and global system roles.
    """
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True, index=True)
    name: str
    email: str = Field(unique=True, index=True)
    sso_provider: Optional[str] = Field(default=None, index=True)
    external_user_id: Optional[str] = Field(default=None, index=True)
    preferred_language: str = Field(default="de")
    global_roles: List[str] = Field(default=[], sa_column=Column(JSON))

    # Relationships
    communities: List["Community"] = Relationship(back_populates="members", link_model=Membership)
    bookmarks: List["Bookmark"] = Relationship(back_populates="user")
    notes: List["UserNote"] = Relationship(back_populates="user")

class Community(SQLModel, table=True):
    """
    Represents an independent parish, monastery, or choir organization.
    """
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True, index=True)
    name: str
    description: Optional[str] = None
    location: Optional[str] = None
    external_calendar_feed: Optional[str] = None
    external_storage_root: Optional[str] = None

    # Relationships
    members: List["User"] = Relationship(back_populates="communities", link_model=Membership)
    services: List["LiturgicalService"] = Relationship(back_populates="community")
    events: List["Event"] = Relationship(back_populates="community")
    resources: List["Resource"] = Relationship(back_populates="community")

class LiturgicalTemplate(SQLModel, table=True):
    """
    Outlines the structure of a worship service (e.g. Divine Liturgy).
    The structure is represented as a tree structure inside the JSON column.
    """
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True, index=True)
    name: str
    tradition: str  # e.g., "Byzantine", "Slavic"
    structure: Dict[str, Any] = Field(default={}, sa_column=Column(JSON))
    
    # Ownership and sharing settings
    community_id: Optional[uuid.UUID] = Field(default=None, foreign_key="community.id", nullable=True)
    author_id: Optional[uuid.UUID] = Field(default=None, foreign_key="user.id", nullable=True)
    is_shared: bool = Field(default=False)

    # Relationships
    author: Optional["User"] = Relationship()
    community: Optional["Community"] = Relationship()

class LiturgicalService(SQLModel, table=True):
    """
    A specific instance of a worship service, tracking active synchronization
    state for visitors.
    """
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True, index=True)
    template_id: uuid.UUID = Field(foreign_key="liturgicaltemplate.id")
    community_id: uuid.UUID = Field(foreign_key="community.id")
    scheduled_time: datetime
    status: str = Field(default="draft")  # draft, active, completed
    current_section_key: Optional[str] = None
    active_languages: List[str] = Field(default=[], sa_column=Column(JSON))

    # Relationships
    community: Community = Relationship(back_populates="services")
    template: LiturgicalTemplate = Relationship()
    events: List["Event"] = Relationship(back_populates="associated_service")
    bookmarks: List["Bookmark"] = Relationship(back_populates="service")

class Event(SQLModel, table=True):
    """
    Represents a calendar activity imported from an external calendar.
    """
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True, index=True)
    title: str
    start_time: datetime
    location: Optional[str] = None
    external_source_type: str  # e.g., "ical", "churchtools"
    external_id: str
    community_id: uuid.UUID = Field(foreign_key="community.id")
    associated_service_id: Optional[uuid.UUID] = Field(default=None, foreign_key="liturgicalservice.id")

    # Relationships
    community: Community = Relationship(back_populates="events")
    associated_service: Optional[LiturgicalService] = Relationship(back_populates="events")

class TextItem(SQLModel, table=True):
    """
    Stores base liturgical text metadata. Unique keys allow referencing texts
    inside JSONB templates. Can be global (community_id is Null) or specific to
    a local community (e.g. sermons, local announcements).
    """
    key: str = Field(primary_key=True, index=True)
    category: str  # e.g. "litany", "hymn", "announcement", "sermon"
    default_text: str
    community_id: Optional[uuid.UUID] = Field(default=None, foreign_key="community.id")

    # Relationships
    translations: List["TranslationItem"] = Relationship(back_populates="text_item")
    notes: List["UserNote"] = Relationship(back_populates="text_item")

class TranslationItem(SQLModel, table=True):
    """
    Stores translations associated with a specific TextItem key.
    """
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True, index=True)
    text_key: str = Field(foreign_key="textitem.key")
    language: str  # e.g. "de", "en", "ru", "el"
    translation_text: str
    approved: bool = Field(default=False)
    author_id: Optional[uuid.UUID] = Field(default=None, foreign_key="user.id")

    # Relationships
    text_item: TextItem = Relationship(back_populates="translations")

class Resource(SQLModel, table=True):
    """
    Stores a reference to files stored on an external cloud (Nextcloud, WebDAV).
    """
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True, index=True)
    external_url: str
    storage_provider: str  # nextcloud, webdav, google_drive
    file_type: str  # sheet_music, audio, document
    group_id: Optional[str] = None  # optional restriction to external group
    community_id: uuid.UUID = Field(foreign_key="community.id")

    # Relationships
    community: Community = Relationship(back_populates="resources")

class Notification(SQLModel, table=True):
    """
    Logs outgoing notifications triggered via webhook and sent to Telegram/Signal.
    """
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True, index=True)
    event_type: str  # service_time_changed, service_started
    target_channel_id: str  # channel hash or group id
    routing_channel: str  # telegram, signal, whatsapp
    status: str = Field(default="pending")  # pending, sent, failed
    error_message: Optional[str] = None
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class Bookmark(SQLModel, table=True):
    """
    Stores a user's bookmarked section index inside a LiturgicalService.
    """
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True, index=True)
    user_id: uuid.UUID = Field(foreign_key="user.id")
    service_id: uuid.UUID = Field(foreign_key="liturgicalservice.id")
    section_key: str
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    # Relationships
    user: User = Relationship(back_populates="bookmarks")
    service: LiturgicalService = Relationship(back_populates="bookmarks")

class UserNote(SQLModel, table=True):
    """
    Stores private notes/explanations created by a user for a specific TextItem.
    """
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True, index=True)
    user_id: uuid.UUID = Field(foreign_key="user.id")
    text_key: str = Field(foreign_key="textitem.key")
    content: str
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    # Relationships
    user: User = Relationship(back_populates="notes")
    text_item: TextItem = Relationship(back_populates="notes")

class WikiArticle(SQLModel, table=True):
    """
    Stores metadata for LiturgyWiki articles explaining terms or structures.
    """
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True, index=True)
    slug: str = Field(unique=True, index=True)
    category: str  # e.g., "terminology", "structure", "customs"
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    # Relationships
    translations: List["WikiTranslation"] = Relationship(back_populates="article")

class WikiTranslation(SQLModel, table=True):
    """
    Stores localized translations for a WikiArticle.
    """
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True, index=True)
    article_id: uuid.UUID = Field(foreign_key="wikiarticle.id")
    language: str  # e.g. "de", "en", "el"
    title: str
    content: str  # Markdown formatted text body
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    # Relationships
    article: WikiArticle = Relationship(back_populates="translations")
