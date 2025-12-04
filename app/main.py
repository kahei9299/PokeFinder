from fastapi import FastAPI, HTTPException, Query
from sqlalchemy import text

from db import engine, run_migrations
from pokeapi_client import fetch_pokemon_list

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
    
@app.get("/debug/pokemon/list")
async def debug_pokemon_list(
    limit: int = Query(5, ge=1, le=50),
    offset: int = Query(0, ge=0),
):
    """
    Debug endpoint to verify we can talk to PokeAPI.

    - Accepts limit & offset as query params
    - Calls PokeAPI's /pokemon endpoint
    - Returns a trimmed version of the JSON

    Does not touch our database yet.
    """
    try:
        data = await fetch_pokemon_list(limit=limit, offset=offset)
    except Exception as e:
        # PokeAPI failed or network issue
        raise HTTPException(
            status_code=502,
            detail=f"Failed to fetch from PokeAPI: {e!s}",
        )

    # Return the important bits for inspection
    return {
        "count": data.get("count"),
        "next": data.get("next"),
        "previous": data.get("previous"),
        "results": data.get("results"),
    }