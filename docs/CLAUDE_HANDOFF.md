# HofmannTool Handoff for Claude

最終更新: 2026-04-30
作業ブランチ: `feature/bootstrap-scaffold`
現HEAD: `b444f64 fix: localize and restyle inspector controls`

## 目的

Glyphs 3 用の `SelectTool` として、Hofmann 1.0.0 のような「グリッド上の円どうしを接線と円弧で接続する」ツールを作る。ユーザーはグリッド点をクリックして接続候補を選び、最終的に Glyphs のアウトラインとしてレイヤーへ適用できるようにしたい。

重要な意図:

- グリッド点は「点」ではなく、`Diameter` で指定した直径の円として扱う。
- 接線候補は円と円の接線であり、最終パスは直線接線 + 円弧で構成される。
- `Diameter >= distance between selected centers` のとき、内接線候補は無効。
- Apply はプレビューを実際の `GSPath` に変換して active layer へ追加する。
- 操作は Glyphs 内で完結し、Web版のコードはコピーしない。

## 参照コード/資料

### Hofmann 1.0.0

Repository:

- https://github.com/bbtgnn/hofmann-1.0.0

特に見るべきファイル:

- `assets/ts/app.ts`
  - グリッドノード、選択状態、候補追加、輪郭閉鎖の状態管理。
- `assets/ts/tangentFunctions.ts`
  - 2円間の接線候補を作る考え方。
  - `O/A` は時計回り/反時計回り相当。
- `assets/ts/tangentRndr.ts`
  - 候補線クリック、次の active node への遷移。
- `assets/ts/contourRndr.ts`
  - 選択済みセグメントを連結し、閉じた輪郭では塗りにする処理。
- `assets/ts/appRndr.ts`
  - `spacing` と `radius = spacing / 2 * ratio` の関係。

注意:

- GPLv3 repo なので、実装を直接コピーしない。
- 今回は挙動/UX/幾何の考え方だけを参照する。

### Glyphs SDK / 既存実装

SDK:

- `/Users/palf/Documents/Glyphs_plugins/GlyphsSDK`

参考:

- `/Users/palf/Documents/Glyphs_plugins/GlyphsSDK/Python Templates/SelectTool/`
  - Python SelectTool の基本構造。
- `/Users/palf/Documents/Glyphs_plugins/GlyphsSDK/Python Templates/SelectTool/Snippets/Custom Info Box/Xcode/`
  - Inspector view の最小例。
- `/Users/palf/Documents/GitHub/CJKAnchorPlacement/CJKAnchorPlacement.glyphsTool/Contents/Resources/plugin.py`
  - `GSInspectorView`, `loadNib("InspectorView", __file__)`, `inspectorDialogView` の参考。
- `/Users/palf/Documents/GitHub/CJKAnchorPlacement/CJKAnchorPlacement.glyphsTool/Contents/Resources/InspectorView.xib`
  - Compact inspector XIB の参考。
- `/Users/palf/Documents/GitHub/SnappingGrid/SnappingGrid.glyphsPlugin/Contents/Resources/plugin.py`
  - Grid描画、設定保存、Glyphs UI色補正、ローカライズの参考。

## 現在の実装

主要ファイル:

- `HofmannTool.glyphsTool/Contents/Resources/plugin.py`
  - Glyphs-facing code。
  - Inspector UI、設定保存、グリッド描画、クリック処理、候補プレビュー描画。
- `HofmannTool.glyphsTool/Contents/Resources/hofmann_geometry.py`
  - Glyphs/AppKit 非依存の geometry module。
  - `Point`, `GridNode`, `TangentCandidate`, `grid_origin`, `node_point`, `create_tangent_candidates`, `is_closed_contour`。
- `HofmannTool.glyphsTool/Contents/Resources/InspectorView.xib`
  - 横長の Inspector UI。
- `HofmannTool.glyphsTool/Contents/Resources/InspectorView.nib`
  - `ibtool` で生成済み。
