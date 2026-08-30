"""Entry point. Run with `uv run main.py`, or build for the browser with `poe web`."""

import asyncio

import pygame  # noqa: F401  # named here so the browser build preloads it

from planet_protectors.app import run

asyncio.run(run())
