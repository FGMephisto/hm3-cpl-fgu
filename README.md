# HarnMaster Comprehensive Pricelist (`hm3-cpl-fgu`)

Converts [toastygm/hm3-cpl](https://github.com/toastygm/hm3-cpl) (Foundry VTT HârnMaster 3 Comprehensive Price Lists) into the **HarnMaster Comprehensive Pricelist** Fantasy Grounds Unity (`.mod`) module for the **HarnMaster3.5E** ruleset.

## Features

- Converts all **40 vendor/craft compendium packs** (**869 items**: 717 general gear items, 131 armor pieces, 21 containers) into a single FGU module (`HarnMaster3.5E_CPL.mod`).
- Preserves vendor/guild groupings as FGU `<category>` groups (`Apothecary`, `Armorer`, `Clothier`, etc.).
- Maps `armorgear` records to `HarnMaster3.5E` fields:
  - Material → `<subtype>` (`Cloth`, `Kurbul`, `Leather`, `Mail`, `Plate`, `Quilt`, `Ring`, `Scale`)
  - Protection → `<armor_blunt>`, `<armor_edge>`, `<armor_point>`, `<armor_fire>`
  - Hit locations → `<armor_coverage>` (`Sk`, `Fa`, `Nk`, `Sh`, `Ua`, `El`, `Fo`, `Ha`, `Tx`, `Ab`, `Hp`, `Gr`, `Th`, `Kn`, `Ca`, `Ft`)
- Formats prices in pence (`<cost>570d</cost>`) and numeric weights (`<weight>`).

## Prerequisites

- Python 3.9+ (standard library only, no third-party packages required)
- Clone the repository (all upstream data files and commit history are vendored directly in `upstream/hm3-cpl/` via `git subtree`):
  ```bash
  git clone https://github.com/FGMephisto/hm3-cpl-fgu.git
  ```

## Building the Module

From the repository root:

```bash
python scripts/build_mod.py
```

By default, this outputs `../HarnMaster3.5E_CPL.mod` (directly into `channels/Test/modules/HarnMaster3.5E_CPL.mod` when cloned there). Use `--output` to specify a custom path:

```bash
python scripts/build_mod.py --output dist/HarnMaster3.5E_CPL.mod
```

## Comparing & Syncing Upstream (`toastygm/hm3-cpl`)

All files and commit history from `toastygm/hm3-cpl` are stored directly inside `upstream/hm3-cpl/` so the data remains preserved even if the upstream repository disappears.

To check and compare against `toastygm/hm3-cpl` for changes:

```bash
# Check for new upstream commits and changed files
python scripts/sync_upstream.py

# Include full unified diff (optionally filter by path)
python scripts/sync_upstream.py --diff
python scripts/sync_upstream.py --diff --path packs/

# Pull upstream updates into upstream/hm3-cpl and rebuild the .mod
python scripts/sync_upstream.py --pull
python scripts/build_mod.py
```

Or using `git` directly:

```bash
# One-time remote setup in a fresh clone
git remote add upstream-hm3-cpl https://github.com/toastygm/hm3-cpl.git
git config remote.upstream-hm3-cpl.tagOpt --no-tags

# Fetch and compare against the vendored tree
git fetch --no-tags upstream-hm3-cpl main
git diff --stat HEAD:upstream/hm3-cpl upstream-hm3-cpl/main

# Pull updates into upstream/hm3-cpl
git subtree pull --prefix=upstream/hm3-cpl upstream-hm3-cpl main
```

## Attribution & License

- **Upstream Foundry Module**: [toastygm/hm3-cpl](https://github.com/toastygm/hm3-cpl) by Toasty
- **Comprehensive Price Lists**: Scythen ([Lythia.com](https://www.lythia.com/game_aides/comprehensive-pricelist/))
- **License**: [Creative Commons Attribution-NonCommercial-ShareAlike 3.0 Unported (CC BY-NC-SA 3.0)](LICENSE)

