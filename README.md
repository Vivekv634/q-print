# Q-Print

Q-Print is an open-source, local print queue management system designed for university and college campus stationery shops. Students upload their PDF files from a browser, specify print settings, and see their estimated cost — the shop owner manages all incoming jobs from a desktop admin panel and sends them to a physical printer with a single click.

---

## Table of Contents

- [Key Features](#key-features)
- [Tech Stack](#tech-stack)
- [Prerequisites](#prerequisites)
- [Installation](#installation)
- [Running the App](#running-the-app)
- [First-Time Setup](#first-time-setup)
- [Architecture Overview](#architecture-overview)
- [Data Flow](#data-flow)
- [Project Structure](#project-structure)
- [Analytics Dashboard](#analytics-dashboard)
- [Available Commands](#available-commands)
- [Troubleshooting](#troubleshooting)
- [Contributing](#contributing)
- [License](#license)

---

## Key Features

- **Student-facing web app** — Upload PDFs, pick print settings (colour mode, copies, layout, paper size), and see a live cost estimate before submitting.
- **Admin desktop panel** — PySide6 GUI for the shop owner to view the live queue, inspect job details, and dispatch to any connected printer.
- **Automatic queue management** — File changes are watched in real time; jobs enter and leave the queue without any manual refresh.
- **LAN peer discovery** — Shops register themselves on the local network via mDNS so multiple Q-Print instances can discover each other.
- **Windows printing** — Jobs are rendered page-by-page via PyMuPDF and sent directly to a Windows printer through `win32print`.
- **Analytics sync** — Aggregated daily stats are pushed to the Q-Print Analytics cloud so shop owners can track trends over time.

---

## Tech Stack

| Layer                 | Technology                                        |
| --------------------- | ------------------------------------------------- |
| **Admin UI**          | PySide6 6.11 (Qt for Python)                      |
| **Web client**        | Next.js 16, React 19, TypeScript 5                |
| **Styling**           | Tailwind CSS v4, shadcn/ui (Radix), `next-themes` |
| **Python API**        | FastAPI + Uvicorn (port 8000)                     |
| **Database**          | SQLite via `client/data/qprint.db`                |
| **File watching**     | watchdog 6                                        |
| **LAN discovery**     | zeroconf (mDNS)                                   |
| **PDF rendering**     | PyMuPDF 1.27, Pillow 12                           |
| **Windows printing**  | pywin32 (`win32print`)                            |
| **PDF page counting** | pdf-lib (client-side)                             |
| **Validation**        | Zod (client), Pydantic (server)                   |
| **Python**            | 3.12+                                             |
| **Node.js**           | 18+                                               |

> **Platform note:** The web client and admin UI run on any OS. Physical printing (`win32print`) requires **Windows**. Develop on Linux or macOS — just expect the "Print" button to be unavailable.

---

## Prerequisites

Install these before running the setup script:

| Tool    | Minimum version      | Download                          |
| ------- | -------------------- | --------------------------------- |
| Python  | 3.12                 | https://www.python.org/downloads/ |
| Node.js | 18 (LTS recommended) | https://nodejs.org/               |
| npm     | bundled with Node.js | —                                 |
| pywin32 | latest               | Windows only — see below          |

### Windows-only: pywin32

Physical printing requires `pywin32`, which must be installed **manually** after the setup script runs (it is excluded from `requirements.txt` for cross-platform compatibility):

```powershell
server\.venv\Scripts\pip install pywin32
```

---

## Installation

### 1. Clone the repository

```bash
git clone https://github.com/Vivekv634/q-print.git
cd q-print
```

### 2. Run the setup script

```bash
python setup.py
```

This single command:

1. Verifies Python ≥ 3.12 and Node.js ≥ 18 are available.
2. Creates a Python virtual environment at `server/.venv`.
3. Installs all Python dependencies from `server/requirements.txt`.
4. Runs `npm install` inside `client/`.
5. Copies `client/shop_config.example.json` → `client/shop_config.json` (skipped if it already exists).
6. Copies `client/cost.example.json` → `client/public/cost.json` (skipped if it already exists).
7. Creates `client/data/` and `client/data/print_job_file_storage/`.

The script is safe to re-run — every step is idempotent.

### 3. (Windows only) Install pywin32

```powershell
server\.venv\Scripts\pip install pywin32
```

---

## Running the App

### Activate the virtual environment

**Linux / macOS**

```bash
source server/.venv/bin/activate
```

**Windows**

```powershell
server\.venv\Scripts\activate
```

### Start everything

```bash
python main.py
```

`main.py` starts the following in order:

1. Frees port 3000 if something else is using it.
2. Shows the **First-Time Setup dialog** if `shop_config.json` still has placeholder values.
3. Registers the shop on the LAN via mDNS.
4. Starts `PeerDiscovery` — scans for other Q-Print shops on the network.
5. Initialises the `QueueManager` (creates `qprint.db` if missing).
6. Starts the **Python FastAPI server** on port 8000 in a daemon thread.
7. Starts the **Next.js dev server** on port 3000 in a daemon thread.
8. Opens the **Admin Window** (PySide6) on the main thread.

Once running, students open `qprint-<slug>.local:3000` in a browser to submit jobs.

### Ports

| Service           | Port |
| ----------------- | ---- |
| Next.js web app   | 3000 |
| Python API server | 8000 |

---

## First-Time Setup

On the very first launch (or any time `shop_config.json` contains sentinel values), a setup dialog appears asking for:

- **Shop name** — displayed to students in the web app.
- **College / university name** — used for analytics registration.
- **mDNS hostname** — auto-generated as `qprint-<slug>.local`, editable.

These values are saved to `client/shop_config.json`. Edit this file at any time to change the shop identity; the app reads it on each startup.

### Configuring print costs

Open the admin panel → **Settings → Edit Print Cost** to set:

| Setting          | Default | Description                   |
| ---------------- | ------- | ----------------------------- |
| `bw_per_page`    | ₹ 3.00  | Cost per black-and-white page |
| `color_per_page` | ₹ 5.00  | Cost per colour page          |

Values are saved to `client/public/cost.json` and immediately reflected in the student web app cost calculator.

---

## Architecture Overview

### Directory structure

```
q-print/
├── main.py                        # Entry point — orchestrates all components
├── setup.py                       # One-time setup script
├── ip_config.py                   # mDNS registration and shop config helpers
├── port_killer.py                 # Frees port 3000 before starting Next.js
├── launch.sh / launch.bat         # Shell launchers (activate venv + run main.py)
│
├── server/
│   ├── requirements.txt           # Python dependencies
│   ├── logs/app_logs.log          # Runtime log (overwritten each run)
│   ├── src/
│   │   ├── api_server.py          # FastAPI app (port 8000)
│   │   ├── database.py            # SQLite helpers (insert, query, aggregate)
│   │   ├── write_queue.py         # Async write queue — serialises DB writes
│   │   ├── observer.py            # watchdog FileObserver
│   │   ├── queue_manager.py       # QueueManager — thread-safe queue ops
│   │   ├── printer_manager.py     # Windows printing via win32print + PyMuPDF
│   │   ├── peer_discovery.py      # zeroconf browser for other Q-Print shops
│   │   └── analytics_sync.py      # Pushes aggregated stats to analytics cloud
│   ├── ui/
│   │   ├── main_window.py         # AdminWindow (splitter: queue + printer panels)
│   │   └── widgets/
│   │       ├── queue_panel.py     # Live queue table (QFileSystemWatcher)
│   │       ├── printer_panel.py   # Windows printer list with live status
│   │       ├── job_detail_dialog.py  # Full job view + print/cancel actions
│   │       ├── cost_settings_dialog.py  # Edit bw/colour cost per page
│   │       └── setup_dialog.py    # First-run shop identity setup
│   └── utils/
│       └── constants.py           # All path and port constants
│
└── client/                        # Next.js app (App Router)
    ├── app/
    │   ├── page.tsx               # Student-facing upload UI
    │   └── api/jobs/              # API routes (upload, read, delete)
    ├── lib/
    │   └── constants.ts           # USER_ID_LENGTH, FILE_ID_LENGTH
    ├── data/                      # Runtime data — not tracked by git
    │   ├── qprint.db              # SQLite database
    │   ├── print_queue.json       # Current queue snapshot
    │   └── print_job_file_storage/  # Uploaded PDFs
    ├── public/
    │   └── cost.json              # Current print prices
    ├── shop_config.json           # Shop identity — not tracked by git
    └── shop_config.example.json   # Template for setup.py
```

### Component responsibilities

**`api_server.py` (FastAPI, port 8000)**
The Python API receives job submissions from the Next.js API routes, serialises all writes through an async `WriteQueue`, and exposes CRUD endpoints consumed by the admin UI and web client. A `/health` endpoint lets `main.py` wait until the server is ready before continuing startup. A `/shutdown` endpoint drains the write queue before the process exits.

**`database.py` + `write_queue.py`**
All SQLite mutations go through `WriteQueue` — a single-consumer asyncio queue — which ensures writes are serialised even under concurrent HTTP requests. `database.py` provides the raw insert/query/aggregate helpers.

**`observer.py` (watchdog)**
`FileObserver` watches `client/data/` for filesystem events. When it detects that `print_queue.json` has changed it syncs the in-memory queue state and notifies the admin panel.

**`queue_manager.py`**
Thread-safe queue operations protected by `threading.Lock`. Key methods: `add_job`, `remove_job` (user-initiated), `complete_job` (admin print or cancel — deletes files and removes from DB).

**`printer_manager.py`**
Windows-only. Opens a printer DC via `win32print`, iterates `filedataArray`, finds each stored file by `_file_id`, renders every PDF page with `fitz.Matrix` at printer DPI, and blits via `ImageWin.Dib`. Gracefully disabled on Linux/macOS.

**`peer_discovery.py`**
Browses the local network for `_qprint._tcp.local.` service records and writes discovered peers to `client/data/discovered_peers.json`.

**Next.js API routes**

| Route                  | Method | Purpose                                          |
| ---------------------- | ------ | ------------------------------------------------ |
| `/api/jobs/upload`     | POST   | Validate with Zod, store file, enqueue job       |
| `/api/jobs/read_by_id` | POST   | Return job records by ID list                    |
| `/api/jobs/delete`     | DELETE | Remove a record; observer triggers queue cleanup |

### Data types

**`UserType`**: `_id`, `name`, `timestamp`, `position`, `filedataArray`, `estimated_time_of_print`, `completed`

**`FileDataType`**: `_file_id`, `file_name`, `page_count`, `no_of_copies`, `color_mode`, `layout`, `paper_size`, `background_graphics`, `headers_footers`, `margins`

---

## Data Flow

```
Student (browser)
  → uploads PDF, picks settings, sees ₹ cost (pdf-lib counts pages, cost.json prices)
  → POST /api/jobs/upload
        ↓
  client/data/qprint.db  (SQLite)          client/data/print_job_file_storage/
        ↓
  Python FastAPI (port 8000) confirms job queued
        ↓
  print_queue.json updated  →  QueuePanel (QFileSystemWatcher) auto-refreshes

Admin (PySide6 admin panel)
  → double-clicks job  →  JobDetailDialog  →  selects printer  →  Print
        ↓
  PrinterManager.print_job()   (PyMuPDF renders pages → win32print sends to printer)
        ↓
  QueueManager.complete_job()  (removes from DB, deletes uploaded files)

Student delete flow
  → trash icon in browser  →  DELETE /api/jobs/delete
        ↓
  DB record removed  →  QueueManager.remove_job()  (removes from queue + deletes files)
```

---

## Analytics Dashboard

Q-Print ships with built-in analytics sync. Once the shop is registered (automatic on first launch), daily aggregated job stats are pushed to the public analytics service every 5 minutes.

**View analytics dashboard:** [https://qprint-analytics.vercel.app](https://qprint-analytics.vercel.app)

Credentials (`analytics_shop_id` and `analytics_api_key`) are generated automatically on first registration and stored in `client/shop_config.json`. No manual configuration is needed.

To opt out or point to a self-hosted analytics instance, set the environment variable before running:

```bash
export ANALYTICS_CLOUD_URL=""          # disable analytics entirely
export ANALYTICS_CLOUD_URL="https://your-instance.example.com"  # self-hosted
```

---

## Available Commands

### Python (run from repo root with venv active)

| Command           | Description                                      |
| ----------------- | ------------------------------------------------ |
| `python main.py`  | Start the full app (admin UI + API + Next.js)    |
| `python setup.py` | Install all dependencies and create config files |
| `pytest`          | Run the Python test suite                        |

### Next.js (run from `client/`)

| Command         | Description                                          |
| --------------- | ---------------------------------------------------- |
| `npm run dev`   | Start Next.js dev server with Turbopack on port 3000 |
| `npm run build` | Production build                                     |
| `npm run start` | Serve the production build                           |
| `npm run lint`  | Run ESLint                                           |

---

## Troubleshooting

### Port 3000 already in use

`main.py` calls `port_killer.py` automatically to free port 3000 before starting Next.js. If it fails, kill the process manually:

```bash
# Linux / macOS
lsof -ti:3000 | xargs kill -9

# Windows (PowerShell)
netstat -ano | findstr :3000
taskkill /PID <PID> /F
```

### `ModuleNotFoundError` on startup

The virtual environment is not activated. Run:

```bash
source server/.venv/bin/activate   # Linux / macOS
server\.venv\Scripts\activate      # Windows
```

### Printing does nothing on Linux/macOS

Physical printing requires `win32print`, which is Windows-only. The "Print" button in `JobDetailDialog` is intentionally disabled on non-Windows platforms. Use Windows to send jobs to a printer.

### `pywin32` not found on Windows

Install it manually inside the venv:

```powershell
server\.venv\Scripts\pip install pywin32
```

### Next.js fails to start

Ensure `client/node_modules/` exists. If not, run:

```bash
cd client
npm install
```

### Cost not showing in web app

`client/public/cost.json` is missing. Run `python setup.py` again — it will create it from `client/cost.example.json`.

### Shop config dialog keeps appearing

`client/shop_config.json` still contains `__setup_required__` sentinel values. Complete the setup dialog, or manually edit `client/shop_config.json`:

```json
{
  "shop_name": "My Print Shop",
  "mdns_hostname": "qprint-myshop.local",
  "college_name": "My College",
  "analytics_shop_id": "",
  "analytics_api_key": ""
}
```

### Analytics not syncing

Check that the machine has internet access. The sync worker retries every 5 minutes. Logs are written to `server/logs/app_logs.log` (overwritten each run).

---

## Contributing

Contributions are welcome from both developers and shop owners with technical feedback.

1. Fork the repository and create a feature branch.
2. Follow the [Installation](#installation) steps to set up your local environment.
3. Make your changes. Run `pytest` to ensure nothing is broken.
4. Open a pull request with a clear description of what was changed and why.

For bug reports or feature requests, open a GitHub issue.

---

## License

Q-Print is open source. See [LICENSE](LICENSE) for details.
