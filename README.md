## Devpost Hackathon Submission
---

## 🛠️ Running Services 

If you prefer to run services separately for development or testing:

```bash
# Start MCP Server
cd sahulat-mcp
uv run uvicorn server:mcp_app.app --host 0.0.0.0 --port 8001

# Start Backend
cd agentic-backend
uv run uvicorn app.main:app --reload --port 8000

# Start Frontend
cd frontend
bun run dev
```

### 📦 Prerequisites

-   🐍 Python 3.12+
-   📦 uv (for Python package management) - [Install uv](https://github.com/astral-sh/uv)
-   📱 Node.js 18+ and bun (for frontend) - [Install bun](https://bun.sh)

> **Note**: Replace Bun commands with npm or yarn if you prefer those package managers.

---

### 2️⃣ Backend (Agentic Backend)

1. **Navigate to the backend directory**:

    ```bash
    cd agentic-backend
    ```

2. **Install dependencies**:

    ```bash
    uv sync
    ```

3. **Set up environment variables**:
   Create a `.env` file with required variables:

    ```bash
    DATABASE_URL=your-database-url
    JWT_SECRET=your-secret-key
    MCP_SERVER_URL=http://localhost:8001  # If running MCP separately
    ```

4. **Run the server**:
    ```bash
    uv run uvicorn app.main:app --reload --port 8000
    ```

The backend will be available at http://127.0.0.1:8000

**API Documentation**: http://127.0.0.1:8000/docs

---

### 3️⃣ Frontend

1. **Navigate to the frontend directory**:

    ```bash
    cd frontend
    ```

2. **Install dependencies**:

    ```bash
    bun install
    # or: npm install
    # or: yarn install
    ```

3. **Set up environment variables**:
   Create a `.env` file:

    ```bash
    VITE_API_URL=http://localhost:8000
    ```

4. **Run the development server**:
    ```bash
    bun run dev
    # or: npm run dev
    # or: yarn dev
    ```

The frontend will be available at http://localhost:3000

---

### Running All Services Individually

To run all three services simultaneously, open three separate terminals:

**Terminal 1 - Backend**:

```bash
cd agentic-backend
uv run uvicorn app.main:app --reload --port 8000
```

**Terminal 2 - Frontend**:

```bash
cd frontend
bun run dev
```

---