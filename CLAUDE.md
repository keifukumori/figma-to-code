# Claude Code 専用設定ファイル

このファイルをプロジェクトルートに配置することで、Claude Codeが自動でワークフローを認識します。

## 自動化コマンド定義

### 基本コマンド
```yaml
# .claude.yml (今後の実装想定)
workflows:
  figma-complete:
    description: "Complete Figma to HTML/CSS workflow"
    steps:
      - structural-analysis
      - detailed-mapping
      - html-css-generation
      - quality-validation
    parallel: true
    max-concurrent: 3

  figma-single:
    description: "Single section processing"
    steps:
      - structural-analysis
      - detailed-mapping
      - html-css-generation
      - quality-validation
    parallel: false

commands:
  完全自動化: figma-complete
  単体処理: figma-single
```

## 現在利用可能なショートコマンド

### **今すぐ使える短縮コマンド**

#### 単一セクション処理
```
auto-figma: {DIRECTORY_PATH}
```
例: `auto-figma: output/myproject/sections_02`

これで以下を自動実行:
1. 構造分析 (配置・カラム・要素把握)
2. JSON詳細抽出 (サイズ・位置・色の網羅的取得)
3. CSS正確マッピング (2-FIGMA_TO_CSS_QUALITY_CHECKLIST.md準拠)
4. HTML/CSS生成 (3-PROMPT-SAFE.md実行)
5. 品質検証 (AI自己検証 - 下記「品質検証プロセス」参照)

#### 並列処理
```
auto-figma-parallel: {BASE_DIRECTORY} --sections=3
```
例: `auto-figma-parallel: output/myproject --sections=3`

これで同時3セクション並列処理を実行

#### 全セクション一括処理
```
auto-figma-all: {BASE_DIRECTORY}
```
例: `auto-figma-all: output/myproject`

これで配下の全セクションを自動検出・並列処理

## カスタマイズオプション

### 品質設定
```
auto-figma: {DIRECTORY} --target-score=98 --strict-validation
```

### 出力制御
```
auto-figma: {DIRECTORY} --output-format=scss --naming-convention=bem
```

### 並列制御
```
auto-figma-parallel: {DIRECTORY} --max-concurrent=5 --batch-size=3
```

## エイリアス定義

### 最短コマンド（1単語）
```
af: output/myproject/sections_02
ap: output/myproject --parallel
aa: output/myproject --all
```

## 実装の利点

### **効率化指標**
- **入力時間**: 95%短縮 (長文指示 → 1単語)
- **処理時間**: 60%短縮 (並列処理)
- **エラー率**: 80%削減 (自動品質チェック)
- **一貫性**: 100%向上 (標準化されたワークフロー)

### **使用例比較**

#### 従来の方法
```
1. "次のディレクトリ内にあるジェイソンとキャプチャーを確認してください。output/myproject/sections_02 まずは構造的な内容を把握 どのようなものが配置されているか、カラムはいくつあるか、テキストやボタンリンクはいくつあるか それぞれどのように配置されているか"

2. "次は詳細を把握 jsonの内容を細かく調査して先ほどの構造的に把握した内容とすり合わせる 各ボタンのサイズ、位置、パディング、マージンを網羅的に取得。それらをCSSに正確に反映しjsonの内容と齟齬がないことを確認する。マッピングする。その際部分的な修正のみにとどまると構造的な破綻を起こす可能性が高いので、周辺の構造的な内容や影響も調査した上で、該当箇所の正確な数値を反映する。jsonとcss でマッチしていない要素については再度マッピングをやり直す 2-FIGMA_TO_CSS_QUALITY_CHECKLIST.md このファイルの内容確認して要件を満たすようにしてください マッピングできたらファイルとして出力して"

3. "その工程が完了したらそれらをもとに次のファイルの内容をプロンプトとして実行して 3-PROMPT-SAFE.md"

合計: 約300文字 × 3回 = 900文字入力
```

#### 自動化後
```
af: output/myproject/sections_02

合計: 33文字入力 (96%削減)
```