- `tests/test_hofmann_geometry.py`
  - geometry module の最小テスト。

現在できること:

- Glyphs でツールとしてロードされる。
- active layer の body box 中央に unit grid を描画する。
- Inspector で `Rows`, `Cols`, `Spacing`, `Diameter`, `X`, `Y`, 表示トグルを設定できる。
- 日本語環境ではラベルが日本語になる。
- クリックで開始ノードを選び、次ノードクリックで接線候補を表示し、候補クリックでプレビュー線を確定できる。

現在できない/不完全なこと:

- `Diameter` の円が描画されていない。
  - 現状はノード位置に小さい dot を描いているだけ。
  - 正しくは各グリッド点に直径 `Diameter` の円を薄く描くべき。
- 候補/確定プレビューが直線だけで、円弧がない。
  - 正しくは接線直線 + 接続円上の arc を描く。
- Apply は未実装。
  - 現状は `print("HofmannTool: Apply will be implemented...")` だけ。
  - 正しくは `GSPath` / `GSNode` を作って active layer に追加する。
- `Filled Shape` / `Centerline` の出力差が未実装。
  - `Centerline`: 開いた状態でも接線+円弧の中心線的アウトライン、または単線相当の open path。
  - `Filled Shape`: 閉じた輪郭のみ有効にし、塗り形状として `GSPath.closed = True`。
- UIの `Apply`, `Undo`, `Clear` がボタンに見えにくい。
  - Glyphs inspector 上では small push button がフラットな文字に見える。
  - より明確な segmented/push style、またはアイコン+短ラベルへの変更が必要。

## ユーザーからの最新フィードバック

2026-04-30:

- 「直径サイズで円が描画されるべき」
- 現在の接続線表示が変に見える。
- `Apply` を押しても何も起きない。
- `Apply`, `Undo`, `Clear` がボタンに見えない。
- いったん Claude に投げられるよう、仕様書、参考コード、現状修正点をまとめたい。

## 期待仕様

### Inspector

横長配置を維持する。現在の幅は `326`, 高さは `104`。

操作項目:

- `Rows` / `行`
- `Cols` / `列`
- `Spacing` / `間隔`
- `Diameter` / `直径`
- `X`, `Y` offset
- output mode: `Filled` / `塗り`, `Line` / `線`
- visibility: `Grid` / `グリッド`, `Nodes` / `ノード`, `Candidates` / `候補`, `Labels` / `ラベル`
- commands: `Apply` / `適用`, `Undo` / `戻す`, `Clear` / `消去`

UI改善希望:

- `Apply`, `Undo`, `Clear` は明確に押せるボタンとして見えること。
- 入力欄の文字は明確に見えること。
- ラベルは白飛びしないこと。
- 右側に不要な余白を作らないこと。

### Grid / 円表示

各 `GridNode(row, col)` の中心:

```text
x = origin.x + col * spacing
y = origin.y + row * spacing
```

`origin` は active layer の body box 中央配置:

```text
body x: 0 .. layer.width
body y: descender .. ascender
grid width  = (cols - 1) * spacing
grid height = (rows - 1) * spacing
origin.x = (layer.width - grid width) / 2 + xOffset
origin.y = (ascender + descender) / 2 - grid height / 2 + yOffset
```

描画:

- grid line は薄い線。
- node center は小さい点として描いてもよい。
- ただし本体は `Diameter` の円として描く。
- 円は薄い stroke で、選択状態に応じて色/太さを変える。
- active/start circle は強調する。

### Tangent / arc preview

クリックフロー:

1. グリッド円をクリックして start/active node にする。
2. 別のグリッド円をクリックして、2円間の有効な接線候補を表示。
3. 候補をクリックして確定。
4. 確定後は `candidate.node_b` が次の active node。
5. 以降は前回の `flow_b` と次候補の `flow_a` が一致する候補だけ表示。
6. start node に戻り、flow も一致したら closed contour。

候補描画:

