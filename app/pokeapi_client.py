import httpx

POKEAPI_BASE_URL = "https://pokeapi.co/api/v2"


async def fetch_pokemon_list(limit: int = 20, offset: int = 0) -> dict:
    """
    Fetch a page of Pokemon from PokeAPI.

    Calls:
        GET https://pokeapi.co/api/v2/pokemon?limit={limit}&offset={offset}

    Returns:
        Parsed JSON as a Python dict.
    """
    url = f"{POKEAPI_BASE_URL}/pokemon"
    params = {"limit": limit, "offset": offset}

    async with httpx.AsyncClient() as client:
        resp = await client.get(url, params=params, timeout=10.0)
        resp.raise_for_status()  # raises if status is 4xx/5xx
        return resp.json()
