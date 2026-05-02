# HofmannTool

[日本語版 README](README.ja.md)

A Glyphs 3 tool for sketching Hofmann-style tangent shapes on a unit grid, then
applying them as `GSPath` contours on the active layer.

The tool works directly inside the edit view: pick a starting node, then keep
picking the next tangent until the contour closes (or stops). The inspector
controls the grid (rows, columns, spacing, offsets) and the diameter that
defines each circle. Output can be a filled contour, a hole (reversed
direction), or an open centerline.

## Features

- Grid-anchored circles with adjustable rows, columns, spacing, and offsets.
- Tangent route building: pick a node, then keep picking neighboring nodes; the
  tool offers candidate tangents and you commit one with a click.
- `Filled`, `Hole`, and `Line` output modes. `Hole` writes the same closed
  contour with reversed direction so it counts as an inner contour.
- `Cmd`-click on a grid node to drop a single closed circle at that node,
  bypassing the route flow. The current direction mode (`Filled` or `Hole`) is
  respected.
- Tool-local `Cmd+Z` / `Shift+Cmd+Z` history for selection and route steps.
  Glyphs' own undo is paused while the tool history has entries.
- Inspector localized in English and Japanese.

## Installation

1. Download or clone this repository.
2. Double-click `HofmannTool.glyphsTool` in Finder, or symlink it into the
   Glyphs plugins folder:

   ```bash
   ln -sf "$(pwd)/HofmannTool.glyphsTool" \
     "$HOME/Library/Application Support/Glyphs 3/Plugins/HofmannTool.glyphsTool"
   ```

3. Restart Glyphs 3 and pick **Hofmann Tool** from the toolbar (default
   shortcut `H`).

## Usage

1. Select the Hofmann Tool. The grid and circle previews appear over the
   active layer.
2. Click a grid node to set the starting circle.
3. Click the next node; the tool draws candidate tangents. Click a candidate
   to commit it. The active node moves to the new endpoint.
4. Repeat. Returning to the start node closes the contour.
5. Pick `Filled`, `Hole`, or `Line` and press **Apply** to write a `GSPath`
   to the active layer.
6. Hold `Cmd` and click any grid node to drop a single circle there, with
   the direction taken from the current mode.

Use `Clear` to reset the in-progress route. `Cmd+Z` / `Shift+Cmd+Z` undo and
redo route steps and clears, but only while the tool has its own history.

## Settings

Stored under the key prefix `com.palf.HofmannTool.<setting>` in
`Glyphs.defaults`:

| Key | Type | Default | Notes |
| --- | --- | --- | --- |
| `rows` | int | 4 | Grid row count |
| `cols` | int | 4 | Grid column count |
| `spacing` | float | 120 | Spacing between grid nodes (units) |
| `diameter` | float | 80 | Circle diameter (units) |
| `xOffset` | float | 0 | Horizontal offset of the grid (units) |
| `yOffset` | float | 0 | Vertical offset of the grid (units) |
| `outputMode` | string | `filled` | One of `filled`, `hole`, `centerline` |

The grid is centered horizontally on `layer.width` and vertically on the
`ascender`/`descender` body box.

## Development

Source layout:

```text
HofmannTool.glyphsTool/Contents/Resources/
  plugin.py             Glyphs-facing SelectTool
  hofmann_geometry.py   Pure Python geometry
  InspectorView.xib     Inspector UI
  InspectorView.nib     Compiled inspector UI
```

Verification:

```bash
python3 -m py_compile \
  HofmannTool.glyphsTool/Contents/Resources/plugin.py \
  HofmannTool.glyphsTool/Contents/Resources/hofmann_geometry.py
python3 -m unittest discover -s tests
ibtool HofmannTool.glyphsTool/Contents/Resources/InspectorView.xib \
  --compile HofmannTool.glyphsTool/Contents/Resources/InspectorView.nib
```

Branching: feature work lands on `feature/*` branches, merged into
`develop`. `main` only tracks released revisions.

## License

Apache License 2.0. See [LICENSE](LICENSE).
