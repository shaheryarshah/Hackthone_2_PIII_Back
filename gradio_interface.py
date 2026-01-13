"""
Gradio Interface for Todo Backend
This creates a web interface to interact with your Todo backend
"""

import os
import sys
from pathlib import Path

# Add src to path for imports
src_path = Path(__file__).parent / "src"
sys.path.insert(0, str(src_path))

import gradio as gr
import requests
import json
from datetime import datetime
from typing import Dict, List, Optional

# Configuration
BASE_URL = os.getenv("BASE_URL", "http://localhost:8000/api/v1")
API_HEADERS = {"Content-Type": "application/json"}

# Global variable to store auth token
auth_token = None

def set_auth_token(token: str):
    """Set the authentication token globally"""
    global auth_token
    auth_token = token
    API_HEADERS["Authorization"] = f"Bearer {token}"

def register_user(username: str, email: str, password: str) -> str:
    """Register a new user"""
    try:
        response = requests.post(
            f"{BASE_URL}/auth/register",
            headers=API_HEADERS,
            json={
                "username": username,
                "email": email,
                "password": password
            }
        )
        if response.status_code == 200:
            return f"User registered successfully: {response.json().get('username', username)}"
        else:
            return f"Error: {response.status_code} - {response.text}"
    except Exception as e:
        return f"Exception occurred: {str(e)}"

def login_user(username: str, password: str) -> str:
    """Login user and get token"""
    try:
        response = requests.post(
            f"{BASE_URL}/auth/login",
            headers=API_HEADERS,
            data={
                "username": username,
                "password": password
            }
        )
        if response.status_code == 200:
            token_data = response.json()
            token = token_data.get("access_token")
            set_auth_token(token)
            return f"Login successful! Token: {token[:20]}..."
        else:
            return f"Error: {response.status_code} - {response.text}"
    except Exception as e:
        return f"Exception occurred: {str(e)}"

def create_todo(title: str, description: str = "", priority: str = "medium", due_date: str = "") -> str:
    """Create a new todo"""
    global auth_token
    if not auth_token:
        return "Please login first!"

    try:
        todo_data = {
            "title": title,
            "description": description,
            "priority": priority
        }

        if due_date:
            todo_data["due_date"] = due_date

        response = requests.post(
            f"{BASE_URL}/todos",
            headers=API_HEADERS,
            json=todo_data
        )

        if response.status_code == 201:
            todo = response.json()
            return f"Todo created successfully! ID: {todo['id']}, Title: {todo['title']}"
        else:
            return f"Error: {response.status_code} - {response.text}"
    except Exception as e:
        return f"Exception occurred: {str(e)}"

def get_todos(search: str = "", status: str = "", priority: str = "") -> str:
    """Get all todos with optional filters"""
    global auth_token
    if not auth_token:
        return "Please login first!"

    try:
        params = {}
        if search:
            params["search"] = search
        if status:
            params["status"] = status
        if priority:
            params["priority"] = priority

        response = requests.get(
            f"{BASE_URL}/todos",
            headers=API_HEADERS,
            params=params
        )

        if response.status_code == 200:
            data = response.json()
            todos = data.get("todos", [])

            if not todos:
                return "No todos found."

            result = f"Found {len(todos)} todos:\n\n"
            for todo in todos:
                result += f"ID: {todo['id']}, Title: {todo['title']}, "
                result += f"Completed: {todo['completed']}, Priority: {todo['priority']}\n"

            return result
        else:
            return f"Error: {response.status_code} - {response.text}"
    except Exception as e:
        return f"Exception occurred: {str(e)}"

def update_todo(todo_id: int, title: str = "", description: str = "", completed: bool = None) -> str:
    """Update a todo"""
    global auth_token
    if not auth_token:
        return "Please login first!"

    try:
        update_data = {}
        if title:
            update_data["title"] = title
        if description:
            update_data["description"] = description
        if completed is not None:
            update_data["completed"] = completed

        response = requests.put(
            f"{BASE_URL}/todos/{todo_id}",
            headers=API_HEADERS,
            json=update_data
        )

        if response.status_code == 200:
            todo = response.json()
            return f"Todo updated successfully! ID: {todo['id']}, Title: {todo['title']}"
        else:
            return f"Error: {response.status_code} - {response.text}"
    except Exception as e:
        return f"Exception occurred: {str(e)}"

def delete_todo(todo_id: int) -> str:
    """Delete a todo"""
    global auth_token
    if not auth_token:
        return "Please login first!"

    try:
        response = requests.delete(
            f"{BASE_URL}/todos/{todo_id}",
            headers=API_HEADERS
        )

        if response.status_code == 200:
            return f"Todo {todo_id} deleted successfully!"
        else:
            return f"Error: {response.status_code} - {response.text}"
    except Exception as e:
        return f"Exception occurred: {str(e)}"

