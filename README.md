# Todo Full-Stack Application - Backend

A FastAPI backend for the Todo application.

## Setup

```bash
# Create virtual environment
python -m venv venv

# Activate virtual environment
# On Windows:
venv\Scripts\activate

# On Linux/Mac:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Run database migrations
alembic upgrade head

# Start the server
uvicorn src.main:app --reload
```

## API Documentation

Once the server is running, visit:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## Project Structure

```
backend/
├── src/
│   ├── models/       # SQLAlchemy models
│   ├── schemas/      # Pydantic schemas
│   ├── api/          # API endpoints
│   ├── services/     # Business logic
│   └── main.py       # FastAPI app
├── tests/
├── alembic/          # Database migrations
├── requirements.txt
├── requirements-prod.txt  # Production requirements
├── requirements-render.txt # Render-specific requirements
├── Dockerfile           # Docker configuration
├── render.yaml          # Render deployment configuration
├── Procfile             # Railway deployment configuration
├── runtime.txt          # Python version specification
├── .railwayignore       # Railway ignore file
└── .env
```

## Deployment Options

### Railway Deployment
```bash
# Install Railway CLI
npm install -g @railway/cli

# Login and initialize
railway login
railway init

# Set environment variables
railway vars set DATABASE_URL="sqlite:///./todos.db"
railway vars set SECRET_KEY="your-secret-key"

# Deploy
railway up
```

### Render Deployment
1. Create a new Web Service on Render
2. Connect to this GitHub repository
3. Set build command: `pip install -r requirements.txt`
4. Set start command: `uvicorn src.main:app --host 0.0.0.0 --port ${PORT}`
5. Add environment variables as needed

### Hugging Face Spaces (Alternative)
Note: Hugging Face Spaces is primarily for ML demos. For a full backend API, Railway or Render are recommended.

If deploying to Hugging Face Spaces:
1. Create a new Space with Docker option
2. Use the provided Dockerfile
3. Configure environment variables in Space settings

## Environment Variables

Copy `.env.example` to `.env` and configure:

- `DATABASE_URL`: SQLite database URL (e.g., sqlite:///./todos.db)
- `SECRET_KEY`: Secret key for JWT tokens
- `API_V1_PREFIX`: API prefix (default: /api/v1)
- `DEBUG`: Enable debug mode (default: true)
- `ENVIRONMENT`: Set to "production" for production deployments
