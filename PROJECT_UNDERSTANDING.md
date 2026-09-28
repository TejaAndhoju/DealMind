# DealMind Project Understanding

## Core Architecture
DealMind is a Python-based asynchronous web application designed to demonstrate an "AI Sales Agent" that remembers past interactions and applies them to future deals.

### Components
1. **Frontend (`static/index.html`)**: A responsive, modern SaaS dashboard using vanilla HTML/JS/CSS. It features real-time SSE (Server-Sent Events) streaming for the chat interface, and displays contextual CRM data.
2. **Backend (`app/main.py`)**: A FastAPI application that serves the static UI and exposes REST endpoints (`/api/deals`, `/api/chat`, `/api/save_solution`).
3. **Database (`app/db.py`)**: A lightweight SQLite database (`crm_pro.db`) used to store synthetic CRM data (Deals, Stages, Values, Blockers, Success Reasons, and Transcripts).
4. **AI Engine (`app/engine.py`)**: The orchestrator that:
   - Aggregates CRM context.
   - Queries Vectorize Hindsight (`hindsight_client_api`) for relevant past strategies.
   - Feeds the combined context to an LLM (`openai/gpt-oss-120b` via Groq) to stream a contextualized sales strategy.

### The Learning Loop (Hindsight Integration)
1. **Recall**: When a user asks about a stuck deal, the Engine queries Hindsight using the prospect's "blocker" to find similar past situations.
2. **Reason**: The LLM uses the recalled memory to formulate a strategy.
3. **Retain**: If no memory exists, the LLM invents a novel strategy. The UI presents a "Save to Hindsight" button, allowing the user to push this new strategy to Vectorize. Future queries will then successfully *Recall* this new strategy.

### Data Flow
- **User Input** -> `POST /api/chat` -> `analyze_chat_stream()` -> `search_hindsight()` -> `LLM` -> SSE Stream -> UI
- **Save Solution** -> `POST /api/save_solution` -> `save_novel_solution()` -> `Hindsight API (Retain)`
