from fastapi import FastAPI
from sqlalchemy import text

from db import engine, run_migrations

app = FastAPI(title="Tokka Intern Pokemon Service")


@app.on_event("startup")
async def on_startup():
    """
    Application startup hook.

    This runs before the app starts serving requests.
    use it to run simple database migrations.
    """
    await run_migrations()


@app.get("/health")
async def health_check():
    """
    Health endpoint.

    Checks:
    - App is running
    - Database is reachable (simple SELECT 1)
    """
    try:
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
        db_status = "connected"
    except Exception as e:
        db_status = f"error: {e!s}"

    return {
        "status": "ok",
        "db": db_status,
    }
