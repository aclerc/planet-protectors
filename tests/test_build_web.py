from scripts.build_web import missing_preloads, top_level_imports


class TestTopLevelImports:
    @staticmethod
    def test_finds_plain_imports() -> None:
        assert top_level_imports("import math\nimport pygame\n") == {"math", "pygame"}

    @staticmethod
    def test_reduces_a_dotted_import_to_its_top_level_package() -> None:
        assert top_level_imports("import os.path\n") == {"os"}

    @staticmethod
    def test_finds_from_imports() -> None:
        assert top_level_imports("from pygame.draw import circle\n") == {"pygame"}

    @staticmethod
    def test_ignores_relative_imports() -> None:
        assert top_level_imports("from . import sibling\n") == set()


class TestMissingPreloads:
    @staticmethod
    def test_nothing_missing_when_the_entry_point_names_every_dependency() -> None:
        assert missing_preloads("import pygame", package_sources=["import pygame"]) == set()

    @staticmethod
    def test_reports_a_dependency_the_entry_point_does_not_name() -> None:
        assert missing_preloads("import asyncio", package_sources=["import pygame"]) == {"pygame"}

    @staticmethod
    def test_ignores_the_standard_library() -> None:
        assert missing_preloads("", package_sources=["import math\nimport json"]) == set()

    @staticmethod
    def test_ignores_the_games_own_package() -> None:
        assert missing_preloads("", package_sources=["from planet_protectors.tuning import TUNING"]) == set()
