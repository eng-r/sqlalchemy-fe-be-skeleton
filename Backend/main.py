from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from app.config import settings
from app.routers import employees, sessions

app = FastAPI(title="Employees API", version="1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

"""
@app.get("/favicon.ico", include_in_schema=False)
async def favicon():
    return Response(status_code=204)  # no content; stops the 404
"""

app.mount("/static", StaticFiles(directory="static"), name="static")


@app.get("/favicon.ico", include_in_schema=False)
async def favicon():
    return FileResponse("static/favicon.ico")


@app.get("/")
async def root():
    return {
        "ok": True,
        "endpoints": [
            "/employees?limit=10&offset=0",
            "/employees/{emp_no}",
            "/employees/{emp_no}/last-name",
            "/sessions/start",
        ],
    }


# Mount routers
app.include_router(employees.router, prefix="/employees", tags=["employees"])
app.include_router(sessions.router, prefix="/sessions", tags=["sessions"])


if __name__ == "__main__":
    # Allow launching as: python main.py --host 127.0.0.1 --port 8000 --reload
    import argparse

    import uvicorn

    parser = argparse.ArgumentParser(description="Run FastAPI server")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8000)
    parser.add_argument("--reload", action="store_true")
    args = parser.parse_args()

    uvicorn.run("main:app", host=args.host, port=args.port, reload=args.reload)
