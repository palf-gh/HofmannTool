# HofmannTool Handoff for Claude

最終更新: 2026-04-30 (操作履歴/UI整理後)
作業ブランチ: `feature/tool-history-ui`
直前HEAD: `b444f64 fix: localize and restyle inspector controls`

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
  - 円弧/Bezier: `candidate_radius`, `arc_to_bezier_segments`。
- `HofmannTool.glyphsTool/Contents/Resources/InspectorView.xib`
  - 横長の Inspector UI。
- `HofmannTool.glyphsTool/Contents/Resources/InspectorView.nib`
  - `ibtool` で生成済み。
- `tests/test_hofmann_geometry.py`
  - geometry module の最小テスト。

現在できること:

- Glyphs でツールとしてロードされる。
- active layer の body box 中央に unit grid を描画する。
- Inspector で `Rows`, `Cols`, `Spacing`, `Diameter`, `X`, `Y`, 出力モードを設定できる。
- グリッド、ノード、候補は常時表示。ラベル表示機能は削除済み。
- 日本語環境ではラベルが日本語になる。
- 各グリッド点に直径 `Diameter` の円を薄く描く。中心 dot は補助表示として残る。
- 開始/アクティブノードは円が太線+色で強調される。
- クリックで開始ノードを選び、次ノードクリックで接線候補を表示し、候補クリックで確定。
- 候補プレビューは「直前 segment からの接続円弧 + 接線直線 + 閉じる場合は閉じ円弧」を表示。
- 確定プレビューは「接線直線 + 各コーナー円弧」を表示。閉じた contour では closePath。
- 選択済みルートは node/flow の履歴として保持し、`Diameter`, `Spacing`, offset 変更時に現在設定で接線を再計算する。
- `Cmd+Z` / `Shift+Cmd+Z` でツール内の選択履歴を undo/redo できる。`Clear` も undo 対象。
- ツール内履歴がある間は Edit メニューの Undo/Redo ターゲットを HofmannTool に一時差し替えし、Glyphs 本来の Undo/Redo が同時に走らないようにする。履歴が空になるかツールを離れたら復元する。
- `Apply`:
  - `Line` モード: open でも closed でも `GSPath` を生成して active layer に追加。closed contour でも `GSPath.closed=False` のままにし、塗り形状にはしない。
  - `Filled` モード: closed のときだけ `GSPath.closed=True` で追加、未 closed 時はコンソール警告。
  - 円弧は polyline ではなく、`GSNode(OFFCURVE)` + `GSNode(CURVE)` の cubic Bezier で近似。
  - Bezier の on-curve node は、円弧が 0/90/180/270 度の極点をまたぐ場合に必ずそこで分割する。
  - `layer.beginChanges()` / `endChanges()` を使って Glyphs の undo grouping に統合。
- `Apply` 後はツールの選択状態とツール内履歴をクリアする。
- `Apply`, `Clear` は inspector 下段に標準サイズの押しボタンとして並ぶ。

現在できない/不完全なこと:

- 候補ホバー強調や、複数候補の見分けやすさ (色/dash) はまだ未調整。
- `Apply` 時に Glyphs 側 Undo メニューに専用名 (例: "Apply Hofmann Tangents") は付いていない。

## ユーザーからの最新フィードバック

2026-04-30:

- 「直径サイズで円が描画されるべき」 → 対応済 (各ノードに `Diameter` 円を描画)。
- 現在の接続線表示が変に見える → 対応済 (接線直線 + 円弧プレビュー)。
- `Apply` を押しても何も起きない → 対応済 (`GSPath` を active layer に追加、Line/Filled mode 切替)。
- `Apply`, `Undo`, `Clear` がボタンに見えない → 対応済 (標準サイズの rounded push button、底部に 3 等分配置)。
- 「円弧作るの逆だと思う」 → 対応済 (flow ラベルの CW/CCW semantics を修正)。
- 「トレースしてポイント作らないでちゃんとベジェ曲線で近似」 → 対応済 (polyline 書き出しを廃止し、cubic Bezier を出力)。
- 「フォントという特性上極点にノードがあったほうがいい」 → 対応済 (0/90/180/270 度をまたぐ円弧は必ずそこで分割)。
- 「グリッド/ノード/候補は常時表示、ラベル不要」 → 対応済 (表示チェックボックスとラベル描画を削除)。
- 「半径変更時に既存分も追随」 → 対応済 (node/flow から接線を再計算)。
- 「戻すボタンを排除して Cmd+Z / Shift+Cmd+Z」 → 対応済 (ツール内履歴 100 件)。
- 「既存の Cmd+Z / Shift+Cmd+Z も機能してしまう」 → 対応済 (ツール内履歴中だけ Edit メニューの Undo/Redo を一時的に横取り)。
- いったん Claude に投げられるよう、仕様書、参考コード、現状修正点をまとめたい → 本ドキュメント。

