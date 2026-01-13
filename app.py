"""
Hugging Face Space Demo for Todo Backend
This is a simplified version suitable for Hugging Face Spaces
"""

import os
import gradio as gr
from fastapi import FastAPI
from contextlib import asynccontextmanager
from src.database import get_db, engine, Base
from src.models.todo import Todo
from src.models.user import User
from src.schemas.todo import TodoCreate, TodoUpdate, TodoResponse, TodoListResponse
from src.services.todo_service import TodoService
from src.middleware.auth import get_current_user
from src.api.routes.auth import router as auth_router
from src.api.chat_router import router as chat_router
from src.api.task_router import router as task_router
from sqlalchemy.orm import Session
from datetime import datetime
from typing import Optional

# Initialize database
@asynccontextmanager
def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)
    yield

# Create FastAPI app
app = FastAPI(lifespan=lifespan)

# Include routers
app.include_router(auth_router, prefix="/api/v1")
app.include_router(chat_router)
app.include_router(task_router, prefix="/api/v1")

def demo_get_todos():
    """Simple demo function to show todos"""
    try:
        # This is a simplified version for demo purposes
        db_gen = get_db()
        db = next(db_gen)

        # For demo, just return a sample response
        sample_todos = [
            {"id": 1, "title": "Sample Todo", "completed": False},
            {"id": 2, "title": "Another Sample Todo", "completed": True}
        ]

        db.close()
        return str(sample_todos)
    except Exception as e:
        return f"Error: {str(e)}"

def demo_create_todo(title: str, description: str = ""):
    """Demo function to create a todo"""
    try:
        return f"Created todo: '{title}' with description: '{description}'"
    except Exception as e:
        return f"Error: {str(e)}"

# Create Gradio interface
with gr.Blocks(title="Todo Backend Demo") as demo:
    gr.Markdown("# Todo Backend Demo")
    gr.Markdown("This is a demo interface for the Todo backend API")

    with gr.Tab("View Todos"):
        gr.Button("Get Todos").click(demo_get_todos, outputs=gr.Textbox(label="Todos"))

    with gr.Tab("Create Todo"):
        title_input = gr.Textbox(label="Title")
        desc_input = gr.Textbox(label="Description")
        create_btn = gr.Button("Create Todo")
        create_output = gr.Textbox(label="Result")
        create_btn.click(demo_create_todo, inputs=[title_input, desc_input], outputs=create_output)

# Mount the Gradio app
app = gr.mount_gradio_app(app, demo, path="/")

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 7860))
    uvicorn.run(app, host="0.0.0.0", port=port)