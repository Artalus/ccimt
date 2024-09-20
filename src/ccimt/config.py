from dataclasses import dataclass
from fnmatch import fnmatch
from pathlib import Path
from typing import Literal, assert_never

import yaml
from pydantic import BaseModel
from result import Err, Ok, Result


@dataclass
class GlobalConfig:
    """Global configuration from file in the repo root"""

    recipe_linters: list['RecipeLintersSet']
    recipe_origins: dict[str, str]
    recipes_folder: Path

    @staticmethod
    def from_dir(path: Path = Path('.')) -> Result['GlobalConfig', str]:
        config_file = path / 'ccimt-config.yml'
        if not config_file.is_file():
            return Err(f'File {config_file.absolute()} does not exist')

        try:
            with config_file.open() as f:
                raw = yaml.safe_load(f)
            cfg = RawGlobal(**raw)
        except Exception as e:
            return Err(f'Could not load config from {config_file.absolute()}: {e}')

        if not cfg.recipes_folder.is_dir():
            return Err(f'recipes_folder: directory {cfg.recipes_folder.absolute()} does not exist')
        origins = {key: value.repo for key, value in cfg.recipe_origins.items()}
        linters = [
            RecipeLintersSet(
                pattern=linter.pattern,
                exclude=linter.exclude,
                commands=linter.commands,
            )
            for linter in cfg.recipe_linters
        ]
        return Ok(
            GlobalConfig(
                recipe_linters=linters,
                recipe_origins=origins,
                recipes_folder=cfg.recipes_folder,
            )
        )


@dataclass
class RecipeConfig:
    """Build configuration for a single recipe in the recipes directory"""

    build_versions: list['RecipeVersionToBuild']
    origin: Literal['local'] | 'RecipeOrigin'

    @staticmethod
    def from_dir(path: Path, global_config: GlobalConfig) -> Result['RecipeConfig', str]:
        config_file = path / 'config.yml'
        match RecipeConfig._parse_config_file(config_file, path, global_config):
            case Ok(_) as ok:
                return ok
            case Err(msg):
                return Err(f'Could not load config from {config_file.absolute()}: {msg}')
            case x:
                assert_never(x)

    @staticmethod
    def _parse_config_file(
        file: Path, recipe_path: Path, global_config: GlobalConfig
    ) -> Result['RecipeConfig', str]:
        if not file.is_file():
            return Err('file does not exist')

        try:
            with file.open() as f:
                raw = yaml.safe_load(f)
            cfg = RawRecipe(**raw)
        except Exception as e:
            return Err(f'parse error: {e}')

        versions = []
        for version, value in cfg.versions.items():
            folder = value.folder
            if not (conanfile := recipe_path / folder / 'conanfile.py').is_file():
                return Err(
                    f'version `{version}` declares `folder: {folder}`, but file '
                    f'{conanfile.absolute()} does not exist'
                )
            versions.append(
                RecipeVersionToBuild(version=version, recipe_folder=recipe_path / folder)
            )

        origin: Literal['local'] | 'RecipeOrigin'
        if isinstance(cfg.origin, dict):
            if len(cfg.origin.keys()) > 1:
                return Err('recipe can only have one origin')
            elif not cfg.origin:
                return Err('recipe should have origin')
            origin = RecipeOrigin(
                repo=list(cfg.origin.keys())[0],
                commit=list(cfg.origin.values())[0].commit,
            )
            if origin.repo not in global_config.recipe_origins:
                return Err(f'origin {origin.repo} is not defined in global config')
        else:
            origin = cfg.origin

        return Ok(RecipeConfig(build_versions=versions, origin=origin))


@dataclass
class RecipeLintersSet:
    pattern: str
    exclude: str | None
    commands: list[str]

    def file_matches_patterns(self, file: Path) -> bool:
        if not fnmatch(str(file), self.pattern):
            return False
        if not self.exclude:
            return True
        return not fnmatch(str(file), self.exclude)


@dataclass
class RecipeVersionToBuild:
    version: str
    recipe_folder: Path


@dataclass
class RecipeOrigin:
    repo: str
    commit: str


class RawGlobal(BaseModel):
    recipe_linters: list['RawGlobalRecipeLinter']
    recipe_origins: dict[str, 'RawGlobalKnownOrigin']
    recipes_folder: Path


class RawGlobalRecipeLinter(BaseModel):
    pattern: str
    exclude: str | None = None
    commands: list[str]


class RawGlobalKnownOrigin(BaseModel):
    repo: str


class RawRecipe(BaseModel):
    versions: dict[str, 'RawRecipeVersion']
    origin: Literal['local'] | dict[str, 'RawRecipeOrigin']


class RawRecipeVersion(BaseModel):
    folder: Path


class RawRecipeOrigin(BaseModel):
    commit: str
