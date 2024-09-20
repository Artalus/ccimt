# Key points

- Build packages from Conan Center Index upstream for a specific set of settings
& options, uploading to a configured remote
    - CCI and its default binaries is never enough for any given enterprise needs

- Get existing recipes from CCI upstream, without need to copy everything
    - adding a package to the build should be as simple as providing a
    "what to build" config file

- Still enable "forking" recipes, to adapt specific recipes to local needs
    - some recipes are doomed to have features somehow not suited to be used
    locally / lack features requested locally

- Keep track of those forks, providing a report on how much they stray from upstream
    - to enable quick reactive merges instead of "oooh dam our recipes are outdated"
    once in a blue moon

- Support full matrix rebuild on a PR – together with precise manual rebuilds for
a given set&opt config
    - to surgically rebuild 1/2/N specific configurations where we know the culprit
    was not on the recipe’s side (invalid CI configuration, etc.)
    - provide tweaking points via PR interface (description? labels?)

- Support conditional linting based on package type
    - if a recipe is forked from upstream CCI, we want to keep the differences
    to a minimum no matter how ugly it is.
    At the same time, we want our recipes to be beautiful.
    So only run ruff, pylint and others on some recipes but not on others

- Enable full rebuild&reupload of any specific package with its dependencies
    - adding a new platform/compiler/settings should not be that much of a pain

- Be aware that a package may only be buildable under a specific platform
    - Windows / Linux / ARM / x64 / Release / … -specific things, together with
    packages clearly stating "we do not support X"

    - If package A is built only for set of platforms X – and either it depends
    on B or B depends on it, while B is built on different set Y – the system
    should warn about that before missing package binaries are found in "production"

- Be aware that a package may be platform/compiler-independent
    - header-only, binary wrapper with compiler irrelevant, …

- Be aware that multiple versions of a package may be required
    - openssl-1 / openssl-3, different protobuf, etc

- Be aware that multiple option sets may be required
    - with / without GPU support, static / shared, default values differing from CCI, …


# Open-sourcing this

- both conan very own devs and other engineers work on (essentially) the same task

- more expertise on how the problem gets solved globally by other devs with other
(or similar!) environments

- some better dev-rel / PR for company, "they are the guys involved with the thing we use"


# Some implementation details

- Implement in Python to interop with Conan API

- Should have clear interfaces and maintain separation from a CI service,
not relying on any behavior specific to Jenkins, Github, Gitlab, etc.

- Not do everything at once, resulting in 40+minute script run.
Instead split separate meaningful stages into different executable calls
    - preserve state in output files, to be read by CI and later stages

- CCI has a config.yml file for each recipe with a list of versions – extrapolate
from there, put in there things like upstream: fork: commit: a1b2c3 and other
metadata needed
