"""
Batch script to generate real German TTS audio tracks for all 32 parts of the
Divine Liturgy of St. John Chrysostom and store them in PostgreSQL.
"""

import os
import urllib.request
import urllib.parse
import ssl
from sqlmodel import Session, select
from backend.app.database import engine
from backend.app.models import TextItem, TranslationItem, AudioTrack

def split_text_into_chunks(text: str, max_chars: int = 150) -> list[str]:
    words = text.split()
    chunks = []
    current_chunk = []
    current_length = 0
    for word in words:
        if current_length + len(word) + 1 > max_chars:
            chunks.append(" ".join(current_chunk))
            current_chunk = [word]
            current_length = len(word)
        else:
            current_chunk.append(word)
            current_length += len(word) + 1
    if current_chunk:
        chunks.append(" ".join(current_chunk))
    return chunks

def generate_all_tracks():
    print("=" * 80)
    print("GENERATING AUDIO TRACKS FOR ALL 32 LITURGY SECTIONS...")
    print("=" * 80)

    # Disable SSL verification for macOS environments
    ssl_context = ssl._create_unverified_context()

    with Session(engine) as session:
        # Fetch all text items that are part of the Liturgy template
        # (excluding sermon placeholder which is updated dynamically by the priest)
        text_items = session.exec(select(TextItem)).all()
        
        count = 0
        for item in text_items:
            # We skip scripture and sermon placeholders here as they are handled individually,
            # but we verton any standard liturgical items (e.g. liturgy.*, oktoechos.*)
            # wait, if Romans 12:1-10 and Matthew 12:1-15 are already seeded, we can skip or recreate them.
            # Let's recreate all standard liturgy.* keys and oktoechos.* keys!
            key = item.key
            if not (key.startswith("liturgy.") or key.startswith("oktoechos.") or key.startswith("scripture.")):
                continue
                
            if key == "liturgy.sermon_placeholder":
                continue

            # Fetch the German translation
            translation = session.exec(
                select(TranslationItem).where(
                    TranslationItem.text_key == key,
                    TranslationItem.language == "de"
                )
            ).first()
            
            if not translation:
                print(f"Skipping {key} - no German translation found.")
                continue

            text_to_speak = translation.translation_text
            # Clean text slightly (remove brackets, etc.)
            clean_text = text_to_speak.replace("[", "").replace("]", "").replace("...", ".")
            
            # If text is too short or empty, skip
            if not clean_text.strip():
                continue

            print(f"Synthesizing [{key}] ({clean_text[:40]}...)...")
            try:
                chunks = split_text_into_chunks(clean_text)
                audio_bytes = b""
                for chunk in chunks:
                    url_encoded_text = urllib.parse.quote(chunk)
                    tts_url = f"https://translate.google.com/translate_tts?ie=UTF-8&tl=de&client=tw-ob&q={url_encoded_text}"
                    req = urllib.request.Request(
                        tts_url,
                        headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
                    )
                    with urllib.request.urlopen(req, context=ssl_context) as response:
                        audio_bytes += response.read()

                # Delete existing track if any
                old_tracks = session.exec(
                    select(AudioTrack).where(
                        AudioTrack.text_key == key,
                        AudioTrack.language == "de"
                    )
                ).all()
                for ot in old_tracks:
                    session.delete(ot)
                session.commit()

                # Save new track
                at = AudioTrack(
                    text_key=key,
                    language="de",
                    audio_url="placeholder",
                    is_system_default=True,
                    is_shared=True,
                    description=f"System-Audio für {key} (de)",
                    audio_data=audio_bytes
                )
                session.add(at)
                session.commit()
                session.refresh(at)
                
                # Update stream URL
                at.audio_url = f"/api/v1/liturgy/audio-tracks/{at.id}/stream"
                session.add(at)
                session.commit()
                
                count += 1
            except Exception as e:
                print(f"  Error synthesizing {key}: {str(e)}")

        print("=" * 80)
        print(f"COMPLETED: Synthesized {count} German audio tracks and saved to PostgreSQL.")
        print("=" * 80)

if __name__ == "__main__":
    generate_all_tracks()
