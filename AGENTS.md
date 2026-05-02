# HofmannTool - Project Instructions

## Overview

HofmannTool is a Glyphs 3 `SelectTool` for creating Hofmann-style tangent paths
on a unit grid. It is inspired by the interaction model of `hofmann-1.0.0`, but
geometry and Glyphs integration must be implemented independently in this repo.

Bundle ID: `com.palf.HofmannTool`

## Branch Strategy

- `main`: release branch only.
- `develop`: integration branch for ongoing development.
- `feature/*`: feature or bugfix branches, merged into `develop` through PRs.

Flow:

```text
feature/<name> -> PR -> develop -> PR -> main
```

Use non-fast-forward merges for PRs when preserving branch history is useful.
Delete feature branches after they are merged.

## Plugin Structure

```text
HofmannTool.glyphsTool/
  Contents/
    Info.plist
    MacOS/plugin
    Resources/
      plugin.py
      hofmann_geometry.py
      InspectorView.xib
      InspectorView.nib
      toolbar.pdf
```

- `plugin.py`: Glyphs-facing SelectTool, inspector wiring, mouse handling,
  preview drawing, and eventual `GSPath` output.
- `hofmann_geometry.py`: pure Python geometry, grid, tangent candidate, and
  path-building logic. Keep it independent from Glyphs/AppKit.
- `InspectorView.xib` and `InspectorView.nib`: inspector UI, based on the
  `CJKAnchorPlacement` style of loading a compact custom inspector view.

## Product Defaults

- Grid is centered in the active layer body box by default:
  `x=0..layer.width`, `y=descender..ascender`.
- Core inspector values are `Rows`, `Cols`, `Spacing`, `Diameter`, `X Offset`,
  and `Y Offset`, all in Glyphs units except row/column counts.
- Output modes are `Filled Shape` and `Centerline`.
- Preview visibility toggles are `Grid`, `Nodes`, `Candidates`, and `Labels`.
- Writes to the active layer happen only through `Apply`.

## Implementation Rules

- Do not copy source code from `hofmann-1.0.0`; use it only as behavioral
  reference.
- Keep geometry deterministic and covered by unit tests before connecting it to
  Glyphs events.
- Store settings under `Glyphs.defaults['com.palf.HofmannTool.<key>']`.
- Keep UI labels in English for now; add localization after MVP behavior is
  stable.
- Do not commit generated caches, `.DS_Store`, or `__pycache__`.

## Verification

```bash
python3 -m py_compile \
  HofmannTool.glyphsTool/Contents/Resources/plugin.py \
  HofmannTool.glyphsTool/Contents/Resources/hofmann_geometry.py

python3 -m unittest discover -s tests

ibtool HofmannTool.glyphsTool/Contents/Resources/InspectorView.xib \
  --compile HofmannTool.glyphsTool/Contents/Resources/InspectorView.nib
```

Manual Glyphs check:

```bash
ln -sf "$(pwd)/HofmannTool.glyphsTool" \
  "$HOME/Library/Application Support/Glyphs 3/Plugins/HofmannTool.glyphsTool"
```

Restart Glyphs 3, select the Hofmann Tool, and confirm inspector loading,
setting persistence, and grid preview drawing.