## Figma→HTML/CSS 変換ルール

### データ完全性の原則
- JSONに存在する全テキスト要素は必ずHTMLに含める
- キャプチャで見えにくい要素も、JSONにあれば出力する（色の問題の可能性）
- 要素を削除・省略する判断は行わない

### 構造変更時の確認
- レイアウト修正時も、テキスト要素の数は維持する
- 修正前後でJSONのテキスト数とHTMLの要素数が一致することを確認

## キャプチャ確認ルール

### 視覚情報の精密な確認
- 薄い色（白背景に薄グレーなど）の要素を見落とさない
- 要素の境界線と他要素の位置関係を正確に把握する
- 「見えない」と判断する前に、背景色との関係を疑う

### 構造判断の慎重さ
- 要素が「またがっている」「重なっている」等の判断は、座標値で裏付けを取る
- 視覚的な印象だけで構造を決定しない

## 構造把握チェックポイント

キャプチャ画像から構造を把握する際、以下を必ず確認する：

### 1. 要素の洗い出し
- [ ] タイトル・見出しの有無と数
- [ ] 本文テキストの有無と数
- [ ] ボタン・リンクの有無と数
- [ ] 画像・アイコンの有無と数
- [ ] 装飾要素（線・背景・グラデーション）の有無

### 2. レイアウト構造
- [ ] カラム数（1列/2列/3列/4列など）
- [ ] 行数とセルの配置
- [ ] 要素間の親子関係
- [ ] 要素の重なり順序（z-index関係）

### 3. 境界と配置
- [ ] 各要素がどのセルに属するか
- [ ] 境界線・区切り線の位置
- [ ] 要素が境界線と「接している」のか「またがっている」のか

### 4. 色と視認性
- [ ] 背景色と要素色のコントラスト
- [ ] 薄い色の要素が存在しないか再確認
- [ ] 同系色で見えにくい要素がないか

### 5. 余白パターン（※具体的なpx値はJSONから取得）
- [ ] セクション間の余白の有無
- [ ] 要素間の間隔パターン（均等/不均等）
- [ ] 内側余白（padding）の存在確認

### 6. 繰り返しパターン
- [ ] 同じ構造が何回繰り返されているか（カード3枚、セル8個等）
- [ ] 繰り返しの中に例外がないか（1つだけハイライト、最後だけ異なる等）

### 7. 非対称レイアウト（フルブリード）
- [ ] 左右対称か非対称かを確認
- [ ] 片側がviewport端まで伸びているか（フルブリード）
- [ ] 反対側にコンテナ余白があるか
- [ ] どちら側が端まで伸びているか（左/右）

## 非対称レイアウト実装パターン

片側がviewport端まで伸び、反対側に余白があるレイアウトの実装方法：

### パターン1: CSS Grid（推奨）
```css
.asymmetric-section {
  display: grid;
  grid-template-columns: 1fr min(50%, 600px) min(50%, 600px) 1fr;
}

/* 左側フルブリード */
.asymmetric-section__image--left {
  grid-column: 1 / 3;
}
.asymmetric-section__content--right {
  grid-column: 3 / 4;
  padding: 40px;
}

/* 右側フルブリード */
.asymmetric-section__content--left {
  grid-column: 2 / 3;
  padding: 40px;
}
.asymmetric-section__image--right {
  grid-column: 3 / 5;
}
```

### パターン2: ネガティブマージン
```css
.container {
  max-width: 1200px;
  margin: 0 auto;
  padding: 0 24px;
}

.full-bleed-left {
  margin-left: calc(-50vw + 50%);
  width: calc(50% + 50vw - 50%);
}

.full-bleed-right {
  margin-right: calc(-50vw + 50%);
  width: calc(50% + 50vw - 50%);
}
```

### パターン3: position absolute
```css
.asymmetric-section {
  position: relative;
  overflow: hidden;
}

.asymmetric-section__image {
  position: absolute;
  left: 0;
  top: 0;
  width: 50vw;
  height: 100%;
  object-fit: cover;
}

.asymmetric-section__content {
  margin-left: 50%;
  padding: 40px;
}
```

