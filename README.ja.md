# HofmannTool

[English README](README.md)

ユニットグリッドの上に Hofmann 風の接線パスをスケッチし、`GSPath` として
アクティブレイヤーに書き出すための Glyphs 3 用ツールです。

エディットビュー上で直接動作します。最初のノードを選び、次の接線候補を
順にクリックしていくと輪郭が組み上がり、最初のノードに戻れば閉じた contour
として確定できます。インスペクタでは行・列・間隔・オフセットなどのグリッド
設定と、円の直径を指定します。出力は `Filled`（塗り）、`Hole`（穴 / 向き反転）、
`Line`（中心線）の3モードから選べます。

## 機能

- 行数・列数・間隔・オフセットを設定できるグリッド上の円。
- 接線ルート組み立て: ノードをクリック → 次のノードをクリック → 候補接線が
  表示されるのでクリックで確定、を繰り返してパスを伸ばします。
- 出力モード `Filled` / `Hole` / `Line`。`Hole` は同じ閉じパスを向き反転して
  穴として使えるようにします。
- `Cmd` を押しながらノードをクリックすると、ルート編集とは独立にその位置に
  単独の閉じた円を書き出します。向きは現在のモード（`Filled` / `Hole`）に
  従います。
- ツール内の `Cmd+Z` / `Shift+Cmd+Z` 履歴で選択・候補・確定・Clear を
  undo/redo できます。ツール履歴が残っている間は Glyphs 本体の Undo は
  一時的に止まります。
- インスペクタは英語と日本語にローカライズされています。

## インストール

1. このリポジトリをクローンまたはダウンロードします。
2. Finder で `HofmannTool.glyphsTool` をダブルクリックするか、Plugins
   フォルダにシンボリックリンクを作ります:

   ```bash
   ln -sf "$(pwd)/HofmannTool.glyphsTool" \
     "$HOME/Library/Application Support/Glyphs 3/Plugins/HofmannTool.glyphsTool"
   ```

3. Glyphs 3 を再起動し、ツールバーから **Hofmann Tool** を選びます
   （デフォルトショートカット `H`）。

## 使い方

1. Hofmann Tool を選ぶと、アクティブレイヤー上にグリッドと候補円が表示
   されます。
2. グリッドノードをクリックして開始の円を決めます。
3. 次のノードをクリックすると候補接線が描画されるので、採用したい候補を
   クリックして確定します。アクティブノードが次の端点に移ります。
4. 繰り返して開始ノードに戻ると contour が閉じます。
5. `Filled` / `Hole` / `Line` を選び **Apply** を押すと `GSPath` が
   アクティブレイヤーに追加されます。
6. `Cmd` を押しながら任意のノードをクリックすると、そのノードに単独の円が
   書き出されます。向きは現在のモードに従います（`Hole` のときは反転）。

`Clear` で組み立て中のルートをリセットできます。`Cmd+Z` / `Shift+Cmd+Z` は
ツール履歴がある間のみ、ルートステップや Clear を undo / redo します。

## 設定

`Glyphs.defaults` 内の `com.palf.HofmannTool.<key>` に保存されます:

| キー | 型 | デフォルト | 備考 |
| --- | --- | --- | --- |
| `rows` | int | 4 | 行数 |
| `cols` | int | 4 | 列数 |
| `spacing` | float | 120 | グリッド間隔（ユニット） |
| `diameter` | float | 80 | 円の直径（ユニット） |
| `xOffset` | float | 0 | グリッド水平オフセット（ユニット） |
| `yOffset` | float | 0 | グリッド垂直オフセット（ユニット） |
| `outputMode` | string | `filled` | `filled` / `hole` / `centerline` |

グリッドは水平方向に `layer.width`、垂直方向に `ascender` / `descender` の
ボディボックスで中心揃えされます。

## 開発

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

## ライセンス

Apache License 2.0。詳細は [LICENSE](LICENSE) を参照してください。
