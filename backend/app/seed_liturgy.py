"""
Database Seeding Script for LiturgyBridge.

Redirects to seed_complete_liturgy to ensure that the complete, untruncated
liturgy texts are always loaded during tests and initialization.
"""

from backend.app.seed_complete_liturgy import seed_complete_liturgy

def seed_database():
    seed_complete_liturgy()

if __name__ == "__main__":
    seed_database()
