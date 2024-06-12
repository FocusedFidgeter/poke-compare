# -----------------------------------------------------------------------------
# Project:     Final Project
# Author:      Paul Devey
# Date:        2024-06-12
# Description: This is the main application file for the Final Project.
#              - it implements type hints, dataclasses, iterators, generators and async/await
#              - it retrieves the Pokemon's name, height, and weight from the PokeAPI
#              - percentile calculations are performed on the Pokemon's height and weight
#              - then saved in the Pokemon's dataclass object as properties
#              - data analysis is performed on the Pokemon's data, and stored in a CSV file
#              - the Pokemon's data is retrieved by the user from the CSV file and displayed
# -----------------------------------------------------------------------------


import logging
import sys
import asyncio
import aiohttp
import aiofiles
import pandas as pd
import numpy as np
from scipy import stats
from dataclasses import dataclass, field
from typing import List, Iterator


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)


# The highest Pokemon id
MAX_POKEMON = 898


# TODO: set up iterators to collect heights and weights of Pokemon
# TODO: perform percentile calculations using itertools


def set_pokemon_entrypoint(poke_id: int) -> str:
    """
    Set the entrypoint for the pokemon API.

    Args:
        poke_id (int): The ID of the Pokemon.

    Returns:
        str: The URL of the Pokemon API endpoint.
    """
    return f"https://pokeapi.co/api/v2/pokemon/{poke_id}/"


@dataclass
class Pokemon:
    _poke_id: int
    _name: str
    _height: float
    _weight: float
    _url: str = field(init=False)

    def __init__(self, poke_id: int, name: str, height: float, weight: float):
        self._poke_id = poke_id
        self._name = name
        self._height = height
        self._weight = weight
        self._height_percentile = None
        self._weight_percentile = None

    def __post_init__(self):
        self._url = set_pokemon_entrypoint(self._poke_id)

    @property
    def poke_id(self) -> int:
        return self._poke_id

    @property
    def name(self) -> str:
        return self._name

    @property
    def height(self) -> float:
        return self._height

    @property
    def weight(self) -> float:
        return self._weight

    @property
    def height_percentile(self):
        return self._height_percentile

    @height_percentile.setter
    def height_percentile(self, value: float):
        self._height_percentile = value

    @property
    def weight_percentile(self):
        return self._weight_percentile

    @weight_percentile.setter
    def weight_percentile(self, value: float):
        self._weight_percentile = value


@dataclass
class PokemonList:
    _pokemons: List[Pokemon]

    def __iter__(self):
        self._index = 0
        return self

    def __next__(self):
        if self._index < len(self._pokemons):
            result = self._pokemons[self._index]
            self._index += 1
            return result
        else:
            raise StopIteration

    def heights(self) -> Iterator[float]:
        for pokemon in self._pokemons:
            yield pokemon.height

    def weights(self) -> Iterator[float]:
        for pokemon in self._pokemons:
            yield pokemon.weight


async def get_pokemon(pokemon_id: int) -> Pokemon:
    logging.info(f"Retrieving Pokemon with ID {pokemon_id}")
    pokemon_url = f"https://pokeapi.co/api/v2/pokemon/{pokemon_id}"
    async with aiohttp.ClientSession() as session:
        async with session.get(pokemon_url) as response:
            data = await response.json()
            return Pokemon(data["id"], data["name"], data["height"], data["weight"])


async def get_pokemon_list() -> PokemonList:
    """
    Asynchronously retrieves a list of Pokemon objects from the PokeAPI.

    Returns:
        PokemonList: A list of Pokemon objects.
    """
    logging.info("Retrieving Pokemon list")
    pokemon_list: List[Pokemon] = []
    async with aiohttp.ClientSession() as session:
        for pokemon_id in range(1, MAX_POKEMON + 1):
            pokemon_url = f"https://pokeapi.co/api/v2/pokemon/{pokemon_id}"
            async with session.get(pokemon_url) as response:
                data = await response.json()
                logging.info(
                    f"Retrieved Pokemon with ID {data['id']}; name: {data['name']}"
                )
                pokemon_list.append(
                    Pokemon(data["id"], data["name"], data["height"], data["weight"])
                )
    return PokemonList(pokemon_list)


def calculate_percentile(data: List[float], value: float) -> float:
    return float(stats.percentileofscore(data, value))


def calculate_statistics(data: List[float]) -> dict[str, float]:
    return {
        "mean": float(np.mean(data)),
        "median": float(np.median(data)),
        "std_dev": float(np.std(data)),
        "variance": float(np.var(data)),
    }


async def analyze_pokemon_data(pokemon_list: PokemonList):
    heights = list(pokemon_list.heights())
    weights = list(pokemon_list.weights())

    height_stats = calculate_statistics(heights)
    weight_stats = calculate_statistics(weights)

    for pokemon in pokemon_list:
        pokemon.height_percentile = calculate_percentile(heights, pokemon.height)
        pokemon.weight_percentile = calculate_percentile(weights, pokemon.weight)

    # Save to percentiles.csv
    async with aiofiles.open("percentiles.csv", "w") as f:
        await f.write("poke_id,height_percentile,weight_percentile\n")
        for pokemon in pokemon_list:
            await f.write(
                f"{pokemon.poke_id},{pokemon.height_percentile},{pokemon.weight_percentile}\n"
            )


async def read_pokemon_from_csv() -> PokemonList:
    df = pd.read_csv("pokemon.csv")
    pokemons = [
        Pokemon(row["poke_id"], row["name"], row["height"], row["weight"])
        for index, row in df.iterrows()
    ]
    return PokemonList(pokemons)


async def save_pokemon_to_csv(pokemon: Pokemon) -> None:
    """
    Asynchronously saves a Pokemon object to a CSV file.

    Args:
        pokemon (Pokemon): The Pokemon object to be saved.

    Returns:
        None
    """
    logging.info("Saving Pokemon to CSV")
    async with aiofiles.open("pokemon.csv", "a") as f:
        await f.write(
            f"{pokemon.poke_id},{pokemon.name},{pokemon.height},{pokemon.weight}\n"
        )


async def save_all_pokemon_to_csv(pokemon_list: PokemonList) -> None:
    """
    Saves all Pokemon objects in a list to a CSV file.

    Args:
        pokemon_list (PokemonList): A list of Pokemon objects.

    Returns:
        None
    """
    logging.info("Saving all Pokemon to CSV")
    async with aiofiles.open("pokemon.csv", "w") as f:
        for pokemon in pokemon_list:
            await f.write(
                f"{pokemon.poke_id},{pokemon.name},{pokemon.height},{pokemon.weight}\n"
            )


async def display_pokemon(pokemon_id: int) -> None:
    df = pd.read_csv("percentiles.csv")
    pokemon = df[df["poke_id"] == pokemon_id]
    if not pokemon.empty:
        print(pokemon)
    else:
        print(f"Pokemon with ID {pokemon_id} not found.")


async def main() -> None:
    logging.info("Starting the main function")
    pokemon_list: PokemonList = await get_pokemon_list()
    # await save_all_pokemon_to_csv(pokemon_list)

    # Everything above this works -------------------------------------------------

    # Perform data analysis
    await analyze_pokemon_data(pokemon_list)

    # Display a Pokemon's data
    await display_pokemon(1)  # Example: display data for Pokemon with ID 1
    await display_pokemon(1000)  # Error Example: display data for Pokemon with ID 1000

    logging.info("Finished the main function")


if __name__ == "__main__":
    asyncio.run(main())