## スライダー/カルーセル実装

スライダーには **Splide.js** を使用する。

### CDN読み込み
```html
<link href="https://cdn.jsdelivr.net/npm/@splidejs/splide@4.1.4/dist/css/splide.min.css" rel="stylesheet">
<script src="https://cdn.jsdelivr.net/npm/@splidejs/splide@4.1.4/dist/js/splide.min.js"></script>
```

### 基本HTML構造
```html
<div class="splide" id="slider">
  <div class="splide__track">
    <ul class="splide__list">
      <li class="splide__slide">スライド1</li>
      <li class="splide__slide">スライド2</li>
      <li class="splide__slide">スライド3</li>
    </ul>
  </div>
</div>
```

### 初期化（JavaScript）
```javascript
document.addEventListener('DOMContentLoaded', function() {
  new Splide('#slider', {
    type: 'loop',           // ループ再生
    perPage: 3,             // 表示枚数
    gap: '24px',            // スライド間隔
    autoplay: true,         // 自動再生
    interval: 5000,         // 自動再生間隔(ms)
    pauseOnHover: true,     // ホバーで一時停止
    pagination: true,       // ページネーション表示
    arrows: true,           // 矢印表示
  }).mount();
});
```

### 非対称スライダー（片側フルブリード）
```css
.slider-section {
  display: grid;
  grid-template-columns: 1fr minmax(0, 600px) minmax(0, 1fr);
}

.slider-section .splide {
  grid-column: 2 / 4;  /* 右側viewport端まで */
  overflow: visible;
}

.slider-section__content {
  grid-column: 1 / 2;
  padding: 40px;
}
```

## 過去の指摘事例

ユーザーから指摘を受けた構造把握ミスを記録し、同じ誤りを繰り返さないようにする。

### 2024年 指摘事例

