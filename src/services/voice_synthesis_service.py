"""
Voice Synthesis Service for the AI Chatbot with Reusable Intelligence
Handles converting text to speech using ElevenLabs API
"""

import os
import asyncio
from typing import Optional
import tempfile
import uuid
from pathlib import Path

from elevenlabs.client import ElevenLabs

class VoiceSynthesisService:
    """Service class for synthesizing voice from text using ElevenLabs"""

    def __init__(self):
        self.api_key = os.getenv('ELEVENLABS_API_KEY')
        if not self.api_key:
            raise ValueError("ELEVENLABS_API_KEY environment variable is not set")

        self.client = ElevenLabs(api_key=self.api_key)

    async def synthesize_speech(self, text: str, voice_id: str = "pNwvVoWzOqhGXHaEKhlV", output_format: str = "mp3") -> Optional[str]:
        """
        Synthesize speech from text using ElevenLabs

        Args:
            text: The text to convert to speech
            voice_id: The ElevenLabs voice ID to use (default is Rachel)
            output_format: The audio format to return (mp3, wav, etc.)

        Returns:
            Path to the generated audio file, or None if failed
        """
        try:
            # Generate audio from text
            audio_generator = self.client.text_to_speech.convert(
                voice_id=voice_id,
                output_format="mp3_22050_32",
                text=text,
                model_id="eleven_multilingual_v2"
            )

            # Create a temporary file to save the audio
            temp_dir = Path(tempfile.gettempdir())
            filename = f"voice_output_{uuid.uuid4().hex}.{output_format}"
            filepath = temp_dir / filename

            # Save the audio to the temporary file
            with open(filepath, "wb") as audio_file:
                for chunk in audio_generator:
                    if isinstance(chunk, bytes):
                        audio_file.write(chunk)

            return str(filepath)

        except Exception as e:
            print(f"Error synthesizing speech: {e}")
            return None

    async def get_available_voices(self) -> list:
        """
        Get list of available voices from ElevenLabs
        """
        try:
            response = self.client.voices.get_all()
            return [{"id": voice.voice_id, "name": voice.name, "category": voice.category} for voice in response.voices]
        except Exception as e:
            print(f"Error getting available voices: {e}")
            # Return the default Adam voice which is typically available for all accounts
            # along with some common public voices
            return [
                {"id": "MF3mGyEYCl7XYWbV9V6O", "name": "Adam", "category": "premade"},
                {"id": "pMsXgVXv3BLzKqxLnJCV", "name": "Antoni", "category": "premade"},
                {"id": "FLmXV8g9XGCPRzUJE41J", "name": "Rachel", "category": "premade"},
                {"id": "iP95p4xoKVk5rqxq9ooV", "name": "Josh", "category": "premade"},
                {"id": "VR6AewLTigWG4xSOukaG", "name": "Arnold", "category": "premade"}
            ]

# Singleton instance
voice_synthesis_service = VoiceSynthesisService()

def get_voice_synthesis_service() -> VoiceSynthesisService:
    """Get the singleton voice synthesis service instance"""
    return voice_synthesis_service