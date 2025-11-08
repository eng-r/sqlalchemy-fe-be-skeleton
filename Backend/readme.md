# FastAPI + MariaDB + SQLAlchemy + Minimal Frontend: End‑to‑End Test Guide

This guide explains how to install, configure, and run the complete Employees Demo project — a small yet academically solid example combining a Python FastAPI backend with a static HTML frontend, using MariaDB as a data source.

---

## Prerequisites (Windows Platform)

1. **Install Python 3.14** 
   [Download Python for Windows](https://www.python.org/downloads/windows/) 
   Check “Add Python to PATH” during installation.

2. **Create and activate a virtual environment**
   ```powershell
   python -m venv .venv
   .venv\Scripts\activate
   ```

3. **Install dependencies**
   ```powershell
   pip install -r requirements.txt
   ```

4. **Install MariaDB**
   [MariaDB Official Download](https://mariadb.org/download/) 
   Note your root password and port (e.g. 3306) for later use.

5. **Install HeidiSQL (Database GUI)** 
   [Download HeidiSQL](https://www.heidisql.com/download.php)

6. **Clone and load the Employees Sample DB**
   ```powershell
   git clone https://github.com/datacharmer/test_db.git
   cd test_db
   mariadb.exe -u root -p < employees.sql
   ```

7. **Verify Data**
   Open HeidiSQL, connect to `localhost`, and run:
   ```sql
   SELECT first_name, last_name FROM employees LIMIT 10;
   ```

8. **Run Backend + Frontend**
   ```powershell
   python main.py --host 127.0.0.1 --port 8000 --reload
   ```
   Then open `frontend/index.html` in a browser and click **Load**.

---

## Backend Architecture

### Database Configuration
```powershell
$env:DB_USER="root"
$env:DB_PASS="your_password"
$env:DB_HOST="127.0.0.1"
$env:DB_PORT="3306"
$env:DB_NAME="employees"
```

### Run the API
```powershell
python main.py --host 127.0.0.1 --port 8000 --reload
```
Output should show:
```
INFO:     Uvicorn running on http://127.0.0.1:8000
```

### Test Endpoint
Visit:
```
http://127.0.0.1:8000/employees?limit=10
```
or use `curl`:
```bash
curl http://127.0.0.1:8000/employees?limit=10
```

Expected output (truncated):
```json
[
  {"emp_no": 10001, "first_name": "Georgi", "last_name": "Facello"},
  {"emp_no": 10002, "first_name": "Bezalel", "last_name": "Simmel"}
]
```

---

## Simplest Frontend (HTML UI)

**Path:** `frontend/index.html` 
This minimal HTML file fetches `/employees` via `fetch()` and renders names dynamically.

1. Ensure backend is running on port 8000. 
2. Open the file in any browser. 
3. Press **Load** → 10 employee names appear.

---

## Troubleshooting

| Problem | Cause | Fix |
|----------|--------|-----|
| `IndentationError` | Tabs instead of spaces | Use 4 spaces per indent. |
| `ModuleNotFoundError: app` | Wrong working directory | Run commands inside `backend/`. |
| `Access denied for user` | Incorrect credentials | Update environment vars. |
| `CORS error in browser` | Cross-origin restriction | Ensure `CORS_ORIGINS` in `config.py` includes `*`. |

---

## References

- [FastAPI Documentation](https://fastapi.tiangolo.com/) 
- [SQLAlchemy 2.x ORM Docs](https://docs.sqlalchemy.org/en/20/orm/) 
- [MariaDB Knowledge Base](https://mariadb.com/kb/en/) 
- [Employees Sample DB on GitHub](https://github.com/datacharmer/test_db) 
- [HeidiSQL](https://www.heidisql.com/) 
- [Uvicorn Server Docs](https://www.uvicorn.org/)

---

