"""
Chat Service for the AI Chatbot with Reusable Intelligence
Handles core chat functionality and integrates with other services
"""

from typing import Dict, Any, List, Optional
from datetime import datetime
import uuid
import os
import re
import google.generativeai as genai

from models.message import Message, MessageCreate
from models.conversation import Conversation
from models.task import Task
from services.translation_service import translation_service, Language
from services.voice_processing_service import voice_processing_service
from services.voice_synthesis_service import voice_synthesis_service
from tools.mcp_server import execute_mcp_tool

# Configure the Gemini API
genai.configure(api_key=os.getenv('GEMINI_API_KEY'))
model = genai.GenerativeModel('gemini-pro')


class ChatService:
    """Service class for handling chat operations"""

    def __init__(self):
        pass

    async def process_user_message(
        self,
        message: str,
        conversation_id: Optional[str],
        message_type: str = "text",
        language: str = "en",
        user_preferences: Optional[Dict[str, Any]] = None,
        user_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Process a user message and generate an appropriate response
        """
        # Generate or use conversation ID
        conv_id = conversation_id or str(uuid.uuid4())

        # Handle voice transcripts
        if message_type == "voice_transcript":
            # Process the voice input to clean text and extract intent
            voice_result = await voice_processing_service.process_voice_input(message)

            # Use the cleaned text for further processing
            processed_message = voice_result.cleaned_text
            extracted_intent = voice_result.extracted_intent
            confidence_score = voice_result.confidence_score

            # If confidence is too low, indicate that the voice input wasn't clear
            if confidence_score < 0.3:
                response = "I'm sorry, I couldn't clearly understand your voice input. Could you please repeat or type your message?"

                return {
                    "response": response,
                    "conversation_id": conv_id,
                    "message_id": str(uuid.uuid4()),
                    "language": language,
                    "timestamp": datetime.utcnow().isoformat(),
                    "voice_processing": {
                        "intent": extracted_intent,
                        "confidence": confidence_score,
                        "processing_time": voice_result.processing_time
                    }
                }
        else:
            processed_message = message

        # Determine language for response
        response_language = user_preferences.get('language_preference', language) if user_preferences else language

        # Process translation if needed
        if translation_service.is_urdu_present(processed_message) or response_language == "ur":
            # Translate message to appropriate language for processing
            processed_message, detected_lang = translation_service.translate_message_for_response(
                processed_message, response_language
            )
        else:
            detected_lang = translation_service.detect_language(processed_message)

        # Check if this is a task-related message with enhanced pattern matching
        message_lower = processed_message.lower()
        task_keywords = [
            "task", "kam", "todo", "to do", "to-do", "work", "job", "assignment", "activity", "chore",
            "add", "create", "make", "set up", "include", "put in", "need to", "want to", "should do",
            "list", "show", "display", "view", "see", "what", "all", "my",
            "complete", "done", "finish", "finished", "completed", "mark as done",
            "delete", "remove", "cancel", "eliminate", "get rid of", "hatao", "nikalo",
            "edit", "update", "change", "modify", "adjust", "revise", "improve", "bnana", "shamil",
            "dikhao", "kya hai", "karna", "kar sakta hun", "manage", "organize"
        ]

        # Check for presence of task-related keywords
        is_task_related = any(keyword in message_lower for keyword in task_keywords)

        # Additional check for common task patterns that might not contain direct keywords
        if not is_task_related:
            # Check for patterns like "I need to..." or "I want to..." which often indicate task creation
            pattern_indicators = [
                r'i need to\s+\w+',
                r'i want to\s+\w+',
                r'i have to\s+\w+',
                r'i should\s+\w+',
                r'must\s+\w+',
                r'have to\s+\w+',
                r'got to\s+\w+'
            ]

            for pattern in pattern_indicators:
                if re.search(pattern, message_lower, re.IGNORECASE):
                    is_task_related = True
                    break

        # Generate response based on message content and intent
        # For task-related messages, use the dedicated task handler
        if is_task_related:
            response = await self._handle_task_request(processed_message, conv_id, user_id=user_id)
        else:
            response = await self._generate_response(processed_message, conv_id, extracted_intent if message_type == "voice_transcript" else "text_message")

        # Translate response back to user's preferred language if needed
        if response_language == "ur" and detected_lang == "en":
            response = translation_service.translate_text(response, Language.URDU, Language.ENGLISH)
        elif response_language == "en" and detected_lang == "ur":
            response = translation_service.translate_text(response, Language.ENGLISH, Language.URDU)

        # Create response object
        response_obj = {
            "response": response,
            "conversation_id": conv_id,
            "message_id": str(uuid.uuid4()),
            "language": response_language,
            "timestamp": datetime.utcnow().isoformat()
        }

        # Add voice processing info if this was a voice input
        if message_type == "voice_transcript":
            response_obj["voice_processing"] = {
                "original_message": message,
                "cleaned_text": processed_message,
                "extracted_intent": extracted_intent,
                "confidence": confidence_score,
                "processing_time": voice_result.processing_time
            }

        # Add processed tasks if any
        if is_task_related:
            user_tasks = await self.get_user_tasks(conv_id, user_id=user_id)

            # Format tasks using the task-formatter skill principles
            formatted_tasks = await self.format_tasks_for_display(user_tasks, format_style="list")

            # Include both raw tasks and formatted version
            response_obj["processed_tasks"] = user_tasks
            response_obj["formatted_tasks"] = formatted_tasks

        # Generate voice output if user prefers voice response
        if user_preferences and user_preferences.get('voice_enabled', False):
            try:
                # Generate speech from the response text
                audio_file_path = await voice_synthesis_service.synthesize_speech(
                    text=response,
                    voice_id=user_preferences.get('voice_id', 'MF3mGyEYCl7XYWbV9V6O')  # Default to Adam
                )

                if audio_file_path:
                    response_obj["audio_url"] = f"/api/audio/{os.path.basename(audio_file_path)}"
            except Exception as e:
                print(f"Error generating voice output: {e}")

        return response_obj

    async def _generate_response(self, message: str, conversation_id: str, intent: str = "text_message") -> str:
        """
        Generate an appropriate response based on the message and intent using Gemini API
        """
        message_lower = message.lower()

        # Handle task-related messages
        if "task" in message_lower or "kam" in message_lower:
            return await self._handle_task_request(message, conversation_id)

        # Handle greetings
        elif "hello" in message_lower or "hi" in message_lower or "hey" in message_lower or \
             "ہیلو" in message_lower or "ہائے" in message_lower:
            return "Hello! How can I assist you today?" if not translation_service.is_urdu_present(message) else "ہیلو! آج میں آپ کی کیسے مدد کر سکتا ہوں؟"

        # Handle questions
        elif "?" in message or "kya" in message_lower or "kyun" in message_lower or "kese" in message_lower:
            return "That's a great question! How else can I assist you?" if not translation_service.is_urdu_present(message) else "یہ ایک عمدہ سوال ہے! میں اور کیسے مدد کر سکتا ہوں؟"

        # Use Gemini API for general responses
        else:
            try:
                # Prepare the prompt for Gemini
                prompt = f"You are a helpful AI assistant. Respond to the following message: '{message}'"

                # Generate response using Gemini
                response = model.generate_content(prompt)

                # Extract the text response
                ai_response = response.text if response.text else f"I received your message: '{message}'. How can I help you?"

                # Handle potential encoding issues for multilingual support
                try:
                    ai_response.encode('utf-8').decode('utf-8')
                except UnicodeError:
                    # If there's a Unicode error, fall back to the original message
                    ai_response = f"I received your message: '{message}'. How can I help you?"

                return ai_response
            except Exception as e:
                print(f"Error calling Gemini API: {e}")
                return f"I received your message: '{message}'. How can I help you?"

    async def _handle_task_request(self, message: str, conversation_id: str, user_id: Optional[int] = None) -> str:
        """
        Handle task-related requests in the chat
        """
        import re

        message_lower = message.lower()

        # Enhanced task extraction patterns
        # Extract potential task title from the message with more flexible patterns
        task_title = None

        # Check for add/create task patterns
        add_patterns = [
            r'(?:add|create|make|set up|put in|include|add to list|create for me|need to|want to|would like to)\s+(?:a |the |an |my )?(?:task|kam|work|job|thing|to-do|todo|item)\s+(.+?)(?:\.|!|\?|and|but|please|now|$)',
            r'(?:add|create|make|set up|put in|include|add to list|create for me|need to|want to|would like to)\s+(?:a |the |an |my )?(.+?)(?:\.|!|\?|and|but|please|now|$)',
            r'(?:i need to|i want to|i would like to|i should|must|have to)\s+(.+?)(?:\.|!|\?|and|but|please|now|$)',
            r'(?:task|kam|work|job|thing|to-do|todo|item):\s*(.+?)(?:\.|!|\?|and|but|please|now|$)',
            r'(.+?)\s+(?:needs to be done|should be done|must be done|to be done|on my list|in my tasks|for me|as a task)',
        ]

        if any(keyword in message_lower for keyword in ["add", "create", "shamil", "bnana", "need to", "want to", "i should", "must", "have to", "create for me"]):
            for pattern in add_patterns:
                match = re.search(pattern, message_lower, re.IGNORECASE)
                if match:
                    task_title = match.group(1).strip()
                    # Clean up common words that might be captured incorrectly
                    task_title = re.sub(r'^to\s+', '', task_title)  # Remove leading "to" from "i need to do X"
                    task_title = re.sub(r'\s+$', '', task_title)  # Remove trailing spaces
                    if task_title and len(task_title) > 1:  # Ensure we have a meaningful title
                        break

        # Enhanced task identification patterns for edit/update
        edit_patterns = [
            r'(?:edit|update|change|modify|adjust|revise|improve)\s+(?:task|kam|work|job|item|#?(\d+)|(.+?))\s+(?:to|and|with|by|so that)\s+(.+?)(?:\.|!|\?|$)',
            r'(?:edit|update|change|modify|adjust|revise|improve)\s+(?:task|kam|work|job|item|#?(\d+)|(.+?))',
            r'(?:update|change|modify)\s+(?:the )?(.+?)(?:\s+to|\s+with|\s+and)\s+(.+?)(?:\.|!|\?|$)'
        ]

        # Check for edit/update task patterns
        edit_task_id = None
        edit_field = None
        edit_value = None

        for pattern in edit_patterns:
            match = re.search(pattern, message_lower, re.IGNORECASE)
            if match:
                # Extract the task identifier (could be number or name)
                groups = match.groups()
                if groups[0]:  # Task ID number
                    edit_task_id = groups[0]
                elif groups[1]:  # Task name
                    edit_task_id = groups[1]

                # If there's a third group, it might be the update details
                if len(groups) > 2 and groups[2]:
                    edit_details = groups[2]
                    # Try to extract field and value for update
                    field_pattern = r'(?:status|priority|due date|due|date|title|description)\s+(.+?)(?:\.|!|\?|$)'
                    field_match = re.search(field_pattern, edit_details)
                    if field_match:
                        edit_value = field_match.group(1).strip()

                break

        # Determine the type of task request with enhanced pattern matching
        if any(keyword in message_lower for keyword in ["add", "create", "shamil", "bnana", "need to", "want to", "i should", "must", "have to", "create for me"]):
            if task_title:
                # Create the task with extracted title
                try:
                    new_task = await self.create_task(title=task_title, conversation_id=conversation_id, user_id=user_id)
                    return f"Task '{new_task['title']}' has been added successfully!" if not translation_service.is_urdu_present(message) else f"کام '{new_task['title']}' کامیابی سے شامل کر دیا گیا ہے!"
                except Exception as e:
                    return f"Error adding task: {str(e)}"
            else:
                # If no specific task title found, ask for it
                return "I can help you add a task. What would you like to add?" if not translation_service.is_urdu_present(message) else "میں آپ کے کام شامل کرنے میں مدد کر سکتا ہوں۔ آپ کیا شامل کرنا چاہیں گے؟"

        elif any(keyword in message_lower for keyword in ["list", "show", "dikhao", "kya hai", "what", "display", "view", "see"]):
            # Show existing tasks
            tasks = await self.get_user_tasks(conversation_id, user_id=user_id)
            if tasks:
                # Format tasks using the task-formatter skill
                formatted_tasks = await self.format_tasks_for_display(tasks, format_style="list")
                return f"Here are your tasks:\n\n{formatted_tasks}" if not translation_service.is_urdu_present(message) else f"یہ آپ کے کام ہیں:\n\n{formatted_tasks}"
            else:
                return "You don't have any tasks yet. Would you like to add one?" if not translation_service.is_urdu_present(message) else "آپ کے کوئی کام نہیں ہیں۔ کیا آپ ایک شامل کرنا چاہیں گے؟"

        elif any(keyword in message_lower for keyword in ["complete", "done", "finished", "finish", "hogaya", "khatam", "completed", "marked done"]):
            # Try to identify which task to complete from the message
            # Look for task number or title mentioned in the message
            tasks = await self.get_user_tasks(conversation_id, user_id=user_id)
            if tasks:
                # Look for numbers in the message to identify task
                number_match = re.search(r'#?(\d+)', message_lower)
                if not number_match:
                    number_match = re.search(r'\b(\d+)\b', message_lower)

                if number_match and int(number_match.group(1)) <= len(tasks):
                    task_index = int(number_match.group(1)) - 1
                    target_task = tasks[task_index]

                    try:
                        updated_task = await self.update_task(task_id=target_task['id'], status='completed', user_id=user_id)
                        return f"Task '{updated_task['title']}' has been marked as completed!" if not translation_service.is_urdu_present(message) else f"کام '{updated_task['title']}' کو مکمل کے بطور نشان زد کر دیا گیا ہے!"
                    except Exception as e:
                        return f"Error completing task: {str(e)}"
                else:
                    # Try to match by title if no number found
                    matched_task = None
                    for task in tasks:
                        if task['title'].lower() in message_lower or message_lower in task['title'].lower():
                            matched_task = task
                            break

                    if matched_task:
                        try:
                            updated_task = await self.update_task(task_id=matched_task['id'], status='completed', user_id=user_id)
                            return f"Task '{updated_task['title']}' has been marked as completed!" if not translation_service.is_urdu_present(message) else f"کام '{updated_task['title']}' کو مکمل کے بطور نشان زد کر دیا گیا ہے!"
                        except Exception as e:
                            return f"Error completing task: {str(e)}"
                    else:
                        # If no specific task identified, ask for it
                        return "Which task would you like to mark as complete? Please specify the task number or name." if not translation_service.is_urdu_present(message) else "آپ کون سا کام مکمل کرنا چاہیں گے؟ براہ کرم کام کا نمبر یا نام بتائیں۔"
            else:
                return "You don't have any tasks to complete. Would you like to add one first?" if not translation_service.is_urdu_present(message) else "آپ کے پاس مکمل کرنے کے لیے کوئی کام نہیں ہے۔ کیا آپ پہلے کوئی کام شامل کرنا چاہیں گے؟"

        elif any(keyword in message_lower for keyword in ["delete", "remove", "hatao", "nikalo", "cancel", "eliminate", "get rid of"]):
            # Try to identify which task to delete from the message
            tasks = await self.get_user_tasks(conversation_id, user_id=user_id)
            if tasks:
                # Look for numbers in the message to identify task
                number_match = re.search(r'#?(\d+)', message_lower)
                if not number_match:
                    number_match = re.search(r'\b(\d+)\b', message_lower)

                if number_match and int(number_match.group(1)) <= len(tasks):
                    task_index = int(number_match.group(1)) - 1
                    target_task = tasks[task_index]

                    try:
                        result = await self.delete_task(task_id=target_task['id'], user_id=user_id)
                        return f"Task '{target_task['title']}' has been deleted successfully!" if not translation_service.is_urdu_present(message) else f"کام '{target_task['title']}' کامیابی سے حذف کر دیا گیا ہے!"
                    except Exception as e:
                        return f"Error deleting task: {str(e)}"
                else:
                    # Try to match by title if no number found
                    matched_task = None
                    for task in tasks:
                        if task['title'].lower() in message_lower or message_lower in task['title'].lower():
                            matched_task = task
                            break

                    if matched_task:
                        try:
                            result = await self.delete_task(task_id=matched_task['id'], user_id=user_id)
                            return f"Task '{matched_task['title']}' has been deleted successfully!" if not translation_service.is_urdu_present(message) else f"کام '{matched_task['title']}' کامیابی سے حذف کر دیا گیا ہے!"
                        except Exception as e:
                            return f"Error deleting task: {str(e)}"
                    else:
                        # If no specific task identified, ask for it
                        return "Which task would you like to delete? Please specify the task number or name." if not translation_service.is_urdu_present(message) else "آپ کون سا کام حذف کرنا چاہیں گے؟ براہ کرم کام کا نمبر یا نام بتائیں۔"
            else:
                return "You don't have any tasks to delete. Would you like to add one first?" if not translation_service.is_urdu_present(message) else "آپ کے پاس حذف کرنے کے لیے کوئی کام نہیں ہے۔ کیا آپ پہلے کوئی کام شامل کرنا چاہیں گے؟"

        elif any(keyword in message_lower for keyword in ["edit", "update", "change", "modify", "adjust", "revise", "improve"]):
            # Handle edit/update requests
            tasks = await self.get_user_tasks(conversation_id, user_id=user_id)
            if tasks:
                # Try to identify which task to edit
                number_match = re.search(r'#?(\d+)', message_lower)
                if not number_match:
                    number_match = re.search(r'\b(\d+)\b', message_lower)

                if number_match and int(number_match.group(1)) <= len(tasks):
                    task_index = int(number_match.group(1)) - 1
                    target_task = tasks[task_index]

                    # Extract what needs to be updated
                    update_fields = {}

                    # Check for status updates
                    if any(status in message_lower for status in ['pending', 'in progress', 'completed', 'cancelled']):
                        for status in ['pending', 'in progress', 'completed', 'cancelled']:
                            if status in message_lower:
                                update_fields['status'] = status.replace(' ', '_') if status != 'in progress' else 'in_progress'
                                break

                    # Check for priority updates
                    if any(priority in message_lower for priority in ['low', 'medium', 'high', 'urgent']):
                        for priority in ['low', 'medium', 'high', 'urgent']:
                            if priority in message_lower:
                                update_fields['priority'] = priority
                                break

                    # Check for due date updates
                    date_pattern = r'(\d{4}-\d{2}-\d{2}|\d{1,2}[/-]\d{1,2}[/-]\d{2,4})'
                    date_match = re.search(date_pattern, message_lower)
                    if date_match:
                        update_fields['due_date'] = date_match.group(1)

                    # Check for title updates
                    title_pattern = r'(?:title|name|rename|called|named)\s+(.+?)(?:\.|!|\?|$)'
                    title_match = re.search(title_pattern, message_lower, re.IGNORECASE)
                    if title_match:
                        update_fields['title'] = title_match.group(1).strip()

                    if update_fields:
                        try:
                            updated_task = await self.update_task(task_id=target_task['id'], user_id=user_id, **update_fields)
                            changes_desc = ", ".join([f"{key}: {value}" for key, value in update_fields.items()])
                            return f"Task '{updated_task['title']}' has been updated with: {changes_desc}!" if not translation_service.is_urdu_present(message) else f"کام '{updated_task['title']}' کو اپ ڈیٹ کر دیا گیا ہے: {changes_desc}!"
                        except Exception as e:
                            return f"Error updating task: {str(e)}"
                    else:
                        return "What would you like to update for this task? You can change status, priority, due date, or title." if not translation_service.is_urdu_present(message) else "آپ اس کام کو کیا اپ ڈیٹ کرنا چاہیں گے؟ آپ حالت، ترجیح، تاریخ یا عنوان تبدیل کر سکتے ہیں۔"
                else:
                    # Try to match by title if no number found
                    matched_task = None
                    for task in tasks:
                        if task['title'].lower() in message_lower or message_lower in task['title'].lower():
                            matched_task = task
                            break

                    if matched_task:
                        # Extract what needs to be updated (same logic as above)
                        update_fields = {}

                        # Check for status updates
                        if any(status in message_lower for status in ['pending', 'in progress', 'completed', 'cancelled']):
                            for status in ['pending', 'in progress', 'completed', 'cancelled']:
                                if status in message_lower:
                                    update_fields['status'] = status.replace(' ', '_') if status != 'in progress' else 'in_progress'
                                    break

                        # Check for priority updates
                        if any(priority in message_lower for priority in ['low', 'medium', 'high', 'urgent']):
                            for priority in ['low', 'medium', 'high', 'urgent']:
                                if priority in message_lower:
                                    update_fields['priority'] = priority
                                    break

                        # Check for due date updates
                        date_pattern = r'(\d{4}-\d{2}-\d{2}|\d{1,2}[/-]\d{1,2}[/-]\d{2,4})'
                        date_match = re.search(date_pattern, message_lower)
                        if date_match:
                            update_fields['due_date'] = date_match.group(1)

                        # Check for title updates
                        title_pattern = r'(?:title|name|rename|called|named)\s+(.+?)(?:\.|!|\?|$)'
                        title_match = re.search(title_pattern, message_lower, re.IGNORECASE)
                        if title_match:
                            update_fields['title'] = title_match.group(1).strip()

                        if update_fields:
                            try:
                                updated_task = await self.update_task(task_id=matched_task['id'], user_id=user_id, **update_fields)
                                changes_desc = ", ".join([f"{key}: {value}" for key, value in update_fields.items()])
                                return f"Task '{updated_task['title']}' has been updated with: {changes_desc}!" if not translation_service.is_urdu_present(message) else f"کام '{updated_task['title']}' کو اپ ڈیٹ کر دیا گیا ہے: {changes_desc}!"
                            except Exception as e:
                                return f"Error updating task: {str(e)}"
                        else:
                            return "What would you like to update for this task? You can change status, priority, due date, or title." if not translation_service.is_urdu_present(message) else "آپ اس کام کو کیا اپ ڈیٹ کرنا چاہیں گے؟ آپ حالت، ترجیح، تاریخ یا عنوان تبدیل کر سکتے ہیں۔"
                    else:
                        return "Which task would you like to edit? Please specify the task number or name." if not translation_service.is_urdu_present(message) else "آپ کون سا کام ایڈیٹ کرنا چاہیں گے؟ براہ کرم کام کا نمبر یا نام بتائیں۔"
            else:
                return "You don't have any tasks to edit. Would you like to add one first?" if not translation_service.is_urdu_present(message) else "آپ کے پاس ایڈیٹ کرنے کے لیے کوئی کام نہیں ہے۔ کیا آپ پہلے کوئی کام شامل کرنا چاہیں گے؟"

        else:
            return "I can help you manage your tasks. You can ask me to add, list, complete, delete, or edit tasks." if not translation_service.is_urdu_present(message) else "میں آپ کے کاموں کا نظم کرنے میں مدد کر سکتا ہوں۔ آپ مجھ سے کام شامل کرنے، فہرست دینے، مکمل کرنے، حذف کرنے یا تبدیل کرنے کو کہ سکتے ہیں۔"

    async def create_task(self, title: str, description: Optional[str] = None,
                         status: str = "pending", priority: str = "medium",
                         due_date: Optional[str] = None,
                         conversation_id: Optional[str] = None, user_id: Optional[int] = None) -> Dict[str, Any]:
        """
        Create a new task using MCP tools
        """
        try:
            # Use MCP tools to create task
            result = execute_mcp_tool(
                "add_task",
                title=title,
                description=description,
                status=status,
                priority=priority,
                due_date=due_date,
                conversation_id=conversation_id,
                user_id=user_id
            )

            return result
        except Exception as e:
            raise Exception(f"Error creating task: {str(e)}")

    async def get_user_tasks(self, conversation_id: str, user_id: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        Get user tasks for the conversation
        """
        try:
            # Use MCP tools to fetch tasks
            tasks_data = execute_mcp_tool(
                "list_tasks",
                conversation_id=conversation_id,
                user_id=user_id
            )

            return tasks_data
        except Exception as e:
            raise Exception(f"Error retrieving tasks: {str(e)}")

    async def update_task(self, task_id: str, user_id: Optional[int] = None, **updates) -> Dict[str, Any]:
        """
        Update an existing task using MCP tools
        """
        try:
            # Use MCP tools to update task
            result = execute_mcp_tool(
                "update_task",
                task_id=task_id,
                user_id=user_id,
                **updates
            )

            return result
        except Exception as e:
            raise Exception(f"Error updating task: {str(e)}")

    async def delete_task(self, task_id: str, user_id: Optional[int] = None) -> Dict[str, Any]:
        """
        Delete a task using MCP tools
        """
        try:
            # Use MCP tools to delete task
            result = execute_mcp_tool("delete_task", task_id=task_id, user_id=user_id)

            return result
        except Exception as e:
            raise Exception(f"Error deleting task: {str(e)}")

    async def format_tasks_for_display(self, tasks: List[Dict[str, Any]], format_style: str = "table") -> str:
        """
        Format tasks for display using task-formatter skill principles
        """
        if not tasks:
            return "No tasks found." if format_style != "urdu" else "کوئی کام نہیں ملا۔"

        if format_style == "table":
            # Create a markdown-style table for tasks
            table_lines = [
                "## Your Tasks",
                "| # | Title | Status | Priority | Due Date |",
                "|---|-------|--------|----------|----------|"
            ]

            for idx, task in enumerate(tasks, 1):
                # Add status emoji
                status_emoji = {
                    "pending": "⏳",
                    "in_progress": "🔄",
                    "completed": "✅",
                    "cancelled": "❌"
                }.get(task.get('status', 'pending'), "📋")

                # Add priority indicator
                priority_indicator = {
                    "low": "▶️",
                    "medium": "◆",
                    "high": "⭐",
                    "urgent": "🔥"
                }.get(task.get('priority', 'medium'), "🔹")

                due_date = task.get('due_date', 'None')
                if due_date:
                    # Format the date properly
                    if isinstance(due_date, str):
                        # If it's already a string, just take the date part
                        formatted_date = due_date.split('T')[0] if 'T' in due_date else due_date
                    else:
                        # If it's a datetime object, format it
                        formatted_date = str(due_date).split(' ')[0] if hasattr(due_date, '__str__') else 'None'
                else:
                    formatted_date = 'None'

                table_lines.append(
                    f"| {idx} | {task.get('title', 'Untitled')} | "
                    f"{status_emoji} {task.get('status', 'pending')} | "
                    f"{priority_indicator} {task.get('priority', 'medium')} | "
                    f"{formatted_date} |"
                )

            return "\n".join(table_lines)

        elif format_style == "list":
            # Numbered list format with more details
            task_list = []
            for idx, task in enumerate(tasks, 1):
                status_emoji = {
                    "pending": "⏳",
                    "in_progress": "🔄",
                    "completed": "✅",
                    "cancelled": "❌"
                }.get(task.get('status', 'pending'), "📋")

                priority_indicator = {
                    "low": "▶️",
                    "medium": "◆",
                    "high": "⭐",
                    "urgent": "🔥"
                }.get(task.get('priority', 'medium'), "🔹")

                due_date = task.get('due_date', 'None')
                if due_date:
                    if isinstance(due_date, str):
                        formatted_date = due_date.split('T')[0] if 'T' in due_date else due_date
                    else:
                        formatted_date = str(due_date).split(' ')[0] if hasattr(due_date, '__str__') else 'None'
                else:
                    formatted_date = 'None'

                task_list.append(
                    f"{idx}. {status_emoji} {task.get('title', 'Untitled')} "
                    f"[{priority_indicator} {task.get('priority', 'medium')}] "
                    f"({task.get('status', 'pending')}) - Due: {formatted_date}"
                )

            return "\n".join(task_list)

        elif format_style == "compact":
            # Compact format suitable for voice responses
            if len(tasks) == 0:
                return "You have no tasks."
            elif len(tasks) == 1:
                task = tasks[0]
                return f"You have 1 task: {task.get('title', 'Untitled')}. Status: {task.get('status', 'pending')}."
            else:
                return f"You have {len(tasks)} tasks. Task 1: {tasks[0].get('title', 'Untitled')}. Use 'show tasks' to see the full list."

        else:
            # Simple list format
            task_list = []
            for idx, task in enumerate(tasks, 1):
                task_list.append(f"{idx}. {task.get('title', 'Untitled')} - {task.get('status', 'pending')}")

            return "\n".join(task_list)


# Singleton instance
chat_service = ChatService()


def get_chat_service() -> ChatService:
    """Get the singleton chat service instance"""
    return chat_service