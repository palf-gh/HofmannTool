# HofmannTool

A Glyphs 3 tool for sketching Hofmann-style tangent shapes on a unit grid, then
applying them as `GSPath` contours on the active layer.

ユニットグリッドの上に Hofmann 風の接線パスをスケッチし、`GSPath` として
アクティブレイヤーに書き出すための Glyphs 3 用ツールです。

The tool works directly inside the edit view: pick a starting node, then keep
picking the next tangent until the contour closes (or stops). The inspector
controls the grid (rows, columns, spacing, offsets) and the diameter that
defines each circle. Output can be a filled contour, a hole (reversed
direction), or an open centerline.

エディットビュー上で直接動作します。最初のノードを選び、次の接線候補を順に
クリックしていくと輪郭が組み上がり、最初のノードに戻れば閉じた contour として
確定できます。インスペクタでは行・列・間隔・オフセットなどのグリッド設定と、
円の直径を指定します。出力は `Filled`（塗り）、`Hole`（穴 / 向き反転）、`Line`
（中心線）の3モードから選べます。

## Features / 機能

- Grid-anchored circles with adjustable rows, columns, spacing, and offsets.
  行数・列数・間隔・オフセットを設定できるグリッド上の円。
- Tangent route building: pick a node, then keep picking neighboring nodes; the
  tool offers candidate tangents and you commit one with a click.
  接線ルート組み立て: ノードをクリック → 次のノードをクリック → 候補接線が
  表示されるのでクリックで確定、を繰り返してパスを伸ばします。
- `Filled`, `Hole`, and `Line` output modes. `Hole` writes the same closed
  contour with reversed direction so it counts as an inner contour.
  出力モード `Filled` / `Hole` / `Line`。`Hole` は同じ閉じパスを向き反転して
  穴として使えるようにします。
- `Cmd`-click on a grid node to drop a single closed circle at that node,
  bypassing the route flow. The current direction mode is respected.
  `Cmd` を押しながらノードをクリックすると、ルート編集とは独立にその位置に
  単独の閉じた円を書き出します。向きは現在のモード（Filled / Hole）に従います。
- Tool-local `Cmd+Z` / `Shift+Cmd+Z` history for selection and route steps.
  Glyphs' own undo is paused while the tool history has entries.
  ツール内の `Cmd+Z` / `Shift+Cmd+Z` 履歴で選択・候補・確定・Clear を
  undo/redo できます。ツール履歴が残っている間は Glyphs 本体の Undo は
  一時的に止まります。
- Inspector localized in English and Japanese.
  インスペクタは英語と日本語にローカライズされています。

## Installation / インストール

1. Download or clone this repository.
   このリポジトリをクローンまたはダウンロードします。
2. Double-click `HofmannTool.glyphsTool` in Finder, or symlink it into the
   Glyphs plugins folder:
   Finder で `HofmannTool.glyphsTool` をダブルクリックするか、Plugins
   フォルダにシンボリックリンクを作ります:

   ```bash
   ln -sf "$(pwd)/HofmannTool.glyphsTool" \
     "$HOME/Library/Application Support/Glyphs 3/Plugins/HofmannTool.glyphsTool"
   ```

3. Restart Glyphs 3 and pick **Hofmann Tool** from the toolbar (default
   shortcut `H`).
   Glyphs 3 を再起動し、ツールバーから **Hofmann Tool** を選びます
   （デフォルトショートカット `H`）。

## Usage / 使い方

1. Select the Hofmann Tool. The grid and circle previews appear over the
   active layer.
   Hofmann Tool を選ぶと、アクティブレイヤー上にグリッドと候補円が表示されます。
2. Click a grid node to set the starting circle.
   グリッドノードをクリックして開始の円を決めます。
3. Click the next node; the tool draws candidate tangents. Click a candidate
   to commit it. The active node moves to the new endpoint.
   次のノードをクリックすると候補接線が描画されるので、採用したい候補を
   クリックして確定します。アクティブノードが次の端点に移ります。
4. Repeat. Returning to the start node closes the contour.
   繰り返して開始ノードに戻ると contour が閉じます。
5. Pick `Filled`, `Hole`, or `Line` and press **Apply** to write a `GSPath`
   to the active layer.
   `Filled` / `Hole` / `Line` を選び **Apply** を押すと `GSPath` が
   アクティブレイヤーに追加されます。
6. Hold `Cmd` and click any grid node to drop a single circle there, with
   the direction taken from the current mode.
   `Cmd` を押しながら任意のノードをクリックすると、そのノードに単独の円が
   書き出されます。向きは現在のモードに従います。

`Clear` resets the in-progress route. `Cmd+Z` / `Shift+Cmd+Z` undo and redo
route steps and clears, but only while the tool has its own history.

`Clear` で組み立て中のルートをリセットできます。`Cmd+Z` / `Shift+Cmd+Z` は
ツール履歴がある間のみ、ルートステップや Clear を undo / redo します。

## Settings / 設定

Stored under the key prefix `com.palf.HofmannTool.<setting>` in
`Glyphs.defaults`.
`Glyphs.defaults` 内の `com.palf.HofmannTool.<key>` に保存されます。

| Key / キー | Type / 型 | Default / デフォルト | Notes / 備考 |
| --- | --- | --- | --- |
| `rows` | int | 4 | Grid row count / 行数 |
| `cols` | int | 4 | Grid column count / 列数 |
| `spacing` | float | 120 | Spacing between grid nodes / グリッド間隔（ユニット） |
| `diameter` | float | 80 | Circle diameter / 円の直径（ユニット） |
| `xOffset` | float | 0 | Horizontal offset / 水平オフセット（ユニット） |
| `yOffset` | float | 0 | Vertical offset / 垂直オフセット（ユニット） |
| `outputMode` | string | `filled` | One of `filled`, `hole`, `centerline` |

The grid is centered horizontally on `layer.width` and vertically on the
`ascender` / `descender` body box.
グリッドは水平方向に `layer.width`、垂直方向に `ascender` / `descender` の
ボディボックスで中心揃えされます。

## Development / 開発

Source layout / ファイル構成:

```text
HofmannTool.glyphsTool/Contents/Resources/
  plugin.py             Glyphs-facing SelectTool / Glyphs SelectTool 本体
  hofmann_geometry.py   Pure Python geometry / 純 Python のジオメトリ
  InspectorView.xib     Inspector UI / インスペクタ UI
  InspectorView.nib     Compiled inspector UI / コンパイル済みインスペクタ UI
```

Verification / 確認手順:

```bash
python3 -m py_compile \
  HofmannTool.glyphsTool/Contents/Resources/plugin.py \
  HofmannTool.glyphsTool/Contents/Resources/hofmann_geometry.py
python3 -m unittest discover -s tests
ibtool HofmannTool.glyphsTool/Contents/Resources/InspectorView.xib \
  --compile HofmannTool.glyphsTool/Contents/Resources/InspectorView.nib
```

Branching: feature work lands on `feature/*` branches, merged into `develop`.
`main` only tracks released revisions.
ブランチ運用: 機能は `feature/*` ブランチ → `develop` にマージ。`main` は
リリース版だけを追跡します。

## License / ライセンス

Apache License 2.0. See [LICENSE](LICENSE).
Apache License 2.0。詳細は [LICENSE](LICENSE) を参照してください。
