import asyncio
from random import randint
from typing import AsyncGenerator, AsyncIterable

import aiohttp

# A few handy JSON types
JSON = int | str | float | bool | None | dict[str, "JSON"] | list["JSON"]
JSONObject = dict[str, JSON]
JSONList = list[JSON]


async def http_get(url: str) -> JSONObject:
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            return await response.json()


# The highest Pokemon id
MAX_POKEMON = 898


async def get_pokemon(pokemon_id: int) -> JSONObject:
    pokemon_url = f"https://pokeapi.co/api/v2/pokemon/{pokemon_id}"
    return await http_get(pokemon_url)


async def get_random_pokemon_name() -> str:
    pokemon_id = randint(1, MAX_POKEMON)
    pokemon_url = f"https://pokeapi.co/api/v2/pokemon/{pokemon_id}"
    pokemon = await http_get(pokemon_url)
    return str(pokemon["name"])


async def next_pokemon(total: int) -> AsyncGenerator[str, None]:
    for _ in range(total):
        name = await get_random_pokemon_name()
        yield name


async def main():

    # retrieve the next 10 pokemon names
    async for name in next_pokemon(10):
        print(name)

    # asynchronous list comprehensions
    names = [name async for name in next_pokemon(10)]
    print(names)
    pokemon_id = randint(1, MAX_POKEMON)
    pokemon = await get_pokemon(pokemon_id + 1)
    print(pokemon["name"])


if __name__ == "__main__":
    asyncio.run(main())
