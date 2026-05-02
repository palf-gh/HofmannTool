# HofmannTool

A Glyphs 3 tool for sketching Hofmann-style tangent shapes on a unit grid, then
applying them as `GSPath` contours on the active layer.

[English](#english) | [日本語](#日本語)

---

## English

The tool works directly inside the edit view: pick a starting node, then keep
picking the next tangent until the contour closes (or stops). The inspector
controls the grid (rows, columns, spacing, offsets) and the diameter that
defines each circle. Output can be a filled contour, a hole (reversed
direction), or an open centerline.

### Features

- Grid-anchored circles with adjustable rows, columns, spacing, and offsets.
- Number steppers next to every numeric inspector field for quick adjustment.
- Tangent route building: pick a node, then keep picking neighboring nodes; the
  tool offers candidate tangents and you commit one with a click.
- `Filled`, `Hole`, and `Line` output modes. `Hole` writes the same closed
  contour with reversed direction so it counts as an inner contour.
- `Cmd`-click on a grid node to drop a single closed circle at that node,
  bypassing the route flow. The direction follows the current mode (`Filled`
  → CCW, `Hole` → CW).
- Tool-local `Cmd+Z` / `Shift+Cmd+Z` history for selection and route steps.
  Glyphs' own undo is paused while the tool history has entries.
- Inspector localized in English and Japanese.

### Installation

1. Download or clone this repository.
2. Double-click `HofmannTool.glyphsTool` in Finder, or symlink it into the
   Glyphs plugins folder:

   ```bash
   ln -sf "$(pwd)/HofmannTool.glyphsTool" \
     "$HOME/Library/Application Support/Glyphs 3/Plugins/HofmannTool.glyphsTool"
   ```

3. Restart Glyphs 3 and pick **Hofmann Tool** from the toolbar. No keyboard
   shortcut is assigned by default; you can bind one in
   `System Settings → Keyboard → Keyboard Shortcuts → App Shortcuts` if you
   like.

### Usage

1. Select the Hofmann Tool. The grid and circle previews appear over the
   active layer.
2. Click a grid node to set the starting circle.
3. Click the next node; the tool draws candidate tangents. Click a candidate
   to commit it. The active node moves to the new endpoint.
4. Repeat. Returning to the start node closes the contour.
5. Pick `Filled`, `Hole`, or `Line` and press **Apply** to write a `GSPath`
   to the active layer.
6. Hold `Cmd` and click any grid node to drop a single circle at that node.
   The direction follows the current mode, so switch to `Hole` first if you
   want a reversed (inner) circle.

`Clear` resets the in-progress route. `Cmd+Z` / `Shift+Cmd+Z` undo and redo
route steps and clears, but only while the tool has its own history.

### Settings

Stored under the key prefix `com.palf.HofmannTool.<setting>` in
`Glyphs.defaults`.

| Key | Type | Default | Notes |
| --- | --- | --- | --- |
| `rows` | int | 4 | Grid row count |
| `cols` | int | 4 | Grid column count |
| `spacing` | float | 40 | Edge-to-edge gap between adjacent circles (units). The grid step is `diameter + spacing`. |
| `diameter` | float | 80 | Circle diameter (units) |
| `xOffset` | float | 0 | Horizontal offset of the grid (units) |
| `yOffset` | float | 0 | Vertical offset of the grid (units) |
| `outputMode` | string | `filled` | One of `filled`, `hole`, `centerline` |

The grid is centered horizontally on `layer.width` and vertically on the
`ascender` / `descender` body box.

### Development

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

Branching: feature work lands on `feature/*` branches, merged into `develop`.
`main` only tracks released revisions.

### License

Apache License 2.0. See [LICENSE](LICENSE).

---

## 日本語

ユニットグリッドの上に Hofmann 風の接線パスをスケッチし、`GSPath` として
アクティブレイヤーに書き出すための Glyphs 3 用ツールです。

エディットビュー上で直接動作します。最初のノードを選び、次の接線候補を順に
クリックしていくと輪郭が組み上がり、最初のノードに戻れば閉じた contour として
確定できます。インスペクタでは行・列・間隔・オフセットなどのグリッド設定と、
円の直径を指定します。出力は `Filled`（塗り）、`Hole`（穴 / 向き反転）、`Line`
（中心線）の3モードから選べます。

### 機能

- 行数・列数・間隔・オフセットを設定できるグリッド上の円。
- インスペクタの各数値入力欄にステッパー（増減ボタン）付き。
- 接線ルート組み立て: ノードをクリック → 次のノードをクリック → 候補接線が
  表示されるのでクリックで確定、を繰り返してパスを伸ばします。
- 出力モード `Filled` / `Hole` / `Line`。`Hole` は同じ閉じパスを向き反転して
  穴として使えるようにします。
- `Cmd` を押しながらノードをクリックすると、ルート編集とは独立にその位置に
  単独の閉じた円を書き出します。向きは現在のモードに従います（`Filled`
  なら CCW、`Hole` なら CW）。
- ツール内の `Cmd+Z` / `Shift+Cmd+Z` 履歴で選択・候補・確定・Clear を
  undo/redo できます。ツール履歴が残っている間は Glyphs 本体の Undo は
  一時的に止まります。
- インスペクタは英語と日本語にローカライズされています。

### インストール

1. このリポジトリをクローンまたはダウンロードします。
2. Finder で `HofmannTool.glyphsTool` をダブルクリックするか、Plugins
   フォルダにシンボリックリンクを作ります:

   ```bash
   ln -sf "$(pwd)/HofmannTool.glyphsTool" \
     "$HOME/Library/Application Support/Glyphs 3/Plugins/HofmannTool.glyphsTool"
   ```

3. Glyphs 3 を再起動し、ツールバーから **Hofmann Tool** を選びます。
   ショートカットはデフォルトでは未割り当てです。必要なら macOS の
   「システム設定 → キーボード → キーボードショートカット → アプリの
   ショートカット」から好きなキーを割り当ててください。

### 使い方

1. Hofmann Tool を選ぶと、アクティブレイヤー上にグリッドと候補円が表示
   されます。
2. グリッドノードをクリックして開始の円を決めます。
3. 次のノードをクリックすると候補接線が描画されるので、採用したい候補を
   クリックして確定します。アクティブノードが次の端点に移ります。
4. 繰り返して開始ノードに戻ると contour が閉じます。
5. `Filled` / `Hole` / `Line` を選び **Apply** を押すと `GSPath` が
   アクティブレイヤーに追加されます。
6. `Cmd` を押しながら任意のノードをクリックすると、そのノードに単独の円が
   書き出されます。穴向きにしたいときは出力モードを先に `Hole` に切り替えて
   ください。

`Clear` で組み立て中のルートをリセットできます。`Cmd+Z` / `Shift+Cmd+Z` は
ツール履歴がある間のみ、ルートステップや Clear を undo / redo します。

### 設定

`Glyphs.defaults` 内の `com.palf.HofmannTool.<key>` に保存されます。

| キー | 型 | デフォルト | 備考 |
| --- | --- | --- | --- |
| `rows` | int | 4 | 行数 |
| `cols` | int | 4 | 列数 |
| `spacing` | float | 40 | 隣り合う円の縁同士の間隔（ユニット）。グリッドの中心間隔は `diameter + spacing` になります。 |
| `diameter` | float | 80 | 円の直径（ユニット） |
| `xOffset` | float | 0 | グリッド水平オフセット（ユニット） |
| `yOffset` | float | 0 | グリッド垂直オフセット（ユニット） |
| `outputMode` | string | `filled` | `filled` / `hole` / `centerline` |

グリッドは水平方向に `layer.width`、垂直方向に `ascender` / `descender` の
ボディボックスで中心揃えされます。

### 開発

ファイル構成:

```text
HofmannTool.glyphsTool/Contents/Resources/
  plugin.py             Glyphs SelectTool 本体
  hofmann_geometry.py   純 Python のジオメトリ
  InspectorView.xib     インスペクタ UI
  InspectorView.nib     コンパイル済みインスペクタ UI
```

確認手順:

```bash
python3 -m py_compile \
  HofmannTool.glyphsTool/Contents/Resources/plugin.py \
  HofmannTool.glyphsTool/Contents/Resources/hofmann_geometry.py
python3 -m unittest discover -s tests
ibtool HofmannTool.glyphsTool/Contents/Resources/InspectorView.xib \
  --compile HofmannTool.glyphsTool/Contents/Resources/InspectorView.nib
```

ブランチ運用: 機能は `feature/*` ブランチ → `develop` にマージ。`main` は
リリース版だけを追跡します。

### ライセンス

Apache License 2.0。詳細は [LICENSE](LICENSE) を参照してください。