def mark_todo_complete(todo_id: int) -> str:
    """Mark a todo as complete"""
    global auth_token
    if not auth_token:
        return "Please login first!"

    try:
        response = requests.patch(
            f"{BASE_URL}/todos/{todo_id}/complete",
            headers=API_HEADERS
        )

        if response.status_code == 200:
            data = response.json()
            completed_task = data.get("completed_task", {})
            result = f"Todo {todo_id} marked as complete!\n"
            result += f"Title: {completed_task.get('title', 'N/A')}"

            next_task = data.get("next_task")
            if next_task:
                result += f"\nNext recurring task created: ID {next_task.get('id')}"

            return result
        else:
            return f"Error: {response.status_code} - {response.text}"
    except Exception as e:
        return f"Exception occurred: {str(e)}"

# Create Gradio interface
with gr.Blocks(title="Todo Backend Interface") as demo:
    gr.Markdown("# Todo Backend Interface")
    gr.Markdown("Interact with the Todo backend API through this interface")

    with gr.Row():
        with gr.Column():
            gr.Markdown("## Authentication")
            with gr.Group():
                username_reg = gr.Textbox(label="Username (Register)")
                email_reg = gr.Textbox(label="Email (Register)")
                password_reg = gr.Textbox(label="Password (Register)", type="password")
                register_btn = gr.Button("Register")
                register_output = gr.Textbox(label="Registration Result", interactive=False)

                username_login = gr.Textbox(label="Username (Login)")
                password_login = gr.Textbox(label="Password (Login)", type="password")
                login_btn = gr.Button("Login")
                login_output = gr.Textbox(label="Login Result", interactive=False)

            gr.Markdown("## Create Todo")
            with gr.Group():
                title_create = gr.Textbox(label="Title")
                description_create = gr.Textbox(label="Description")
                priority_create = gr.Dropdown(choices=["low", "medium", "high"], value="medium", label="Priority")
                due_date_create = gr.Textbox(label="Due Date (YYYY-MM-DD)")
                create_btn = gr.Button("Create Todo")
                create_output = gr.Textbox(label="Creation Result", interactive=False)

        with gr.Column():
            gr.Markdown("## Manage Todos")
            with gr.Group():
                search_input = gr.Textbox(label="Search")
                status_input = gr.Dropdown(choices=["", "completed", "pending"], label="Status Filter")
                priority_filter = gr.Dropdown(choices=["", "low", "medium", "high"], label="Priority Filter")
                get_todos_btn = gr.Button("Get Todos")
                todos_output = gr.Textbox(label="Todos List", interactive=False)

            gr.Markdown("## Update/Delete Todo")
            with gr.Group():
                todo_id_update = gr.Number(label="Todo ID to Update/Delete")
                title_update = gr.Textbox(label="New Title (leave blank to keep current)")
                description_update = gr.Textbox(label="New Description (leave blank to keep current)")
                completed_update = gr.Checkbox(label="Mark as Completed")

                with gr.Row():
                    update_btn = gr.Button("Update Todo")
                    delete_btn = gr.Button("Delete Todo")
                    complete_btn = gr.Button("Mark Complete")

                manage_output = gr.Textbox(label="Management Result", interactive=False)

    # Register event handlers
    register_btn.click(register_user, inputs=[username_reg, email_reg, password_reg], outputs=register_output)
    login_btn.click(login_user, inputs=[username_login, password_login], outputs=login_output)
    create_btn.click(create_todo, inputs=[title_create, description_create, priority_create, due_date_create], outputs=create_output)
    get_todos_btn.click(get_todos, inputs=[search_input, status_input, priority_filter], outputs=todos_output)
    update_btn.click(update_todo, inputs=[todo_id_update, title_update, description_update, completed_update], outputs=manage_output)
    delete_btn.click(delete_todo, inputs=[todo_id_update], outputs=manage_output)
    complete_btn.click(mark_todo_complete, inputs=[todo_id_update], outputs=manage_output)

# Run the app
if __name__ == "__main__":
    import uvicorn
    from fastapi import FastAPI

    # Mount the Gradio app
    app = FastAPI()
    app = gr.mount_gradio_app(app, demo, path="/")

    port = int(os.getenv("PORT", 7860))
    print(f"Starting Gradio interface on port {port}")
    print(f"API will connect to: {BASE_URL}")

    # Run with uvicorn
    uvicorn.run(app, host="0.0.0.0", port=port)