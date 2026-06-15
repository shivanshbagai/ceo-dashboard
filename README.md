# CEO Dashboard
The CEO Dashboard is a full-stack web application designed to give executives immediate insights into their business performance. It combines a modern, responsive user interface with an AI-powered backend, allowing users to query their using natural language and receive automated executive briefings.
## Features
- **Natural Language Data Querying**: Ask questions about business performance, employee headcounts, or project metrics in plain English, and the system translates them into SQL to fetch real-time answers.
- **Executive Briefings**: Automatically generates concise, weekly AI summaries highlighting macro trends, operational risks, and strategic recommendations based on the latest data.
- **KPI Tracking**: View top-level metrics such as revenue, MRR, pipeline, and customer satisfaction scores at a glance.
- **Interactive Visualizations**: Clean, responsive charts for tracking historical performance.
## Technology Stack
**Frontend:**
- React (bootstrapped with Vite)
- Chakra UI for component styling
- Recharts for data visualization
- Framer Motion for animations
- Lucide React for iconography
**Backend:**
- Python with FastAPI
- SQLite for the local data warehouse
- Pandas for data manipulation
- OpenRouter / Google Gemini for Large Language Model (LLM) capabilities
## Project Structure
The repository is divided into two main sections:
- `backend/`: Contains the FastAPI application, database files, and data processing scripts.
- `frontend/`: Contains the React application, routing, and UI components.
## Getting Started
Follow these steps to set up the project locally.
### Prerequisites
- Node.js
- Python 3
### Backend Setup
1. Navigate to the backend directory:
   cd backend
2. Create and activate a virtual environment:
   python -m venv venv
   source venv/bin/activate
3. Install the required Python packages:
   pip install -r requirements.txt
4. Create a `.env` file in the backend directory and add your API keys. You will need to provide an API key for the LLM integration.
### Frontend Setup
1. Navigate to the frontend directory:
   cd frontend
2. Install the Node dependencies:
   npm install
## Running the Application
You can start both the frontend and backend servers simultaneously from the frontend directory.
1. Ensure your backend virtual environment is created (the start script expects it at `backend/venv`).
2. From the `frontend` directory, run:
   npm start
This command launches the FastAPI server and the Vite development server concurrently. Navigate to the local URL provided in your terminal to view the dashboard.
