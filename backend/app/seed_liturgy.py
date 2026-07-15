"""
Database Seeding Script for LiturgyBridge.

Populates PostgreSQL with the complete sequential structure of the Divine Liturgy
of St. John Chrysostom, featuring aligned Church Slavonic (cu, Cyrillic) and
German (de) text overlays, Tone 6 Resurrectional Hymns, Sunday Scripture readings,
and parish-shared choir audio track references.
"""

import uuid
from datetime import datetime, timezone
from sqlmodel import Session, SQLModel, select

from backend.app.database import engine
from backend.app.models import (
    User,
    Community,
    LiturgicalTemplate,
    TextItem,
    TranslationItem,
    AudioTrack,
)

def seed_database():
    print("Initializing tables...")
    SQLModel.metadata.create_all(engine)

    with Session(engine) as session:
        # 1. Verify if already seeded
        existing_template = session.exec(
            select(LiturgicalTemplate).where(LiturgicalTemplate.name == "Göttliche Liturgie des Hl. Johannes Chrysostomus")
        ).first()
        if existing_template:
            print("Database already seeded with Liturgy Template. Skipping seeding.")
            return
        print("Seeding community and priest...")
        # Create or fetch default community
        comm = session.get(Community, uuid.UUID("87a935b6-6124-4f7c-8b9c-8605ef4dad87"))
        if not comm:
            comm = Community(
                id=uuid.UUID("87a935b6-6124-4f7c-8b9c-8605ef4dad87"),
                name="Kathedrale zum Hl. Nikolaus",
                location="Berlin, Deutschland"
            )
            session.add(comm)
            session.commit()
            session.refresh(comm)

        # Create or fetch default priest user
        priest = session.get(User, uuid.UUID("d56ba13b-8512-4eb1-b92c-f9be88a101f3"))
        if not priest:
            priest = User(
                id=uuid.UUID("d56ba13b-8512-4eb1-b92c-f9be88a101f3"),
                name="Vater Alexej",
                email="alexej@nikolaus-kathedrale.de",
                sso_provider="nextcloud",
                external_user_id="nc_alexej"
            )
            session.add(priest)
            session.commit()
            session.refresh(priest)

        print("Seeding text library (Church Slavonic and German overlays)...")

        # Texts list: (key, category, default_en, cu_text, de_text)
        texts_to_seed = [
            # 1. Opening Blessing
            (
                "liturgy.opening_blessing", "litany",
                "Blessed is the Kingdom of the Father and of the Son and of the Holy Spirit, now and ever and unto ages of ages.",
                "Благословено Царство Отца и Сына и Святаго Духа, ныне и присно и во веки веков.",
                "Gesegnet sei das Reich des Vaters und des Sohnes und des Heiligen Geistes, jetzt und immerdar und in die Ewigkeiten der Ewigkeiten."
            ),
            # 2. Great Litany Response
            (
                "liturgy.great_litany.lord_have_mercy", "litany",
                "Lord, have mercy.",
                "Господи, помилуй.",
                "Herr, erbarme dich."
            ),
            # 3. First Antiphon Refrain
            (
                "liturgy.first_antiphon.refrain", "hymn",
                "Through the prayers of the Theotokos, O Savior, save us.",
                "Молитвами Богородицы, Спасе, спаси нас.",
                "Auf die Fürbitten der Gottesgebärerin, o Retter, rette uns."
            ),
            # 4. Trisagion (Holy God)
            (
                "liturgy.trisagion.main", "hymn",
                "Holy God, Holy Mighty, Holy Immortal, have mercy on us.",
                "Святый Боже, Святый Крепкий, Святый Безсмертный, помилуй нас.",
                "Heiliger Gott, heiliger Starker, heiliger Unsterblicher, erbarme dich unser."
            ),
            # 5. Cherubic Hymn
            (
                "liturgy.cherubic_hymn.main", "hymn",
                "Let us who mystically represent the Cherubim and sing the thrice-holy hymn to the life-giving Trinity lay aside all earthly cares.",
                "Иже Херувимы тайно образующе, и Животворящей Троице Трисвятую песнь припевающе, всякое ныне житейское отложим попечение.",
                "Die wir die Cherubim geheimnisvoll darstellen und der lebensspendenden Dreifaltigkeit den dreimalheiligen Lobgesang singen, lasst uns ablegen alle irdischen Sorgen."
            ),
            # 6. Creed
            (
                "liturgy.creed.main", "creed",
                "I believe in one God, the Father Almighty, Maker of heaven and earth...",
                "Верую во единаго Бога Отца Вседержителя, Творца небу и земли...",
                "Ich glaube an den einen Gott, den Vater, den Allmächtigen, den Schöpfer des Himmels und der Erde..."
            ),
            # 7. Lord's Prayer
            (
                "liturgy.lords_prayer.main", "prayer",
                "Our Father, who art in heaven, hallowed be Thy name...",
                "Отче наш, Иже еси на небесех, да святится имя Твое...",
                "Vater unser im Himmel, geheiligt werde Dein Name..."
            ),
            # 8. Sermon Placeholder
            (
                "liturgy.sermon_placeholder", "sermon",
                "Sermon / Homily",
                "Проповедь",
                "[Wort des Priesters / Predigt]"
            ),
            # --- Tonal changeables (Tone 6 for July 19, 2026) ---
            (
                "oktoechos.tone_6.troparion", "hymn",
                "The Angelic powers were at Your tomb and the guards became as dead men...",
                "Ангельския силы на гробе Твоем, и стрегущии омертвеша...",
                "Die Engelsmächte waren an Deinem Grabe, und die Wächter erstarrten wie Tote..."
            ),
            (
                "oktoechos.tone_6.kontakion", "hymn",
                "When Christ our God rose from the tomb, He shattered the gates of Hades...",
                "Живоначальною дланию умершыя от мрачных удолий воскресив...",
                "Als Christus, unser Gott, aus dem Grab auferstand, zerbrach Er die Pforten des Hades..."
            ),
            (
                "oktoechos.tone_6.prokeimenon", "hymn",
                "O Lord, save Your people and bless Your inheritance.",
                "Спаси, Господи, люди Твоя, и благослови достояние Твое.",
                "Rette, o Herr, Dein Volk und segne Dein Erbe."
            ),
            # --- Scripture changeables (7th Sunday after Pentecost, Romans 12:1-10 & Matthew 12:1-15) ---
            (
                "scripture.epistle.Romans 12:1-10", "scripture",
                "Epistle Reading: Romans 12:1-10. Having gifts that differ according to the grace given to us...",
                "Апостол: Римлянам 12:1-10. Имуще же дарования по благодати данней нам различна...",
                "Epistellesung: Römer 12,1-10. Da wir aber verschiedene Gaben haben nach der uns gegebenen Gnade..."
            ),
            (
                "scripture.gospel.Matthew 12:1-15", "scripture",
                "Gospel Reading: Matthew 12:1-15. And getting into a boat he crossed over and came to his own city...",
                "Евангелие: Матфея 12:1-15. И влез в корабль, преплы и прииде во свой град...",
                "Evangelienlesung: Matthäus 12,1-15. Da stieg er in ein Boot, fuhr hinüber und kam in seine Stadt..."
            ),
        ]

        for key, cat, en_val, cu_val, de_val in texts_to_seed:
            # Create base TextItem if not existing
            ti = session.get(TextItem, key)
            if not ti:
                ti = TextItem(key=key, category=cat, default_text=en_val)
                session.add(ti)
                session.commit()
            
            # Create Slavonic Translation if not existing
            cu_trans = session.exec(
                select(TranslationItem).where(TranslationItem.text_key == key, TranslationItem.language == "cu")
            ).first()
            if not cu_trans:
                cu_trans = TranslationItem(
                    text_key=key,
                    language="cu",
                    translation_text=cu_val,
                    approved=True
                )
                session.add(cu_trans)

            # Create German Translation if not existing
            de_trans = session.exec(
                select(TranslationItem).where(TranslationItem.text_key == key, TranslationItem.language == "de")
            ).first()
            if not de_trans:
                de_trans = TranslationItem(
                    text_key=key,
                    language="de",
                    translation_text=de_val,
                    approved=True
                )
                session.add(de_trans)
        
        session.commit()
        print("Base texts seeded.")

        print("Seeding AudioTracks (Choral recordings & fallback TTS)...")
        
        # We simulate some high-quality pre-recorded German audio files for static elements
        default_audios = [
            ("liturgy.opening_blessing", "/static/audio/de/opening_blessing.mp3", "System Default Speech - Segen"),
            ("liturgy.great_litany.lord_have_mercy", "/static/audio/de/great_litany.mp3", "System Default Speech - Ektenie"),
            ("liturgy.creed.main", "/static/audio/de/creed.mp3", "System Default Speech - Glaubensbekenntnis"),
            ("liturgy.lords_prayer.main", "/static/audio/de/lords_prayer.mp3", "System Default Speech - Vaterunser"),
        ]
        
        for key, path, desc in default_audios:
            at = AudioTrack(
                text_key=key,
                language="de",
                audio_url="placeholder",
                is_system_default=True,
                is_shared=True,
                description=desc,
                audio_data=f"MOCK_DEFAULT_AUDIO_DATA_FOR_{key}".encode("utf-8")
            )
            session.add(at)
            session.commit()
            session.refresh(at)
            
            # Point URL to the dynamic database stream route
            at.audio_url = f"/api/v1/liturgy/audio-tracks/{at.id}/stream"
            session.add(at)

        # Seed a beautiful community-shared choir recording of the Cherubic Hymn
        choir_hymn = AudioTrack(
            text_key="liturgy.cherubic_hymn.main",
            language="de",
            audio_url="placeholder",
            community_id=comm.id,
            is_shared=True,
            is_system_default=False,
            description="Byzantinischer Tonsatz - Gesungen vom Chor der St. Nikolaus Kathedrale Berlin (Deutsch)",
            audio_data=b"MOCK_ST_NICHOLAS_CHOIR_RECORDING_BYTES_MP3"
        )
        session.add(choir_hymn)
        session.commit()
        session.refresh(choir_hymn)
        
        # Point URL to dynamic database stream route
        choir_hymn.audio_url = f"/api/v1/liturgy/audio-tracks/{choir_hymn.id}/stream"
        session.add(choir_hymn)
        session.commit()
        print("AudioTracks seeded in database.")

        print("Seeding Divine Liturgy Template...")
        # Define the complete Divine Liturgy structure
        liturgy_structure = {
            "name": "Göttliche Liturgie des Hl. Johannes Chrysostomus",
            "sections": [
                {
                    "section_key": "part_1.blessing",
                    "text_keys": ["liturgy.opening_blessing"]
                },
                {
                    "section_key": "part_1.great_litany",
                    "text_keys": ["liturgy.great_litany.lord_have_mercy"]
                },
                {
                    "section_key": "part_1.first_antiphon",
                    "text_keys": ["liturgy.first_antiphon.refrain"]
                },
                {
                    "section_key": "part_1.trisagion",
                    "text_keys": ["liturgy.trisagion.main"]
                },
                {
                    "section_key": "part_1.troparion",
                    "text_keys": ["dynamic.tonal_troparion"] # Tone-dependent placeholder
                },
                {
                    "section_key": "part_1.readings_epistle",
                    "text_keys": ["dynamic.epistle_reading"] # Date-dependent placeholder
                },
                {
                    "section_key": "part_1.readings_gospel",
                    "text_keys": ["dynamic.gospel_reading"] # Date-dependent placeholder
                },
                {
                    "section_key": "part_1.sermon",
                    "text_keys": ["liturgy.sermon_placeholder"] # Priest custom text
                },
                {
                    "section_key": "part_2.cherubic_hymn",
                    "text_keys": ["liturgy.cherubic_hymn.main"]
                },
                {
                    "section_key": "part_2.creed",
                    "text_keys": ["liturgy.creed.main"]
                },
                {
                    "section_key": "part_2.lords_prayer",
                    "text_keys": ["liturgy.lords_prayer.main"]
                }
            ]
        }

        template = LiturgicalTemplate(
            id=uuid.UUID("a9fb5917-a068-4592-80de-df619280d922"),
            name="Göttliche Liturgie des Hl. Johannes Chrysostomus",
            tradition="Byzantine",
            structure=liturgy_structure,
            is_shared=True
        )
        session.add(template)
        session.commit()
        print("Divine Liturgy Template seeded successfully!")

if __name__ == "__main__":
    seed_database()
