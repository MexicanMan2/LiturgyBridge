"""
LiturgyBridge Community Router.

This module defines endpoints for managing community configuration,
syncing calendars (iCal feeds), and connecting to Nextcloud WebDAV resources.
"""

from fastapi import APIRouter

router = APIRouter(
    prefix="/communities",
    tags=["Communities"]
)

@router.get("/{community_id}/calendar/sync")
def trigger_calendar_sync(community_id: str):
    """
    Triggers manual sync of external calendar events (ICS feed)
    for the specified community.
    """
    return {"message": f"Calendar sync initiated for community {community_id}."}

@router.get("/{community_id}/resources")
def list_external_resources(community_id: str, folder_path: str = "/"):
    """
    Fetches file lists contextually from Nextcloud storage for the specified community
    (e.g., choir sheet music, rehearsal recordings).
    """
    return {
        "community_id": community_id,
        "folder_path": folder_path,
        "files": []  # List of Nextcloud resource references
    }
