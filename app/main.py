import asyncio
import httpx

from fastapi import FastAPI, HTTPException, Query, Depends
from sqlalchemy import text, delete
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.dialects.postgresql import insert as pg_insert

from db import engine, run_migrations, get_db
from pokeapi_client import fetch_pokemon_list, fetch_pokemon_details
from models import Pokemon, PokemonType

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
    
@app.get("/pokemon/save")
async def save_pokemon(
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
):
    """
    Fetches Pokemon data from PokeAPI and saves them to the PostgreSQL database.

    - Uses limit & offset to control how many Pokemon to fetch.
    - For each listed Pokemon, fetches detailed info.
    - Upserts into 'pokemon' table.
    - Replaces associated rows in 'pokemon_types' table.
    """
    # Step 1: fetch list from PokeAPI
    try:
        list_data = await fetch_pokemon_list(limit=limit, offset=offset)
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to fetch Pokemon list from PokeAPI: {e!s}",
        )

    results = list_data.get("results", [])
    if not results:
        return {
            "message": "Successfully saved Pokemon to database",
            "saved_count": 0,
            "offset": offset,
            "limit": limit,
        }

    # Step 2: concurrently fetch details using a shared AsyncClient
    async with httpx.AsyncClient() as client:
        tasks = [
            fetch_pokemon_details(client, item["url"])
            for item in results
            if "url" in item
        ]
        details_list = await asyncio.gather(*tasks)

    saved_count = 0

    # Step 3: for each detail, upsert into DB
    for details in details_list:
        if details is None:
            continue

        pokemon_id = details.get("id")
        name = details.get("name")
        base_experience = details.get("base_experience")
        height = details.get("height")
        order_value = details.get("order")
        weight = details.get("weight")
        location_area_encounters = details.get("location_area_encounters")
        types = details.get("types", [])

        if pokemon_id is None or name is None:
            # Skip malformed entries
            continue

        # Upsert into pokemon table using PostgreSQL's ON CONFLICT
        stmt = pg_insert(Pokemon).values(
            pokemon_id=pokemon_id,
            name=name,
            base_experience=base_experience,
            height=height,
            order=order_value,
            weight=weight,
            location_area_encounters=location_area_encounters,
        )
        stmt = stmt.on_conflict_do_update(
            index_elements=[Pokemon.pokemon_id],
            set_={
                "name": name,
                "base_experience": base_experience,
                "height": height,
                "order": order_value,
                "weight": weight,
                "location_area_encounters": location_area_encounters,
            },
        )
        await db.execute(stmt)

        # Replace types for this Pokemon
        await db.execute(
            delete(PokemonType).where(PokemonType.pokemon_id == pokemon_id)
        )
        for entry in types:
            t = entry.get("type", {})
            type_name = t.get("name")
            type_url = t.get("url")
            if type_name and type_url:
                await db.execute(
                    PokemonType.__table__.insert().values(
                        pokemon_id=pokemon_id,
                        type_name=type_name,
                        type_url=type_url,
                    )
                )

        saved_count += 1

    # Step 4: commit once for the whole batch
    await db.commit()

    return {
        "message": "Successfully saved Pokemon to database",
        "saved_count": saved_count,
        "offset": offset,
        "limit": limit,
    }
