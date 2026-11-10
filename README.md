# Hârn Comprehensive Price Lists for Fantasy Grounds Unity (`hm3-cpl-fgu`)

Converts [toastygm/hm3-cpl](https://github.com/toastygm/hm3-cpl) (Foundry VTT HârnMaster 3 Comprehensive Price Lists) into a Fantasy Grounds Unity (`.mod`) module for the **HarnMaster3.5E** ruleset.

## Features

- Converts all **40 vendor/craft compendium packs** (**869 items**: 717 general gear items, 131 armor pieces, 21 containers) into a single FGU module (`HarnMaster3.5E_CPL.mod`).
- Preserves vendor/guild groupings as FGU `<category>` groups (`CPL - Apothecary`, `CPL - Armorer`, `CPL - Clothier`, etc.).
- Maps `armorgear` records to `HarnMaster3.5E` fields:
  - Material → `<subtype>` (`Cloth`, `Kurbul`, `Leather`, `Mail`, `Plate`, `Quilt`, `Ring`, `Scale`)
  - Protection → `<armor_blunt>`, `<armor_edge>`, `<armor_point>`, `<armor_fire>`
  - Hit locations → `<armor_coverage>` (`Sk`, `Fa`, `Nk`, `Sh`, `Ua`, `El`, `Fo`, `Ha`, `Tx`, `Ab`, `Hp`, `Gr`, `Th`, `Kn`, `Ca`, `Ft`)
- Formats prices in pence (`<cost>570d</cost>`) and numeric weights (`<weight>`).

## Prerequisites

- Python 3.9+ (standard library only, no third-party packages required)
- Submodule initialized:
  ```bash
  git clone --recurse-submodules https://github.com/FGMephisto/hm3-cpl-fgu.git
  ```
  *(Or `git submodule update --init --recursive` if already cloned.)*

## Building the Module

From the repository root:

```bash
python scripts/build_mod.py
```

By default, this outputs `../HarnMaster3.5E_CPL.mod` (directly into `channels/Test/modules/HarnMaster3.5E_CPL.mod` when cloned there). Use `--output` to specify a custom path:

```bash
python scripts/build_mod.py --output dist/HarnMaster3.5E_CPL.mod
```

To update upstream data when `toastygm/hm3-cpl` changes:

```bash
git submodule update --remote upstream/hm3-cpl
python scripts/build_mod.py
```

## Attribution & License

- **Upstream Foundry Module**: [toastygm/hm3-cpl](https://github.com/toastygm/hm3-cpl) by Toasty
- **Comprehensive Price Lists**: Scythen ([Lythia.com](https://www.lythia.com/game_aides/comprehensive-pricelist/))
- **License**: [Creative Commons Attribution-NonCommercial-ShareAlike 3.0 Unported (CC BY-NC-SA 3.0)](LICENSE)
