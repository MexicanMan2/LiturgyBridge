"""
LiturgyBridge Audio Streaming & Capture Service.

This module handles incoming audio capture streams (e.g., chunk buffers sent
via WebSockets from priest or choir microphones) and routes them to speech-to-text
pipelines for translation.
"""

from typing import AsyncGenerator

class AudioStreamService:
    def __init__(self):
        # Dictionary of active audio channel buffers (service_id -> stream_chunks)
        self.active_streams: dict[str, list[bytes]] = {}

    def receive_chunk(self, service_id: str, channel: str, audio_data: bytes):
        """
        Receives binary PCM/Opus audio chunks from a client microphone
        (e.g., priest channel or choir channel) and appends it to the active stream buffer.
        """
        stream_key = f"{service_id}:{channel}"
        if stream_key not in self.active_streams:
            self.active_streams[stream_key] = []
        self.active_streams[stream_key].append(audio_data)

    async def get_stream_generator(self, service_id: str, channel: str) -> AsyncGenerator[bytes, None]:
        """
        Yields accumulated audio chunks as an async generator, allowing
        AI speech-to-text translators to consume the stream in real-time.
        """
        stream_key = f"{service_id}:{channel}"
        if stream_key in self.active_streams:
            for chunk in self.active_streams[stream_key]:
                yield chunk

    def clear_stream(self, service_id: str, channel: str):
        """
        Clears the stream buffer once the sermon/service has ended.
        """
        stream_key = f"{service_id}:{channel}"
        if stream_key in self.active_streams:
            del self.active_streams[stream_key]

audio_stream_service = AudioStreamService()
