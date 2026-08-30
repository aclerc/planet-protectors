"""Reading colours back off a surface, for the tests that check what the game drew."""

import pygame

from planet_protectors.tuning import Colour, Point


def colour_at(surface: pygame.Surface, point: Point) -> Colour:
    """Return the RGB colour of one pixel, dropping the alpha channel."""
    red, green, blue, _ = surface.get_at(point)
    return (red, green, blue)
