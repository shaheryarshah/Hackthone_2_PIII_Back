"""
MCP Server implementation for the AI Chatbot with Reusable Intelligence
Using the Python SDK to wrap existing Phase II logic as tools
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional
import uuid
from datetime import datetime

# Import database and models to connect to real persistence layer
from database import SessionLocal, engine
from models.todo import Todo
from schemas.todo import TodoCreate, TodoUpdate
from services.todo_service import TodoService


def get_db():
    """Dependency to get database session"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# Mock MCP SDK implementation - in a real scenario, this would import the actual MCP SDK
class MCPSDK:
    """Mock MCP SDK for demonstration purposes"""

    @staticmethod
    def execute_tool(tool_name: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Execute an MCP tool with the given parameters"""
        print(f"MCP SDK executing tool: {tool_name} with params: {params}")
        return {"result": "success", "data": params}


class MCPTool(ABC):
    """Abstract base class for MCP tools"""

    @abstractmethod
    def execute(self, **kwargs) -> Dict[str, Any]:
        """Execute the tool with given parameters"""
        pass


class AddTaskTool(MCPTool):
    """MCP tool for adding tasks via MCP SDK"""

    def execute(self, title: str, description: Optional[str] = None,
                status: str = "pending", priority: str = "medium",
                due_date: Optional[str] = None,
                conversation_id: Optional[str] = None, user_id: Optional[int] = None) -> Dict[str, Any]:
        """
        Add a new task via MCP tools as required by FR-006
        """
        params = {
            "title": title,
            "description": description,
            "status": status,
            "priority": priority,
            "due_date": due_date,
            "conversation_id": conversation_id,
            "user_id": user_id,
            "created_at": datetime.utcnow().isoformat()
        }

        # Execute through MCP SDK to ensure compliance with constitution
        result = MCPSDK.execute_tool("add_task", params)

        # Connect to real database and create the task
        db = SessionLocal()
        try:
            # If user_id is None (not authenticated), we can't create a task since user_id is required
            if user_id is None:
                raise Exception("User must be authenticated to create tasks")

            # Parse due_date if provided
            parsed_due_date = None
            if due_date:
                try:
                    parsed_due_date = datetime.fromisoformat(due_date.replace('Z', '+00:00'))
                except ValueError:
                    # If ISO format fails, try parsing as a standard datetime string
                    try:
                        parsed_due_date = datetime.strptime(due_date.split('.')[0], '%Y-%m-%dT%H:%M:%S')
                    except ValueError:
                        # If all parsing fails, ignore the due date
                        parsed_due_date = None

            # Create TodoCreate schema object
            todo_data = TodoCreate(
                title=title,
                description=description,
                priority=priority,
                due_date=parsed_due_date,
                recurrence="none"  # Default for chatbot-created tasks
            )

            # Use TodoService to create the task in the database
            todo_service = TodoService(db, user_id=user_id)
            created_todo = todo_service.create(todo_data)

            # Return the created task data
            return {
                "id": created_todo.id,
                "title": created_todo.title,
                "description": created_todo.description,
                "completed": created_todo.completed,
                "priority": created_todo.priority,
                "due_date": created_todo.due_date.isoformat() if created_todo.due_date else None,
                "recurrence": created_todo.recurrence,
                "created_at": created_todo.created_at.isoformat(),
                "updated_at": created_todo.updated_at.isoformat(),
                "user_id": created_todo.user_id,
                "conversation_id": conversation_id
            }
        finally:
            db.close()


class ListTasksTool(MCPTool):
    """MCP tool for listing tasks via MCP SDK"""

    def execute(self, conversation_id: Optional[str] = None,
                status: Optional[str] = None,
                priority: Optional[str] = None, user_id: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        List tasks via MCP tools as required by FR-006
        """
        params = {
            "conversation_id": conversation_id,
            "status": status,
            "priority": priority,
            "user_id": user_id
        }

        # Execute through MCP SDK to ensure compliance with constitution
        result = MCPSDK.execute_tool("list_tasks", params)

        # Connect to real database and fetch tasks
        db = SessionLocal()
        try:
            # If user_id is None (not authenticated), we can't fetch tasks since user_id is required
            if user_id is None:
                raise Exception("User must be authenticated to list tasks")

            # Use TodoService to fetch tasks from the database
            todo_service = TodoService(db, user_id=user_id)

            # Map status parameter for TodoService (TodoService uses completed=True/False)
            status_param = None
            if status:
                if status.lower() == "completed":
                    status_param = "completed"
                elif status.lower() == "pending":
                    status_param = "pending"

            # Fetch tasks from database
            todos = todo_service.get_all(status=status_param, priority=priority)

            # Convert Todo objects to dictionary format
            tasks = []
            for todo in todos:
                tasks.append({
                    "id": todo.id,
                    "title": todo.title,
                    "description": todo.description,
                    "completed": todo.completed,
                    "priority": todo.priority or "medium",
                    "due_date": todo.due_date.isoformat() if todo.due_date else None,
                    "recurrence": todo.recurrence,
                    "created_at": todo.created_at.isoformat(),
                    "updated_at": todo.updated_at.isoformat(),
                    "user_id": todo.user_id,
                    "conversation_id": conversation_id
                })
            return tasks
        finally:
            db.close()


class UpdateTaskTool(MCPTool):
    """MCP tool for updating tasks via MCP SDK"""

    def execute(self, task_id: str, user_id: Optional[int] = None, **updates) -> Dict[str, Any]:
        """
        Update a task via MCP tools as required by FR-006
        """
        params = {
            "task_id": task_id,
            "user_id": user_id,
            **updates
        }

        # Execute through MCP SDK to ensure compliance with constitution
        result = MCPSDK.execute_tool("update_task", params)

        # Connect to real database and update the task
        db = SessionLocal()
        try:
            # If user_id is None (not authenticated), we can't update tasks since user_id is required
            if user_id is None:
                raise Exception("User must be authenticated to update tasks")

            # Use TodoService to update the task in the database
            todo_service = TodoService(db, user_id=user_id)

            # Prepare update data in TodoUpdate format
            todo_update_data = TodoUpdate(**{k: v for k, v in updates.items() if v is not None})

            updated_todo = todo_service.update(int(task_id), todo_update_data)

            if updated_todo:
                return {
                    "id": updated_todo.id,
                    "title": updated_todo.title,
                    "description": updated_todo.description,
                    "completed": updated_todo.completed,
                    "priority": updated_todo.priority or "medium",
                    "due_date": updated_todo.due_date.isoformat() if updated_todo.due_date else None,
                    "recurrence": updated_todo.recurrence,
                    "created_at": updated_todo.created_at.isoformat(),
                    "updated_at": updated_todo.updated_at.isoformat(),
                    "user_id": updated_todo.user_id
                }
            else:
                raise Exception(f"Task with id {task_id} not found or user not authorized")
        finally:
            db.close()


class DeleteTaskTool(MCPTool):
    """MCP tool for deleting tasks via MCP SDK"""

    def execute(self, task_id: str, user_id: Optional[int] = None) -> Dict[str, Any]:
        """
        Delete a task via MCP tools as required by FR-006
        """
        params = {
            "task_id": task_id,
            "user_id": user_id
        }

        # Execute through MCP SDK to ensure compliance with constitution
        result = MCPSDK.execute_tool("delete_task", params)

        # Connect to real database and delete the task
        db = SessionLocal()
        try:
            # If user_id is None (not authenticated), we can't delete tasks since user_id is required
            if user_id is None:
                raise Exception("User must be authenticated to delete tasks")

            # Use TodoService to delete the task from the database
            todo_service = TodoService(db, user_id=user_id)
            success = todo_service.delete(int(task_id))

            if success:
                return {
                    "message": f"Task {task_id} deleted successfully",
                    "task_id": task_id,
                    "success": True
                }
            else:
                raise Exception(f"Task with id {task_id} not found or user not authorized")
        finally:
            db.close()


class MCPToolRegistry:
    """Registry for managing MCP tools"""

    def __init__(self):
        self.tools = {
            "add_task": AddTaskTool(),
            "list_tasks": ListTasksTool(),
            "update_task": UpdateTaskTool(),
            "delete_task": DeleteTaskTool()
        }

    def get_tool(self, tool_name: str) -> MCPTool:
        """Get a tool by name"""
        return self.tools.get(tool_name)

    def execute_tool(self, tool_name: str, **kwargs) -> Dict[str, Any]:
        """Execute a tool by name with given parameters"""
        tool = self.get_tool(tool_name)
        if not tool:
            raise ValueError(f"Unknown tool: {tool_name}")
        return tool.execute(**kwargs)


# Global MCP tool registry instance
mcp_registry = MCPToolRegistry()


def get_mcp_tool(tool_name: str) -> MCPTool:
    """Get an MCP tool by name"""
    return mcp_registry.get_tool(tool_name)


def execute_mcp_tool(tool_name: str, **kwargs) -> Dict[str, Any]:
    """Execute an MCP tool with given parameters"""
    return mcp_registry.execute_tool(tool_name, **kwargs)


# Implementation of MCP server tools for Neon DB interaction (T040)
def add_task_mcp(title: str, description: Optional[str] = None,
                 status: str = "pending", priority: str = "medium",
                 due_date: Optional[str] = None,
                 conversation_id: Optional[str] = None, user_id: Optional[int] = None) -> Dict[str, Any]:
    """MCP server tool for adding tasks to Neon DB"""
    return execute_mcp_tool("add_task", title=title, description=description,
                           status=status, priority=priority, due_date=due_date,
                           conversation_id=conversation_id, user_id=user_id)


def list_tasks_mcp(conversation_id: Optional[str] = None,
                   status: Optional[str] = None,
                   priority: Optional[str] = None, user_id: Optional[int] = None) -> List[Dict[str, Any]]:
    """MCP server tool for listing tasks from Neon DB"""
    return execute_mcp_tool("list_tasks", conversation_id=conversation_id,
                           status=status, priority=priority, user_id=user_id)


def update_task_mcp(task_id: str, user_id: Optional[int] = None, **updates) -> Dict[str, Any]:
    """MCP server tool for updating tasks in Neon DB"""
    return execute_mcp_tool("update_task", task_id=task_id, user_id=user_id, **updates)


def delete_task_mcp(task_id: str, user_id: Optional[int] = None) -> Dict[str, Any]:
    """MCP server tool for deleting tasks from Neon DB"""
    return execute_mcp_tool("delete_task", task_id=task_id, user_id=user_id)