# NayePankh InsightHub

**AI-Powered NGO Intelligence Platform**

This platform is being developed for the NayePankh Foundation technical internship selection task. It aims to demonstrate Artificial Intelligence, Machine Learning, and Data Analytics capabilities to help NGOs turn data into meaningful insights.

## Current Phase 1 Capabilities
The project is currently in Phase 1: Project Foundation and Workspace Shell. 

Capabilities currently implemented:
- Full-stack monorepo structure (Next.js frontend, FastAPI backend)
- Persistent active workspace selection
- Workspace CRUD operations (Create, Read, Update, Delete)
- Responsive workspace-based application shell with mobile drawer
- Honest placeholders for upcoming modules

## Planned Modules (Future Phases)
- Data Workspace (Upload and mapping)
- Analytics
- Machine Learning
- AI Copilot
- Decision Intelligence
- Reports

*Note: Phase-based development is strictly followed. Modules listed above will be implemented in subsequent phases.*

## Technology Stack
- **Frontend**: Next.js (App Router), TypeScript, Tailwind CSS, TanStack Query, Lucide React
- **Backend**: FastAPI, SQLModel (SQLite), Pydantic, Pytest

## Directory Structure
```
NayePankh InsightHub/
├── frontend/      # Next.js web application
├── backend/       # FastAPI Python application
└── data/          # Local SQLite storage (created at runtime)
```

## Prerequisites
- Node.js (v18+)
- Python (3.10+)

## Setup Instructions

### Backend Setup
1. Navigate to the `backend` directory: `cd backend`
2. Create a virtual environment: `python -m venv venv`
3. Activate the virtual environment:
   - Windows: `venv\Scripts\activate`
   - Mac/Linux: `source venv/bin/activate`
4. Install dependencies: `pip install -r requirements.txt`
5. Copy environment variables: `cp .env.example .env` (adjust if needed)

### Frontend Setup
1. Navigate to the `frontend` directory: `cd frontend`
2. Install dependencies: `npm install`
3. Copy environment variables: `cp .env.example .env.local` (adjust if needed)

## Running the Application

### Start Backend
From the `backend` directory with the virtual environment activated:
```bash
uvicorn app.main:app --reload
```
The API documentation will be available at: http://localhost:8000/docs

### Start Frontend
From the `frontend` directory:
```bash
npm run dev
```
The application will be available at: http://localhost:3000

## Testing
To run backend tests, from the `backend` directory:
```bash
pytest
```

## Current Limitations
- Authentication and multi-user systems are not implemented.
- The project runs on a local SQLite database and is not configured for distributed deployment yet.
