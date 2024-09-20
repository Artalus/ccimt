#!/usr/bin/env python3

import logging
import subprocess
from argparse import ArgumentParser
from dataclasses import dataclass
from pathlib import Path
from typing import assert_never

from result import Err, Ok, Result

from ccimt.config import GlobalConfig, RecipeConfig

logger = logging.getLogger(__name__)


@dataclass
class Args:
    files: list[Path]
    strict_recipe_configs: bool
    debug: bool


def parse_args() -> Args:
    p = ArgumentParser()
    p.add_argument('files', nargs='+', type=Path, help='files to lint')
    p.add_argument(
        '--strict-recipe-configs',
        action='store_true',
        help='fail the lint if any recipe config is invalid; ignore file otherwise',
    )
    p.add_argument('--debug', action='store_true')
    return Args(**p.parse_args().__dict__)


def main(args: Args) -> int:
    logging.basicConfig(
        level=logging.DEBUG if args.debug else logging.INFO,
        style='{',
        format='{levelname:5} : {name:10} : {message}',
    )

    for f in args.files:
        if not f.is_file():
            logger.error(f'File {f} does not exist')
            return 1

    match GlobalConfig.from_dir():
        case Ok(config):
            pass
        case Err(e):
            logger.error(e)
            return 1
        case x:
            assert_never(x)

    recipe_files = [f for f in args.files if f.is_relative_to(config.recipes_folder)]
    if not recipe_files:
        logger.info(f'Changed files are not under {config.recipes_folder}')
        return 0
    logger.info(f'Files to lint:{"".join([f"\n * {r}" for r in recipe_files])}\n')

    match lint_files(args.files, config, args.strict_recipe_configs):
        case Ok(None):
            logger.info('Linting succeeded')
            return 0
        case Err(failures):
            failures = [f'\n  * {f}' for f in failures]
            logger.info(f'Failed lints:{"".join(failures)}')
            return 1
        case y:
            assert_never(y)


def lint_files(
    files: list[Path], global_config: GlobalConfig, strict: bool
) -> Result[None, list[str]]:
    recipe_configs: dict[str, Result[RecipeConfig, str]] = dict()
    failures = []
    for file in files:
        relative = file.relative_to(global_config.recipes_folder)
        logger.debug(f'check {relative}...')
        # -1 is `.`, -2 is first subdirectory (`foo`)
        recipe = str(relative.parents[-2])

        config: RecipeConfig | None
        match load_recipe_config_cached(recipe, recipe_configs, global_config):
            case Ok(config):
                pass
            case Err(msg):
                config = None
                if strict:
                    failures.append(msg)
            case x:
                assert_never(x)

        file_should_be_linted = config and config.origin == 'local'
        if not file_should_be_linted:
            logger.info(
                f'({recipe}) skipping {relative}: {"no recipe config" if not config else "recipe not local"}'
            )
            continue

        for linter in global_config.recipe_linters:
            logger.debug(f' match {linter.pattern}...')

            if not linter.file_matches_patterns(relative):
                logger.debug('  does not match, ignore')
                continue

            logger.info(f'Linting {relative}...')
            for cmd in linter.commands:
                cmd = cmd.format(FILE=file)
                logger.debug(f' >  `{cmd}`')
                rc = subprocess.call(cmd, shell=True)
                if rc != 0:
                    failures.append(f'{cmd}  =>  {rc}')

    if failures:
        return Err(failures)
    return Ok(None)


def load_recipe_config_cached(
    recipe: str, cache: dict[str, Result[RecipeConfig, str]], global_config: GlobalConfig
) -> Result[RecipeConfig, str]:
    if c := cache.get(recipe):
        return c

    res = RecipeConfig.from_dir(global_config.recipes_folder / recipe, global_config)
    match res:
        case Ok(_):
            cache[recipe] = res
            return res
        case Err(e):
            msg = f'Failed to load recipe config for {recipe}: {e}'
            logger.warning(msg)
            return Err(msg)
        case x:
            assert_never(x)


def _main_script() -> int:
    return main(parse_args())


if __name__ == '__main__':
    exit(_main_script())
