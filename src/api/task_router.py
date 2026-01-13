from fastapi import APIRouter, HTTPException, Query
from typing import Optional, List, Dict, Any
import uuid
from datetime import datetime

from models.task import Task, TaskCreate, TaskRead, TaskUpdate
from tools.mcp_server import execute_mcp_tool

router = APIRouter(tags=["tasks"])


@router.get("/tasks", response_model=List[TaskRead])
async def list_tasks(
    conversation_id: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    priority: Optional[str] = Query(None)
):
    """
    List user's tasks with optional filters
    Retrieve all tasks for the current user or conversation
    """
    try:
        # Use MCP tools to fetch tasks
        tasks_data = execute_mcp_tool(
            "list_tasks",
            conversation_id=conversation_id,
            status=status,
            priority=priority
        )

        # In a real implementation, this would convert the MCP result to Task objects
        # For now, returning mock data
        tasks = []
        for i in range(3):  # Mock 3 tasks
            task = TaskRead(
                id=str(uuid.uuid4()),
                title=f"Sample Task {i+1}",
                description="This is a sample task for demonstration",
                status="pending",
                priority="medium",
                due_date=None,
                conversation_id=conversation_id,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow(),
                completed_at=None
            )
            tasks.append(task)

        return tasks
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving tasks: {str(e)}")


@router.post("/tasks", response_model=TaskRead)
async def create_task(task_create: TaskCreate):
    """
    Create a new task via MCP tools
    """
    try:
        # Use MCP tools to create task
        result = execute_mcp_tool(
            "add_task",
            title=task_create.title,
            description=task_create.description,
            status=task_create.status,
            priority=task_create.priority,
            due_date=task_create.due_date.isoformat() if task_create.due_date else None,
            conversation_id=task_create.conversation_id
        )

        # Create task object from result
        new_task = TaskRead(
            id=str(uuid.uuid4()),
            title=task_create.title,
            description=task_create.description,
            status=task_create.status,
            priority=task_create.priority,
            due_date=task_create.due_date,
            conversation_id=task_create.conversation_id,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
            completed_at=None
        )

        return new_task
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error creating task: {str(e)}")


@router.get("/tasks/{task_id}", response_model=TaskRead)
async def get_task(task_id: str):
    """
    Get a specific task by ID
    """
    try:
        # In a real implementation, this would fetch from database via MCP
        # Returning mock data for now
        task = TaskRead(
            id=task_id,
            title="Sample Task Details",
            description="This is a sample task fetched by ID",
            status="pending",
            priority="medium",
            due_date=None,
            conversation_id=None,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
            completed_at=None
        )

        return task
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving task: {str(e)}")


@router.put("/tasks/{task_id}", response_model=TaskRead)
async def update_task(task_id: str, task_update: TaskUpdate):
    """
    Update an existing task via MCP tools
    """
    try:
        # Prepare update data
        update_data = {}
        for field, value in task_update.dict(exclude_unset=True).items():
            if value is not None:
                update_data[field] = value

        # Use MCP tools to update task
        result = execute_mcp_tool(
            "update_task",
            task_id=task_id,
            **update_data
        )

        # Return updated task (mock data for now)
        updated_task = TaskRead(
            id=task_id,
            title=update_data.get('title', f'Sample Task {task_id[:8]}'),
            description=update_data.get('description', 'Updated sample task'),
            status=update_data.get('status', 'pending'),
            priority=update_data.get('priority', 'medium'),
            due_date=update_data.get('due_date'),
            conversation_id=update_data.get('conversation_id'),
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
            completed_at=datetime.utcnow() if update_data.get('status') == 'completed' else None
        )

        return updated_task
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error updating task: {str(e)}")


@router.delete("/tasks/{task_id}")
async def delete_task(task_id: str):
    """
    Delete a task via MCP tools
    """
    try:
        # Use MCP tools to delete task
        result = execute_mcp_tool("delete_task", task_id=task_id)

        # Return success response
        return {"message": f"Task {task_id} deleted successfully", "success": True}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error deleting task: {str(e)}")


# Additional helper endpoints
@router.patch("/tasks/{task_id}/complete")
async def complete_task(task_id: str):
    """
    Mark a task as completed
    """
    try:
        result = execute_mcp_tool("update_task", task_id=task_id, status="completed")
        return {"message": f"Task {task_id} marked as completed", "success": True}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error completing task: {str(e)}")


@router.patch("/tasks/{task_id}/in-progress")
async def mark_task_in_progress(task_id: str):
    """
    Mark a task as in progress
    """
    try:
        result = execute_mcp_tool("update_task", task_id=task_id, status="in_progress")
        return {"message": f"Task {task_id} marked as in progress", "success": True}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error updating task status: {str(e)}")