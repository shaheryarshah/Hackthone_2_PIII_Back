"""
Translation Service for the AI Chatbot with Reusable Intelligence
Handles bidirectional translation between English and Urdu
"""

import re
from typing import Dict, List, Optional, Tuple
from enum import Enum


class Language(str, Enum):
    ENGLISH = "en"
    URDU = "ur"


class TranslationService:
    """Service class for handling translations between English and Urdu"""

    def __init__(self):
        # Basic translation dictionary - in a real implementation, this would connect to a proper translation API
        self.translation_dict = self._load_translation_dictionary()

    def _load_translation_dictionary(self) -> Dict[str, Dict[str, str]]:
        """
        Load basic translation mappings
        In a real implementation, this would load from a database or translation API
        """
        return {
            Language.ENGLISH: {
                "hello": "ہیلو",
                "hi": "ہیلو",
                "goodbye": "الوداع",
                "thank you": "شکریہ",
                "please": "براہ کرم",
                "yes": "جی ہاں",
                "no": "نہیں",
                "how are you": "آپ کیسے ہیں",
                "what is your name": "آپ کا نام کیا ہے",
                "my name is": "میرا نام ہے",
                "task": "کام",
                "add": "شامل کریں",
                "remove": "ہٹا دیں",
                "update": "اپ ڈیٹ",
                "list": "فہرست",
                "complete": "مکمل",
                "pending": "زیر التوا",
                "in progress": "جاري",
                "completed": "مکمل شدہ",
                "cancel": "منسوخ کریں",
                "delete": "حذف کریں",
                "create": "تخلیق کریں",
                "edit": "ترمیم",
                "save": "محفوظ کریں",
                "exit": "باہر نکلیں",
                "help": "مدد",
                "settings": "ترتیبات",
                "profile": "پروفائل",
                "chat": "بات چیت",
                "message": "پیغام",
                "conversation": "بات چیت",
                "user": "صارف",
                "assistant": "مساعد",
                "today": "آج",
                "tomorrow": "کل",
                "yesterday": "گزشتہ روز",
                "week": "ہفتہ",
                "month": "ماہ",
                "year": "سال",
                "time": "وقت",
                "date": "تاریخ",
                "schedule": "شیڈول",
                "reminder": "یاد دہانی",
                "priority": "اہمیت",
                "high": "زیادہ",
                "medium": "درمیانہ",
                "low": "کم",
                "urgent": "فوری",
                "buy groceries": "دودھ، انڈے، روٹی وغیرہ خریدنا",
                "call mom": "ماما کو فون کرنا",
                "finish report": "رپورٹ مکمل کرنا",
                "attend meeting": "میٹنگ میں شرکت کرنا",
                "pay bills": "بلز ادا کرنا",
                "exercise": "ورزش کرنا",
                "read book": "کتاب پڑھنا",
                "learn": "سیکھنا",
                "work": "کام",
                "home": "گھر",
                "office": "دفتر",
                "school": "اسکول",
                "hospital": "ہسپتال",
                "restaurant": "ریستوراں",
                "park": "پارک",
                "market": "مارکیٹ",
                "shop": "دکان",
                "bank": "بینک",
                "post office": "ڈاک خانہ",
                "library": "لائبریری",
                "gym": "جمنازیم",
                "doctor": "ڈاکٹر",
                "teacher": "استاد",
                "engineer": "انجنئر",
                "student": "طلبہ",
                "friend": "دوست",
                "family": "خاندان",
                "important": "اہم",
                "done": "ہو گیا",
                "not done": "نہیں ہوا",
                "to do": "کرنا ہے",
                "todo": "کرنا ہے",
                "task list": "کاموں کی فہرست",
                "things to do": "کرنے کے لیے چیزیں"
            },
            Language.URDU: {
                "ہیلو": "hello",
                "الوداع": "goodbye",
                "شکریہ": "thank you",
                "براہ کرم": "please",
                "جی ہاں": "yes",
                "نہیں": "no",
                "آپ کیسے ہیں": "how are you",
                "آپ کا نام کیا ہے": "what is your name",
                "میرا نام ہے": "my name is",
                "کام": "task",
                "شامل کریں": "add",
                "ہٹا دیں": "remove",
                "اپ ڈیٹ": "update",
                "فہرست": "list",
                "مکمل": "complete",
                "زیر التوا": "pending",
                "جاري": "in progress",
                "مکمل شدہ": "completed",
                "منسوخ کریں": "cancel",
                "حذف کریں": "delete",
                "تخلیق کریں": "create",
                "ترمیم": "edit",
                "محفوظ کریں": "save",
                "باہر نکلیں": "exit",
                "مدد": "help",
                "ترتیبات": "settings",
                "پروفائل": "profile",
                "بات چیت": "chat",
                "پیغام": "message",
                "بات چیت": "conversation",
                "صارف": "user",
                "مساعد": "assistant",
                "آج": "today",
                "کل": "tomorrow",
                "گزشتہ روز": "yesterday",
                "ہفتہ": "week",
                "ماہ": "month",
                "سال": "year",
                "وقت": "time",
                "تاریخ": "date",
                "شیڈول": "schedule",
                "یاد دہانی": "reminder",
                "اہمیت": "priority",
                "زیادہ": "high",
                "درمیانہ": "medium",
                "کم": "low",
                "فوری": "urgent",
                "دودھ، انڈے، روٹی وغیرہ خریدنا": "buy groceries",
                "ماما کو فون کرنا": "call mom",
                "رپورٹ مکمل کرنا": "finish report",
                "میٹنگ میں شرکت کرنا": "attend meeting",
                "بلز ادا کرنا": "pay bills",
                "ورزش کرنا": "exercise",
                "کتاب پڑھنا": "read book",
                "سیکھنا": "learn",
                "کام": "work",
                "گھر": "home",
                "دفتر": "office",
                "اسکول": "school",
                "ہسپتال": "hospital",
                "ریستوراں": "restaurant",
                "پارک": "park",
                "مارکیٹ": "market",
                "دکان": "shop",
                "بینک": "bank",
                "ڈاک خانہ": "post office",
                "لائبریری": "library",
                "جمنازیم": "gym",
                "ڈاکٹر": "doctor",
                "استاد": "teacher",
                "انجنئر": "engineer",
                "طلبہ": "student",
                "دوست": "friend",
                "خاندان": "family",
                "اہم": "important",
                "ہو گیا": "done",
                "نہیں ہوا": "not done",
                "کرنا ہے": "to do",
                "کاموں کی فہرست": "task list",
                "کرنے کے لیے چیزیں": "things to do"
            }
        }

    def translate_text(self, text: str, target_language: Language, source_language: Optional[Language] = None) -> str:
        """
        Translate text from source language to target language
        If source language is not provided, attempts to detect it
        """
        if not text.strip():
            return text

        # Normalize text for comparison
        normalized_text = text.lower().strip()

        # If source language not provided, try to detect it
        if source_language is None:
            source_language = self.detect_language(text)

        # If translating to same language, return original
        if source_language == target_language:
            return text

        # Attempt translation
        if source_language in self.translation_dict:
            # Look for exact matches first
            if normalized_text in self.translation_dict[source_language]:
                return self.translation_dict[source_language][normalized_text]

            # For more complex text, split into words and translate individually
            words = normalized_text.split()
            translated_words = []

            for word in words:
                # Remove punctuation for lookup
                clean_word = re.sub(r'[^\w\s]', '', word).lower()

                if clean_word in self.translation_dict[source_language]:
                    translated_words.append(self.translation_dict[source_language][clean_word])
                else:
                    # If word not found, keep original
                    translated_words.append(word)

            return ' '.join(translated_words)

        return text  # Return original if no translation available

    def detect_language(self, text: str) -> Language:
        """
        Detect the language of the given text
        Uses character-based detection for Urdu/Arabic script
        """
        # Count Arabic/Persian/Urdu characters (Unicode range 0x0600-0x06FF)
        arabic_urdu_chars = sum(1 for c in text if '\u0600' <= c <= '\u06FF')
        total_chars = len([c for c in text if c.isalpha()])

        if total_chars > 0 and arabic_urdu_chars / total_chars > 0.3:
            return Language.URDU
        else:
            return Language.ENGLISH

    def is_urdu_present(self, text: str) -> bool:
        """
        Check if Urdu characters are present in the text
        """
        return any('\u0600' <= c <= '\u06FF' for c in text)

    def translate_message_for_response(self, message: str, user_language_preference: str = "en") -> Tuple[str, str]:
        """
        Translate a message for response considering user language preference
        Returns (translated_message, response_language)
        """
        detected_lang = self.detect_language(message)

        # Determine response language based on user preference and message context
        if user_language_preference == "ur" or self.is_urdu_present(message):
            response_lang = Language.URDU
        else:
            response_lang = Language.ENGLISH

        # Translate if needed
        if detected_lang != response_lang:
            translated = self.translate_text(message, response_lang, detected_lang)
            return translated, response_lang.value
        else:
            return message, detected_lang.value


# Singleton instance
translation_service = TranslationService()


def get_translation_service() -> TranslationService:
    """Get the singleton translation service instance"""
    return translation_service