## 期待仕様

### Inspector

横長配置を維持する。現在の幅は `326`, 高さは `124` (ボタン行を確保するため `104` から拡張)。

操作項目:

- `Rows` / `行`
- `Cols` / `列`
- `Spacing` / `間隔`
- `Diameter` / `直径`
- `X`, `Y` offset
- output mode: `Filled` / `塗り`, `Line` / `線`
- commands: `Apply` / `適用`, `Clear` / `消去`
- undo/redo: `Cmd+Z`, `Shift+Cmd+Z`

UI改善希望:

- `Apply`, `Clear` は明確に押せるボタンとして見えること。
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

未コミットの作業 (本ハンドオフ後の修正):

- geometry に `candidate_radius`, `arc_to_bezier_segments` を追加し、テストを 6 → 15 に増やす。
- flow ラベルの CW/CCW semantics を修正し、接線点が実際の進行方向と一致するようにした。
- plugin で各ノードに `Diameter` 円を描画。アクティブ/開始ノードは太線+色で強調。
- 接線+Bezier 円弧プレビュー (候補/確定共通) を実装。
- `applyAction_` を実装。Line/Filled モードに対応し、円弧は `OFFCURVE`/`CURVE` ノードで出力。Line mode は closed contour でも `GSPath.closed=False`、Filled mode は closed contour のみ `True`。`layer.beginChanges()` で undo に統合。
- Inspector 高さを `104` → `124` に拡張し、底部に 3 つの標準サイズ rounded push button を配置。
- Apply/Undo/Clear のタイトル色オーバーライドを停止 (システム既定の bezel が活きるように)。
- 表示チェックボックスと Undo ボタンを削除し、Inspector 高さを `96` に縮小。
- ツール内履歴を追加し、`Cmd+Z` / `Shift+Cmd+Z` で選択、候補表示、候補確定、Clear を undo/redo 可能にした。
- ツール内履歴がある間は Edit メニューの Undo/Redo を一時的に HofmannTool へ向け、履歴が空になったら元の target/action に戻す。

## 次に直すべき順番

1. ~~円表示を実装する~~ → 完了。
2. ~~接線プレビューを直線 + 円弧にする~~ → 完了 (描画/Apply 双方)。
3. ~~`Apply` を実装する~~ → 完了 (Line / Filled mode 切替, undo grouping 込み)。
4. ~~コマンドボタンを見た目上のボタンにする~~ → 完了 (rounded push button, 標準サイズ)。
5. ~~円弧 → cubic bezier 近似で `GSPath` に書き出す~~ → 完了。
   - `GSNode(OFFCURVE)` + `GSNode(CURVE)` で最大 90° ごとに分けて出力。
   - 0/90/180/270 度の極点をまたぐ場合、必ずそこで on-curve node を置く。
   - 制御点の長さは `radius * (4/3) * tan(theta/4)`。
6. Inspector のホバー強調や候補の色分け。
   - 4 候補のうちカーソルに最近いものを濃く描き、他を薄く描く。
   - 内接線/外接線で dash パターンを変える案もあり。
7. Apply 時の Glyphs Undo メニュー名指定。
   - `layer.beginChanges()` 周りで `Glyphs.font.parent.windowController().undoManager()` を取得して
     `setActionName_("Apply Hofmann Tangents")` を呼べるか確認する。
   - ツール内に undo/redo 履歴があるときは `Cmd+Z` / `Shift+Cmd+Z` をツール側で消費する。Apply 後はツール履歴をクリアするため、Glyphs 側 undo に戻る想定。
8. Geometry tests の追補。
   - flow 継続失敗時に候補が空になること。
   - Bezier 円弧が flow 方向どおりに進むこと (現テストで CCW/CW を確認済)。
   - closed contour の最終円弧が Glyphs 上で期待どおり閉じることの手動確認。

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

1. Glyphs 上で closed contour の Apply 結果を確認し、閉じ円弧の node type が崩れる場合は修正する
2. 候補ホバー強調や候補ごとの見分けやすさを改善する
3. Apply 時の Glyphs Undo メニュー名を付けられるか確認する
4. flow 継続失敗時や無効直径のテストを追加する

Web版 hofmann-1.0.0 のコードはコピーせず、挙動の参考に留めてください。
検証は py_compile, unittest, ibtool compile を通してください。
```
