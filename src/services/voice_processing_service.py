"""
Voice Processing Service for the AI Chatbot with Reusable Intelligence
Handles the cleaning and intent extraction from raw voice-to-text strings
"""

import asyncio
import json
from typing import Dict, Optional, Tuple
from dataclasses import dataclass
import uuid
from datetime import datetime


@dataclass
class VoiceProcessingResult:
    """Data class for voice processing results"""
    cleaned_text: str
    extracted_intent: str
    confidence_score: float
    processing_time: float
    original_audio_path: Optional[str] = None


class VoiceProcessingService:
    """Service class for processing voice input and extracting intent"""

    def __init__(self):
        # In a real implementation, this would initialize speech recognition models
        # For now, we'll simulate processing
        pass

    async def process_voice_input(self, raw_text: str, audio_path: Optional[str] = None) -> VoiceProcessingResult:
        """
        Process raw voice-to-text input to clean text and extract intent
        """
        start_time = datetime.now()

        # Clean the raw text
        cleaned_text = await self._clean_text(raw_text)

        # Extract intent from the cleaned text
        extracted_intent, confidence_score = await self._extract_intent(cleaned_text)

        end_time = datetime.now()
        processing_time = (end_time - start_time).total_seconds()

        return VoiceProcessingResult(
            cleaned_text=cleaned_text,
            extracted_intent=extracted_intent,
            confidence_score=confidence_score,
            processing_time=processing_time,
            original_audio_path=audio_path
        )

    async def _clean_text(self, raw_text: str) -> str:
        """
        Clean raw voice-to-text output
        Removes filler words, corrects common speech-to-text errors
        """
        # Remove common filler words and normalize
        cleaned = raw_text.lower().strip()

        # Common speech-to-text corrections
        corrections = {
            "umm": "",
            "uh": "",
            "uhh": "",
            "ah": "",
            "like": "",
            "you know": "",
            "right": "",
            "okay": "",
            "so": "",
        }

        for word, replacement in corrections.items():
            cleaned = cleaned.replace(word, replacement)

        # Remove extra whitespace
        cleaned = ' '.join(cleaned.split())

        # Capitalize first letter
        if cleaned:
            cleaned = cleaned[0].upper() + cleaned[1:] if len(cleaned) > 1 else cleaned.upper()

        return cleaned

    async def _extract_intent(self, text: str) -> Tuple[str, float]:
        """
        Extract intent from cleaned text with confidence score
        """
        text_lower = text.lower()

        # Define common intents and their keywords
        intents = {
            "task_add": {
                "keywords": ["add", "create", "make", "new", "task", "kam", "bnao", "shamil"],
                "confidence_boost_keywords": ["add task", "create task", "kam shamil"]
            },
            "task_list": {
                "keywords": ["list", "show", "display", "dikhao", "list karo", "kya hai"],
                "confidence_boost_keywords": ["show tasks", "list tasks", "kam dikhao"]
            },
            "task_complete": {
                "keywords": ["complete", "done", "finish", "hogaya", "ho gaya", "khatam"],
                "confidence_boost_keywords": ["mark done", "complete task", "kam khatam"]
            },
            "task_delete": {
                "keywords": ["delete", "remove", "delete", "hatado", "nikalo", "khatam"],
                "confidence_boost_keywords": ["delete task", "remove task", "kam hatao"]
            },
            "greeting": {
                "keywords": ["hello", "hi", "hey", "helo", "kese ho", "kaia hal", "assalam"],
                "confidence_boost_keywords": ["hello there", "hi there", "helo"]
            },
            "question": {
                "keywords": ["what", "how", "why", "kya", "kese", "kyun", "kaia"],
                "confidence_boost_keywords": ["what is", "how to", "kya hai", "kese"]
            },
            "affirmation": {
                "keywords": ["yes", "yeah", "sure", "jeee", "haan", "jaroor", "ji"],
                "confidence_boost_keywords": ["yes please", "sure thing", "haan ji"]
            },
            "negation": {
                "keywords": ["no", "nope", "nahi", "mat", "mtlb", "nahe", "nai"],
                "confidence_boost_keywords": ["no thanks", "no please", "nahi chahiye"]
            }
        }

        best_intent = "unknown"
        best_confidence = 0.0

        for intent, config in intents.items():
            confidence = 0

            # Score based on regular keywords
            for keyword in config["keywords"]:
                if keyword in text_lower:
                    confidence += 1

            # Boost score for specific phrases
            for phrase in config["confidence_boost_keywords"]:
                if phrase in text_lower:
                    confidence += 2  # Higher weight for specific phrases

            # Calculate confidence as percentage of matched keywords
            if confidence > 0:
                # Normalize based on the length of the input text
                confidence_ratio = min(confidence / len(text_lower.split()), 1.0)
                final_confidence = min(confidence_ratio * 2, 1.0)  # Boost slightly but cap at 1.0

                if final_confidence > best_confidence:
                    best_confidence = final_confidence
                    best_intent = intent

        # Set a minimum confidence threshold
        if best_confidence < 0.1:
            best_intent = "unknown"
            best_confidence = 0.0

        return best_intent, best_confidence

    async def validate_voice_input(self, raw_text: str) -> bool:
        """
        Validate if the voice input is usable
        """
        if not raw_text or len(raw_text.strip()) == 0:
            return False

        # Check if text is just noise or common meaningless phrases
        invalid_phrases = [
            "noise", "background", "static", "garbage", "unintelligible",
            "inaudible", "unclear", "", " ", "\n", "\t"
        ]

        cleaned = raw_text.strip().lower()
        if cleaned in invalid_phrases:
            return False

        # Check if it's mostly repeated characters (indicating poor quality)
        if len(set(cleaned)) < 3 and len(cleaned) > 10:
            return False

        return True


# Singleton instance
voice_processing_service = VoiceProcessingService()


def get_voice_processing_service() -> VoiceProcessingService:
    """Get the singleton voice processing service instance"""
    return voice_processing_service