- 直線だけではなく、円周上の arc も見えること。
- 確定済み path も、直線 + arc で描画すること。
- Hofmann 風の見た目では、円どうしを接線でつなぎ、方向転換は円弧で行われる。

### Apply behavior

`Apply` は active layer に実アウトラインを追加する。

優先順位:

1. `Line` mode:
   - openでもclosedでも適用できる。
   - まずは接線点とarc近似点を通る open/closed `GSPath` として生成する。
2. `Filled` mode:
   - closed contour のときだけ適用。
   - closedでないときは何もしないか、Glyphs UI上で message/console warning。

Undo integration:

- Apply時は Glyphs undo grouping を使うのが望ましい。
- 例: `layer.beginChanges()` / `layer.endChanges()` が使えるか確認。

## 修正履歴

`a827484 chore: scaffold HofmannTool glyphs tool`

- repository 初期化後の SelectTool skeleton。
- `AGENTS.md` 原本 + `CLAUDE.md` symlink。
- `Info.plist`, `plugin.py`, `hofmann_geometry.py`, XIB/NIB, tests を追加。

`ee1797a fix: show compact inspector and candidate preview`

- Inspector を縦長から横長に変更。
- XIB を Auto Layout + 明示サイズ制約に変更。
- `view()` を明示し、Inspector表示経路を補強。
- クリックで start/target/candidate preview を最低限動かす処理を追加。

`b444f64 fix: localize and restyle inspector controls`

- 日本語ローカライズ追加。
- ラベル/入力欄/ボタン文字色をコード側で明示補正。
- 入力欄の文字色を黒、背景を白に固定。
- Inspector 幅を `360` から `326` に縮小。

## 次に直すべき順番

1. 円表示を実装する。
   - `Diameter` を使って全ノードに円を描く。
   - 小さい center dot は補助表示として残してよい。
2. 接線プレビューを直線 + 円弧にする。
   - `TangentCandidate` は `point_a`, `point_b`, `center_a`, `center_b`, `angle_a`, `angle_b`, `flow_a`, `flow_b` を持っている。
   - この情報から arc を描画する。
3. `Apply` を実装する。
   - まず `Line` mode で `GSPath` 追加。
   - その後 `Filled` mode を closed contour 限定で実装。
4. コマンドボタンを見た目上のボタンにする。
   - XIB上の `NSButton` style を見直す。
   - Glyphs inspector 上で flat text に見えるなら、3分割 segmented control にする案もあり。
5. Geometry tests を増やす。
   - 外接線/内接線の接点位置。
   - flow継続。
   - arc方向。
   - diameter >= distance の候補除外。
   - closed contour から path samples 生成。

## 開発/検証コマンド

```bash
python3 -m py_compile \
  HofmannTool.glyphsTool/Contents/Resources/plugin.py \
  HofmannTool.glyphsTool/Contents/Resources/hofmann_geometry.py

python3 -m unittest discover -s tests

ibtool HofmannTool.glyphsTool/Contents/Resources/InspectorView.xib \
  --compile HofmannTool.glyphsTool/Contents/Resources/InspectorView.nib
```

Glyphs install symlink:

```bash
ln -sf "$(pwd)/HofmannTool.glyphsTool" \
  "$HOME/Library/Application Support/Glyphs 3/Plugins/HofmannTool.glyphsTool"
```

Glyphs はプラグイン変更後に再起動する。

## Claudeへ渡すなら

依頼文例:

```text
この repo は Glyphs 3 用 SelectTool の HofmannTool です。
docs/CLAUDE_HANDOFF.md を読んで、まず以下を直してください。

1. Diameter の円を各グリッド点に描画する
2. 候補/確定プレビューを接線直線 + 円弧表示にする
3. Apply を Line mode から実装して active layer に GSPath を追加する
4. Apply/Undo/Clear が Glyphs inspector 上でボタンに見えるよう UI を調整する

Web版 hofmann-1.0.0 のコードはコピーせず、挙動の参考に留めてください。
検証は py_compile, unittest, ibtool compile を通してください。
```
