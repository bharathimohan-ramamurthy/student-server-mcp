# Student Records MCP Server

A fully functional **Model Context Protocol (MCP)** server built in Python that manages a student records system. Any MCP-compatible AI client (Claude Desktop, VS Code Copilot, MCP Inspector) can call its tools using natural language.

---

## Table of Contents

1. [What is MCP?](#1-what-is-mcp)
2. [Project Requirements](#2-project-requirements)
3. [System Architecture](#3-system-architecture)
4. [File Structure](#4-file-structure)
5. [Setup and Installation](#5-setup-and-installation)
6. [MCP Transport Types](#6-mcp-transport-types)
7. [Command Reference](#7-command-reference)
8. [MCP Inspector Guide](#8-mcp-inspector-guide)
9. [VS Code Integration](#9-vs-code-integration)
10. [Error Reference](#10-error-reference)
11. [Quick Reference Card](#11-quick-reference-card)

---

## 1. What is MCP?

**MCP (Model Context Protocol)** is an open standard created by Anthropic that allows AI models to call external tools and access data sources in a structured, secure way. Think of it as a universal plugin system for AI — you expose tools over a standard protocol and any compatible AI client can use them.

```
AI Client (Claude / VS Code Copilot)
        │
        │  JSON-RPC over stdio or HTTP
        ▼
MCP Server (server.py)
        │
        │  Python function calls
        ▼
Database Layer (database.py + SQLite)
        │
        ▼
students.db
```

---

## 2. Project Requirements

### Student Attributes
| Field | Type | Notes |
|---|---|---|
| student_id | TEXT | Primary Key |
| name | TEXT | Full name |
| email | TEXT | Unique |
| interests | TEXT | Comma-separated |
| home_location | TEXT | City and country |
| grade | TEXT | A, B+, etc. |

### Course Attributes
| Field | Type | Notes |
|---|---|---|
| course_id | INTEGER | Auto-increment PK |
| name | TEXT | Unique |
| domain | TEXT | technology, science, arts, business |
| term_years | REAL | Duration as decimal |

### Enrollment Attributes (Junction Table)
| Field | Type | Notes |
|---|---|---|
| student_name | TEXT | References student |
| course_name | TEXT | References course |
| enrollment_start | TEXT | Format: YYYY-MM-DD |
| enrollment_end | TEXT | Nullable |
| course_completed | INTEGER | 0 = No, 1 = Yes |

### MCP Tools
| Tool | Purpose |
|---|---|
| `get_student` | Retrieve student by ID |
| `add_student` | Insert new student record |
| `search_student` | Search by name/email/location/interests |
| `enroll_student` | Enroll student in a course (junction table) |
| `courses_available` | List all available courses |
| `add_course` | Insert new course |
| `search_course` | Search courses by name or domain |

---

## 3. System Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    AI CLIENT LAYER                       │
│  Claude Desktop │ VS Code Copilot │ Inspector │ curl    │
└───────────────────────────┬─────────────────────────────┘
                            │
              stdio (local) │ HTTP POST /mcp (network)
                            │
┌───────────────────────────▼─────────────────────────────┐
│                    MCP SERVER LAYER                      │
│     server.py → FastMCP instance → @mcp.tool() handlers │
└───────────────────────────┬─────────────────────────────┘
                            │
                  Python function calls
                            │
┌───────────────────────────▼─────────────────────────────┐
│                  DATABASE ACCESS LAYER                   │
│       database.py → get_connection() → sqlite3 queries  │
└───────────────────────────┬─────────────────────────────┘
                            │
                           SQL
                            │
┌───────────────────────────▼─────────────────────────────┐
│                      DATA LAYER                          │
│        students.db                                       │
│        ├── students                                      │
│        ├── courses                                       │
│        └── student_courses  (junction)                   │
└─────────────────────────────────────────────────────────┘
```

### Database Schema

```sql
CREATE TABLE students (
    student_id    TEXT PRIMARY KEY,
    name          TEXT NOT NULL,
    email         TEXT UNIQUE NOT NULL,
    interests     TEXT,
    home_location TEXT,
    grade         TEXT
);

CREATE TABLE courses (
    course_id   INTEGER PRIMARY KEY AUTOINCREMENT,
    name        TEXT UNIQUE NOT NULL,
    domain      TEXT NOT NULL,
    term_years  REAL NOT NULL
);

CREATE TABLE student_courses (
    id                INTEGER PRIMARY KEY AUTOINCREMENT,
    student_name      TEXT NOT NULL,
    course_name       TEXT NOT NULL,
    enrollment_start  TEXT NOT NULL,
    enrollment_end    TEXT,
    course_completed  INTEGER NOT NULL DEFAULT 0,
    UNIQUE(student_name, course_name)  -- prevents duplicate enrollment
);
```

---

## 4. File Structure

```
student-mcp-server/
├── server.py              # MCP server — FastMCP instance + all 7 tools
├── database.py            # Schema DDL + get_connection() helper
├── seed_data.py           # Dummy data — 5 students, 8 courses, 6 enrollments
├── students.db            # Auto-created SQLite database
├── test_server.py         # Python HTTP test client (handles session ID)
├── cleanup.sh             # Kill stuck MCP ports (macOS/Linux)
├── cleanup.ps1            # Kill stuck MCP ports (Windows)
└── .vscode/
    ├── mcp.json           # VS Code MCP server config
    ├── tasks.json         # VS Code tasks (seed, inspector, cleanup)
    └── launch.json        # Debug configs
```

---

## 5. Setup and Installation

### Step 1 — Create Project and Virtual Environment
```bash
mkdir student-mcp-server
cd student-mcp-server
python -m venv venv

# Activate venv
source venv/bin/activate          # macOS/Linux
venv\Scripts\activate             # Windows
```

### Step 2 — Install Dependencies
```bash
pip install mcp fastmcp uvicorn starlette httpx
pip install "mcp[cli]"    # MCP CLI + Inspector

# Verify
pip show mcp
mcp --version
```

### Step 3 — Seed the Database
```bash
python seed_data.py
# Output: Database seeded successfully.
# Creates students.db with 5 students, 8 courses, 6 enrollments
```

### Step 4 — Run the Server

```bash
# stdio mode (Claude Desktop / VS Code)
python server.py

# Streamable HTTP (auto port detection)
python server.py --transport streamable-http

# Streamable HTTP on specific port
python server.py --transport streamable-http --port 8080
```

---

## 6. MCP Transport Types

| Transport | Code | Best For |
|---|---|---|
| **stdio** | `mcp.run(transport="stdio")` | Local dev, Claude Desktop, VS Code — single client, same machine |
| **SSE** | `mcp.run(transport="sse")` | MCP 1.6.x HTTP — older API, endpoint: `/sse` |
| **Streamable HTTP** | `mcp.run(transport="streamable-http")` | Production, multiple clients, MCP 1.9+, endpoint: `/mcp` |

### Transport Evolution
```
stdio (2024)  →  SSE (2024, deprecated)  →  Streamable HTTP (2025, current)
```

### Streamable HTTP — Session Flow
```
POST /mcp  initialize          →  server creates session
                               ←  mcp-session-id: abc123  (capture this!)

POST /mcp  notifications/initialized
           mcp-session-id: abc123   →  session validated ✅

POST /mcp  tools/call ...
           mcp-session-id: abc123   →  session validated ✅
```

---

## 7. Command Reference

### MCP Inspector Commands
| Command | What It Does |
|---|---|
| `mcp dev server.py` | Launch Inspector UI (port 6274) + Proxy + server.py |
| `mcp --version` | Check installed MCP CLI version |
| `pip install "mcp[cli]"` | Install MCP CLI with Inspector |
| `pip install --upgrade mcp` | Upgrade to latest MCP version |
| `pip show mcp` | Show installed version and details |

### Port Management (macOS/Linux)
```bash
# Kill a specific port
lsof -ti:6274 | xargs kill -9
lsof -ti:6277 | xargs kill -9
lsof -ti:8000 | xargs kill -9

# Kill all MCP ports at once
lsof -ti:6274,6277,3000,8000 | xargs kill -9

# Check if port is free (no output = free)
lsof -i:8000
```

### Port Management (Windows PowerShell)
```powershell
# Find process on port
netstat -ano | findstr :8000

# Kill by PID
taskkill /PID <PID_NUMBER> /F
```

### stdio JSON-RPC Test Commands
Always send `initialize` first, then any tool call.

```bash
# 1. Initialize (always first)
{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2024-11-05","capabilities":{},"clientInfo":{"name":"test","version":"1.0"}}}

# 2. List tools
{"jsonrpc":"2.0","id":2,"method":"tools/list","params":{}}

# 3. get_student
{"jsonrpc":"2.0","id":3,"method":"tools/call","params":{"name":"get_student","arguments":{"student_id":"STU001"}}}

# 4. search_student
{"jsonrpc":"2.0","id":4,"method":"tools/call","params":{"name":"search_student","arguments":{"query":"London"}}}

# 5. courses_available
{"jsonrpc":"2.0","id":5,"method":"tools/call","params":{"name":"courses_available","arguments":{}}}

# 6. search_course
{"jsonrpc":"2.0","id":6,"method":"tools/call","params":{"name":"search_course","arguments":{"query":"science"}}}

# 7. add_student
{"jsonrpc":"2.0","id":7,"method":"tools/call","params":{"name":"add_student","arguments":{"student_id":"STU006","name":"Leo Tan","email":"leo@example.com","interests":"Cloud","home_location":"Singapore","grade":"A"}}}

# 8. enroll_student
{"jsonrpc":"2.0","id":8,"method":"tools/call","params":{"name":"enroll_student","arguments":{"student_name":"Leo Tan","course_name":"Machine Learning 101","enrollment_start":"2025-09-01"}}}
```

### curl Commands for Streamable HTTP
```bash
# Initialize — use -v to see mcp-session-id in response headers
curl -v -X POST http://localhost:8000/mcp \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  -d '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2024-11-05","capabilities":{},"clientInfo":{"name":"curl-test","version":"1.0"}}}'

# All subsequent calls — include session ID
curl -X POST http://localhost:8000/mcp \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  -H "mcp-session-id: <SESSION_ID>" \
  -d '{"jsonrpc":"2.0","id":2,"method":"tools/list","params":{}}'
```

### Python Introspection Commands
```bash
# Check what your MCP version accepts in run()
python -c "from mcp.server.fastmcp import FastMCP; help(FastMCP.run)"

# Check FastMCP constructor parameters
python -c "from mcp.server.fastmcp import FastMCP; help(FastMCP.__init__)"

# Get MCP version
python -c "import mcp; print(mcp.__version__)"

# Get absolute paths for config files
which python          # macOS/Linux
where python          # Windows
realpath server.py    # macOS/Linux
echo %cd%\server.py   # Windows

# Collapse multi-line JSON to single line
echo '{...}' | jq -c .
echo '{...}' | python -m json.tool

# Pretty print compressed JSON response
echo '{...}' | python -m json.tool
```

---

## 8. MCP Inspector Guide

### What Runs When You Type `mcp dev server.py`

```
mcp dev server.py
      │
      ├──► Process 1: Inspector UI     → port 6274  (React web app)
      ├──► Process 2: Proxy Server     → port 6277  (HTTP ↔ stdio bridge)
      └──► Process 3: server.py        → stdin/stdout (spawned on Connect click)
```

### MCP_PROXY_AUTH_TOKEN
- Generated using `secrets.token_hex(32)` — 64 hex chars, 256 bits of randomness
- Embedded in the Inspector URL as `?token=abc123...`
- Sent as `x-mcp-proxy-token` header on every browser→proxy request
- Validated with `hmac.compare_digest()` — constant-time, prevents timing attacks
- Lives only in process memory — never written to disk
- Destroyed on `Ctrl+C` — new token every launch

### Inspector Connection Form
| Field | Value | Notes |
|---|---|---|
| Transport Type | `STDIO` | Use for local dev |
| Command | `/path/to/venv/bin/python` | Must be absolute path |
| Arguments | `/path/to/server.py` | Must be absolute path |
| Environment Vars | `FASTMCP_PORT=8000` | Optional key=value pairs |
| URL (HTTP mode) | `http://localhost:8000/mcp` | For Streamable HTTP transport |

> **Paths with spaces**: Use the Arguments field and wrap the path in double quotes, or move the project to a path without spaces (e.g. `C:\projects\student-mcp-server`).

### How to Capture Raw JSON-RPC
| Method | How To |
|---|---|
| Inspector History Panel | Bottom of the UI — click any entry |
| Browser DevTools Network | F12 → Network → filter `localhost:3000` → Payload/Response tabs |
| Console Fetch Interceptor | Paste JS intercept script in DevTools Console |
| Server-side Log File | Add `logging` to server.py → `tail -f mcp_trace.log` |

---

## 9. VS Code Integration

### Requirements
- VS Code **1.99 or later**
- GitHub Copilot Chat extension installed and signed in

### `.vscode/mcp.json`
```json
{
  "servers": {
    "student-records": {
      "type": "stdio",
      "command": "${workspaceFolder}/venv/bin/python",
      "args": ["${workspaceFolder}/server.py"],
      "env": {}
    }
  }
}
```

> `${workspaceFolder}` resolves to your absolute project path automatically — handles spaces, no hardcoding needed.

**Windows version:**
```json
{
  "servers": {
    "student-records": {
      "type": "stdio",
      "command": "${workspaceFolder}\\venv\\Scripts\\python.exe",
      "args": ["${workspaceFolder}\\server.py"],
      "env": {}
    }
  }
}
```

### How to Use
1. Press `Ctrl+Alt+I` to open Copilot Chat
2. Switch to **Agent** mode at the bottom of the panel
3. Click the tools icon — verify all 7 tools are checked
4. Type natural language — Copilot calls the right tool automatically

### Example Prompts
```
"Get me the details for student STU001"
"Find all students from London"
"Add a new student named Marco Rossi, email marco@example.com, ID STU011, grade B+"
"What courses are available?"
"Show me all science courses"
"Enroll Alice Chen in Data Structures starting 2025-09-01"
"Find all technology courses then enroll Alice in Data Structures"
```

### Verify Connection
```
Ctrl+Shift+P → MCP: List Servers        # should show: student-records  Running
View → Output → MCP: student-records    # raw JSON-RPC logs
Ctrl+Shift+P → MCP: Restart Server      # if stuck
```

---

## 10. Error Reference

### Connection Errors

| Error | Root Cause | Solution |
|---|---|---|
| `Connection Error — proxy token incorrect` | Running `server.py` separately before `mcp dev`, or URL missing `?token=` | Stop `server.py`. Run only: `mcp dev server.py`. Copy full URL from terminal including token |
| `Inspector PORT IS IN USE at localhost:6274` | Terminal closed with X instead of Ctrl+C — process still running | `lsof -ti:6274 \| xargs kill -9` |
| `Proxy Server PORT IS IN USE at port 6277` | Proxy from previous session holding port | `lsof -ti:6274,6277,3000,8000 \| xargs kill -9` |
| `[Errno 48] address already in use (port 8000)` | Previous `python server.py` still running | `lsof -ti:8000 \| xargs kill -9` |

### API / Version Errors

| Error | Root Cause | Solution |
|---|---|---|
| `TypeError: FastMCP.run() got unexpected keyword argument 'host'` | MCP 1.6.x — host/port go in constructor or env vars, not in `run()` | Set `os.environ["FASTMCP_HOST"]` and `FASTMCP_PORT` before `FastMCP()`. Call `mcp.run(transport="streamable-http")` with no other args |
| `mcp command not found` | MCP CLI not installed or venv not activated | `source venv/bin/activate` then `pip install "mcp[cli]"` |

### HTTP / Protocol Errors

| Error | Root Cause | Solution |
|---|---|---|
| `{"error":{"code":-32600,"message":"Not Acceptable: Client must accept both..."}}` | curl missing Accept header — Streamable HTTP requires both MIME types | Add `-H "Accept: application/json, text/event-stream"` to every curl |
| `missing session ID` | Streamable HTTP is stateless — each request needs `mcp-session-id` | Capture `mcp-session-id` from initialize response header (`curl -v`). Send as `-H "mcp-session-id: VALUE"` on all subsequent requests |
| `404 Not Found on http://localhost:8000/` | Root URL has no handler — only `/mcp` exists | Use `http://localhost:8000/mcp` for all requests |
| `405 Method Not Allowed on GET /mcp` | MCP endpoint requires POST — GET is not supported | **This is correct and expected** — confirms endpoint exists. Use POST |
| `Inspector form blank / not pre-filled` | URL opened without query params, or spaces in path broke URL encoding | Use exact URL from terminal. Run: `mcp dev "$(pwd)/server.py"` |

### Data Errors

| Error | Root Cause | Solution |
|---|---|---|
| `UNIQUE constraint failed: student_courses` | Enrolling student in a course they are already enrolled in | Expected behavior — duplicate prevention working. Returns `success: false` |
| `No student found with ID 'STU001'` | Wrong student ID or DB not seeded | Run `python seed_data.py` first |

---

## 11. Quick Reference Card

### All Ports Used
| Port | Service | Kill (macOS/Linux) |
|---|---|---|
| 6274 | MCP Inspector UI | `lsof -ti:6274 \| xargs kill -9` |
| 6277 | MCP Proxy Server | `lsof -ti:6277 \| xargs kill -9` |
| 3000 | MCP Proxy (older) | `lsof -ti:3000 \| xargs kill -9` |
| 8000 | Streamable HTTP | `lsof -ti:8000 \| xargs kill -9` |

### JSON-RPC Message Structure
```json
// Request
{
  "jsonrpc": "2.0",        // always 2.0
  "id": 1,                 // integer — matches response to request
  "method": "tools/call",  // initialize | tools/list | tools/call
  "params": {
    "name": "get_student", // tool name
    "arguments": {         // tool inputs
      "student_id": "STU001"
    }
  }
}

// Response
{
  "jsonrpc": "2.0",
  "id": 1,                 // matches request id
  "result": {
    "content": [{
      "type": "text",
      "text": "{\"student_id\": \"STU001\", ...}"
    }]
  }
}
```

### Dummy Data — Students
| ID | Name | Location | Grade |
|---|---|---|---|
| STU001 | Alice Chen | San Francisco, CA | A |
| STU002 | Bob Martin | Austin, TX | B+ |
| STU003 | Clara Osei | London, UK | A- |
| STU004 | David Kim | Seoul, South Korea | B |
| STU005 | Eva Rossi | Rome, Italy | A+ |

### Dummy Data — Courses
| Name | Domain | Term |
|---|---|---|
| Machine Learning 101 | technology | 1.0 yr |
| Web Development Bootcamp | technology | 0.5 yr |
| Biology Fundamentals | science | 2.0 yr |
| Art History | arts | 1.0 yr |
| Quantum Physics | science | 2.0 yr |
| Music Theory | arts | 1.5 yr |
| Data Structures | technology | 1.0 yr |
| Digital Marketing | business | 0.5 yr |

### Daily Workflow
```bash
# 1. Navigate and activate
cd student-mcp-server
source venv/bin/activate

# 2a. Inspector testing
mcp dev server.py
# Open URL from terminal (includes token), connect, use Tools tab

# 2b. Streamable HTTP testing
python server.py --transport streamable-http
# Inspector: Transport = Streamable HTTP, URL = http://localhost:8000/mcp

# 2c. VS Code — just open chat in Agent mode, server auto-starts

# 3. If ports are stuck
lsof -ti:6274,6277,3000,8000 | xargs kill -9
./cleanup.sh
```

### Transport Comparison
| Factor | stdio | Streamable HTTP |
|---|---|---|
| Claude Desktop | ✅ Required | ❌ Not yet |
| VS Code Copilot | ✅ Yes | ✅ Yes |
| Multiple clients | ❌ One only | ✅ Many |
| Deploy to server | ❌ No | ✅ Yes |
| Session ID needed | ❌ No | ✅ Yes |
| Port required | ❌ No | ✅ Yes (8000) |

---

*Student Records MCP Server — Reference Guide — Built with Python, FastMCP, SQLite*