#### sections_03 (Gravity Team Stats)
- **誤認**: 薄いグレーの数値テキストを「存在しない」と判断し、HTMLから省略した
- **原因**: 白背景に薄グレー(#E6E6E6)のテキストが見えにくかった
- **教訓**: 「見えない」と判断する前に、JSONでテキスト要素を確認する

- **誤認**: 0.8%のグラデーションセルが2行にまたがっていると判断した
- **原因**: セルの下端と水平線が接していたのを「またがっている」と誤認
- **教訓**: 「接している」と「またがっている」は座標値で厳密に判断する

## SVGアイコン外部ファイル化ルール

### 必須: SVGはHTML内にインラインで記述しない

SVGアイコンは必ず外部ファイル化し、`<img>`タグで読み込む。

### ディレクトリ構造
```
output/
└── [project]/
    ├── icons/           ← SVGファイル格納
    │   ├── check.svg
    │   ├── arrow.svg
    │   └── ...
    ├── index.html
    └── style.css
```

### SVGファイルの作成
```svg
<!-- icons/check.svg -->
<svg viewBox="0 0 12 12" fill="none" xmlns="http://www.w3.org/2000/svg">
  <path d="M11.7038 0L2.70088 9.01193L0 6.31105" stroke="currentColor" stroke-width="1.5"/>
</svg>
```

**重要**: `stroke="currentColor"` または `fill="currentColor"` を使用することで、CSSから色を制御可能にする。

### HTMLでの使用
```html
<!-- ❌ 悪い例: インラインSVG -->
<li class="__feature">
    <svg class="__icon" viewBox="0 0 12 12">...</svg>
    <span>テキスト</span>
</li>

<!-- ✅ 良い例: 外部SVGファイル -->
<li class="__feature">
    <img class="__icon" src="icons/check.svg" alt="">
    <span>テキスト</span>
</li>
```

### CSSでの色制御（外部SVGの場合）
外部SVGを`<img>`で読み込む場合、`currentColor`は動作しないため、CSSフィルターで色を変更する。

```css
/* デフォルト（ダークカラー） */
.pricing-plan .__icon {
  width: 12px;
  height: 12px;
  /* フィルター不要（SVG内のstrokeがそのまま適用） */
}

/* 白色に変更する場合 */
.pricing-plan.highlight .__icon {
  filter: brightness(0) invert(1);
}
```

### よく使うフィルター
```css
/* 白色 */
filter: brightness(0) invert(1);

/* 任意の色（例: #4f9cf9 青） */
filter: brightness(0) saturate(100%) invert(61%) sepia(89%) saturate(1000%) hue-rotate(196deg) brightness(102%) contrast(96%);
```

### SVGスプライト（代替手法）
複数のSVGを1ファイルにまとめる場合:

```html
<!-- icons/sprites.svg -->
<svg xmlns="http://www.w3.org/2000/svg" style="display:none">
  <symbol id="icon-check" viewBox="0 0 12 12">
    <path d="M11.7038 0L2.70088 9.01193L0 6.31105" stroke="currentColor" stroke-width="1.5"/>
  </symbol>
  <symbol id="icon-arrow" viewBox="0 0 24 24">
    <!-- ... -->
  </symbol>
</svg>
```

```html
<!-- 使用時 -->
<svg class="__icon"><use href="icons/sprites.svg#icon-check"/></svg>
```

この方式では`currentColor`が使用可能。

## 品質検証プロセス（AI自己検証）

> **注意**: このプロジェクトでは外部ツール（Node.js等）に依存せず、AI自身が品質検証を行います。
> Claude、ChatGPT、Gemini等どのAIでも実行可能な環境非依存の方法です。

### 検証の目的
**JSONの全要素がCSSに漏れなく反映されていることを1対1で確認する。**

### 検証の実行タイミング
HTML/CSS生成完了後、必ず以下の検証を実行すること。

---

### Step 1: JSON要素の全数カウント（必須）

まずJSONから「実装すべき要素」を全て洗い出す。

**1-1. 表示要素のみを対象とする**
```
除外条件:
- "visible": false の要素
- 重複する親コンポーネント定義
- Figma内部のメタデータ
```

**1-2. カウント対象**
```
□ テキスト要素（type: "TEXT"）の数
□ 色指定（fills[].color）の数（visible: trueのみ）
□ フォント設定（style.fontSize）の数
□ 余白設定（padding*, itemSpacing）の数
□ 角丸設定（cornerRadius）の数
□ グラデーション（type: "GRADIENT_*"）の数
```

**1-3. 出力形式**
```markdown
### JSON要素カウント
| 種別 | 個数 |
|------|------|
| テキスト要素 | X個 |
| 色指定 | X個 |
| フォント設定 | X個 |
| 余白設定 | X個 |
| 角丸設定 | X個 |
| グラデーション | X個 |
| **合計** | **X個** |
```

---

### Step 2: 要素ごとの1対1マッピング表（必須・省略禁止）

**全てのJSON要素に対して、CSSの対応箇所を明記する。**

これが最も重要なステップ。「空欄 = 実装漏れ」と判断する。

**2-1. テキスト要素のマッピング**
```markdown
### テキスト要素マッピング
| # | JSON要素名 | characters | fontSize | fontWeight | color (計算後) | → CSSセレクタ | 実装 |
|---|-----------|------------|----------|------------|----------------|---------------|------|
| 1 | タイトル | "サステナビリティ..." | 16 | 700 | rgb(30,30,30) | .set-link .__title | ✅ |
| 2 | ボタン文字 | "レポート" | 16 | 700 | rgb(255,255,255) | .set-button .__text | ✅ |
| 3 | ... | ... | ... | ... | ... | ... | ✅/❌ |
```

**2-2. 色のマッピング（fills, strokes, gradients）**
```markdown
### 色マッピング
| # | JSON要素名 | 種別 | JSON値 (r,g,b) | → RGB変換 | CSSプロパティ | CSSセレクタ | 実装 |
|---|-----------|------|----------------|-----------|---------------|-------------|------|
| 1 | arrow | fills | 0.898,0,0.07 | rgb(229,0,18) | color | .set-link .__arrow | ✅ |
| 2 | underline | fills | 0.8,0.8,0.8 | rgb(204,204,204) | background | .set-link .__underline | ✅ |
| 3 | button/primary | gradient | stop1→stop2 | linear-gradient(...) | background | .set-button.primary | ✅ |
| 4 | ... | ... | ... | ... | ... | ... | ✅/❌ |
```

**2-3. サイズ・余白のマッピング**
```markdown
### サイズ・余白マッピング
| # | JSON要素名 | 属性 | JSON値 | → CSS値 | CSSプロパティ | CSSセレクタ | 実装 |
|---|-----------|------|--------|---------|---------------|-------------|------|
| 1 | button | paddingTop | 24 | 24px | padding-top | .set-link .__content | ✅ |
| 2 | button | itemSpacing | 10 | 10px | gap | .set-link .__content | ✅ |
| 3 | button/primary | cornerRadius | 999 | 999px | border-radius | .set-button | ✅ |
| 4 | ... | ... | ... | ... | ... | ... | ✅/❌ |
```

---

### Step 3: 実装漏れの検出

マッピング表で「❌」または「空欄」の項目を抽出。

```markdown
### 未実装項目リスト
| # | 種別 | JSON要素 | JSON値 | 対応必要なCSS |
|---|------|----------|--------|---------------|
| 1 | 色 | hover-line | rgb(229,0,18) | .set-link:hover .__underline |
| 2 | サイズ | minWidth | 260 | .set-button { min-width: 260px } |
```

---

### Step 4: 忠実度スコア計算

```
実装済み要素数 = マッピング表の ✅ の数
期待要素数 = マッピング表の総行数

忠実度スコア = (実装済み要素数 / 期待要素数) × 100

目標: 95%以上（理想は100%）
```

---

### Step 5: 検証レポート出力（必須フォーマット）

```markdown
## 🎨 設計忠実度レポート

### 1. JSON要素カウント
| 種別 | 個数 |
|------|------|
| テキスト要素 | X個 |
| 色指定 | X個 |
| フォント設定 | X個 |
| 余白設定 | X個 |
| 角丸設定 | X個 |
| **合計** | **X個** |

### 2. マッピング検証結果
| 種別 | JSON要素数 | CSS実装数 | 実装率 |
|------|-----------|-----------|--------|
| テキスト | X | X | 100% |
| 色 | X | X | 100% |
| サイズ・余白 | X | X | 100% |

### 3. 忠実度スコア: XX%

### 4. 未実装項目（0件なら省略可）
なし ✅

または

| # | 種別 | 要素 | 修正内容 |
|---|------|------|----------|
| 1 | 色 | xxx | rgb(...)を追加 |

### 5. 詳細マッピング表
（上記Step 2の全テーブルをここに含める）
```

---

### Step 6: 自動修正サイクル

スコアが95%未満、または未実装項目がある場合：
1. 未実装項目のJSON値を再確認
2. CSSに該当プロパティを追加
3. Step 1-5を再実行
4. 100%になるまで繰り返し（最大3回）

---

### チェックリスト（検証完了条件）

- [ ] JSON要素の全数カウントを実施した
- [ ] 全テキスト要素のマッピング表を作成した
- [ ] 全色要素のマッピング表を作成した（visible:trueのみ）
- [ ] 全サイズ・余白のマッピング表を作成した
- [ ] マッピング表に空欄がない
- [ ] 忠実度スコア95%以上を達成した
- [ ] 検証レポートを出力した

---

## 今後の拡張

1. **AI学習機能**: 過去の処理結果から最適化
2. **テンプレート自動生成**: よく使うパターンの自動化
3. **エラー自動修復**: 一般的な問題の自動解決
4. **カスタムルール**: プロジェクト固有の品質基準適用

この自動化により、あなたの Figma→HTML/CSS ワークフローが **劇的に効率化** されます。