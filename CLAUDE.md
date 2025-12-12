# Claude Code 専用設定ファイル

このファイルをプロジェクトルートに配置することで、Claude Codeが自動でワークフローを認識します。

---

## ⛔ 最優先: JSON前処理（絶対に最初に実行）

> **警告**: figma-data.json は数MB〜数十MBになることがあり、AIが直接読み込むとコンテキストを圧迫します。
> **必ず以下のスクリプトを最初に実行し、extracted.md を生成してから作業を開始してください。**

### 実行コマンド
```bash
python3 scripts/extract_figma.py {パス}/figma-data.json
```

### 例
```bash
# デスクトップ版
python3 scripts/extract_figma.py figma-assets/sample/sections/pricing/desktop/figma-data.json

# モバイル版（存在する場合）
python3 scripts/extract_figma.py figma-assets/sample/sections/pricing/mobile/figma-data.json
```

### 結果
- 入力: `figma-data.json` (5MB+)
- 出力: `extracted.md` (10KB程度) ← **これを読む**
- サイズ削減率: 99%以上

### ワークフロー
```
1. python3 scripts/extract_figma.py でextracted.md生成

2. キャプチャ画像(figma-capture.png)で構造把握 ← 重要！
   - 全体レイアウト: カラム数、行数、配置パターン
   - 要素の種類: 見出し、本文、ボタン、リンク、画像、アイコン
   - 要素の数: テキスト○個、ボタン○個、カード○枚など
   - 繰り返しパターン: 同じ構造が何回あるか
   - 特殊要素: ハイライト、装飾線、グラデーション
   ※詳細は「構造把握チェックポイント」セクション参照

3. extracted.md を読み込む（JSONは読まない！）
   - 構造把握した内容と数値データを突き合わせる

4. HTML/CSS生成

5. 品質検証
```

**❌ 禁止**: figma-data.json を直接 Read ツールで読み込むこと
**✅ 正解**: extracted.md を読み込むこと

---

## 🚨 クイックリファレンス（必読）

**CSS/HTML生成前に必ずこのセクションを確認すること。**

### 1. CSS命名規則（スコープドBEM）

| 階層 | 命名パターン | 例 |
|------|-------------|-----|
| セクション | ハイフン繋ぎ | `.chat`, `.home`, `.cart` |
| パーツ（第1階層） | セクション名-パーツ名 | `.chat-header`, `.chat-messages` |
| 内部要素（第2階層以下） | `.__` プレフィックス | `.__title`, `.__icon`, `.__text` |
| Modifier | `.__` プレフィックス | `.__sent`, `.__received`, `.__active` |

```scss
// ✅ 正しい例
.chat { ... }
.chat-header { ... }
.chat-header .__title { ... }
.chat-messages .__bubble { ... }
.chat-messages .__bubble.__sent { ... }

// ❌ 間違い例
.chat__header { ... }                    // パーツにアンダースコア使用
.chat__message--received { ... }         // 標準BEMのModifier
.chat-messages__bubble__text { ... }     // 深いネスト
```

### 2. HTMLタグ選択ルール（セマンティックHTML）

| 用途 | 使用タグ | 禁止 |
|------|----------|------|
| 画像 | `<figure>` | `<div>` |
| 画像キャプション | `<figcaption>` | `<span>`, `<p>` |
| カード一覧（複数） | `<ul><li>` | `<div>`の羅列 |
| 独立記事本文 | `<article>` | - |
| ナビゲーション | `<nav>` | `<div>` |
| セクション | `<section>` | `<div>` |

```html
<!-- ✅ 正しい例 -->
<ul class="blog-cards">
  <li class="blog-card">
    <figure class="__image">
      <img src="..." alt="...">
    </figure>
    <div class="__content">
      <h3 class="__title">タイトル</h3>
      <a href="#" class="__link">Readmore</a>
    </div>
  </li>
  <li class="blog-card">...</li>
</ul>

<!-- ❌ 間違い例 -->
<div class="blog-cards">
  <div class="blog-card">
    <div class="blog-card__image">
      <img src="...">
    </div>
  </div>
</div>
```

### 3. データ完全性の原則

- **JSONに存在する全要素は必ずHTMLに出力する**
- キャプチャで見えにくい要素もJSONにあれば含める
- 要素の削除・省略は行わない
- 修正前後でJSONのテキスト数とHTMLの要素数が一致することを確認

### 3. 品質検証プロセス（概要）

HTML/CSS生成後、以下を必ず実行：

1. **JSON要素の全数カウント** - テキスト、色、フォント、余白、角丸などを数える
2. **1対1マッピング表作成** - 全JSON要素にCSSの対応箇所を明記（空欄＝実装漏れ）
3. **忠実度スコア計算** - 目標95%以上

---

## ⚠️ CSS生成前チェックポイント

**以下の質問にすべて「はい」と答えられるまでCSS生成を開始しない：**

```
□ スコープドBEM命名規則を理解した
  - パーツは「セクション名-パーツ名」で命名する
  - 内部要素は「.__」プレフィックスを使う
  - 標準BEMの「__」「--」は使わない

□ JSONを全て読み込んだ
  - テキスト要素の数を把握した
  - 色指定（fills）の数を把握した
  - サイズ・余白の値を確認した

□ キャプチャ画像を確認した
  - 薄い色の要素を見落としていないか確認した
  - レイアウト構造（カラム数、行数）を把握した
  - 繰り返しパターンの数を確認した

□ 生成後に1対1マッピング検証を行う準備がある
```

---

## ⚠️ 作業環境の制約（Claude Code使用時）

> **注意**: このセクションはClaude Code特有の制約です。他のAIツールを使用する場合は適用されません。

### Git Worktree禁止
- **このプロジェクトではgit worktreeを使用しない**
- 必ずメインリポジトリ `/Users/fukumorikei/figma-to-code` で作業すること
- 理由: Claude Codeのworktree環境ではnvmのパスが通らず、npmが動作しないため

---

## ディレクトリ対応ルール

### 基本原則
`figma-assets/{プロジェクト名}/` の内容は `src/{プロジェクト名}/` に統合して出力する。

```
figma-assets/myproject/        →    src/myproject/
├── gravity/                        ├── _includes/
│   ├── figma-data.json                 ├── gravity-stats.html
│   └── figma-capture.png               └── blog-section.html
└── blog-section/                   ├── scss/
    ├── figma-data.json                 ├── style.scss
    └── figma-capture.png               ├── _gravity-stats.scss
                                        └── _blog-section.scss
                                    └── index.html
```

### 対応関係
| figma-assets | src | 説明 |
|--------------|-----|------|
| `/{プロジェクト名}/` | `/{プロジェクト名}/` | 1プロジェクト = 1ディレクトリ |
| `/{プロジェクト名}/{セクション}/` | `/_includes/{セクション}.html` | 各セクション = 1インクルードファイル |

### 禁止事項
- `figma-assets/` に対応するプロジェクトが存在しない `src/` ディレクトリを勝手に作成しない
  - ✅ OK: `figma-assets/f/` があるから `src/f/` を作成
  - ❌ NG: `figma-assets/` に存在しない `src/random-project/` を勝手に作成
- figma-assetsの各セクションを別プロジェクトとして分離しない

### 作業フロー
1. `figma-assets/{プロジェクト名}/` 内のセクション一覧を確認
2. `src/{プロジェクト名}/` が存在するか確認（なければ作成）
3. 各セクションを `_includes/` と `scss/` に配置
4. `index.html` で全セクションを `@@include` で統合

---

## 現在利用可能なショートコマンド

### **今すぐ使える短縮コマンド**

#### 単一セクション処理
```
auto-figma: {DIRECTORY_PATH}
```
例: `auto-figma: output/myproject/sections_02`

これで以下を自動実行:
1. **JSON前処理スクリプト実行** (大きなJSONを軽量Markdownに変換)
   ```bash
   python3 scripts/extract_figma.py {DIRECTORY}/figma-data.json
   ```
   → `extracted.md` が生成される（99%サイズ削減）
2. 構造分析 (キャプチャ画像 + extracted.md で配置・カラム・要素把握)
3. CSS正確マッピング (extracted.mdの値をそのまま使用)
4. HTML/CSS生成 (3-PROMPT-SAFE.md実行)
5. 品質検証 (AI自己検証 - 下記「品質検証プロセス」参照)

---

> **並列処理について**: 並列処理機能は現在停止中です。詳細は `CLAUDE-PARALLEL.md` を参照してください。

## カスタマイズオプション

### 品質設定
```
auto-figma: {DIRECTORY} --target-score=98 --strict-validation
```

### 出力制御
```
auto-figma: {DIRECTORY} --output-format=scss --naming-convention=bem
```

## エイリアス定義

### 最短コマンド（1単語）
```
af: output/myproject/sections_02
```

## 実装の利点

### **効率化指標**
- **入力時間**: 95%短縮 (長文指示 → 1単語)
- **エラー率**: 80%削減 (自動品質チェック)
- **一貫性**: 100%向上 (標準化されたワークフロー)

## Figma→HTML/CSS 変換ルール

### CSS命名規則（スコープドBEM）

クラス名の冗長な繰り返しを避け、階層に応じた命名規則を使用する。

---

#### 階層ルール

| 階層 | 命名 | 例 |
|------|------|-----|
| セクション | ハイフン繋ぎ | `.chat`, `.home`, `.cart` |
| パーツ（第1階層） | セクション名-パーツ名 | `.chat-header`, `.chat-messages`, `.home-banner` |
| 内部要素（第2階層以下） | `.__` プレフィックス | `.__title`, `.__icon`, `.__text` |
| Modifier | `.__` プレフィックス（並列） | `.__sent`, `.__received`, `.__active` |

**ポイント**:
- パーツ（独立したUIブロック）はフルネームで記述し、所属セクションを明確にする
- 内部要素とModifierは同じ`.__`を使う。区別はHTML構造で判断
  - Element: 子要素に付与
  - Modifier: 同じ要素に付与（パーツと並列）

---

#### 判断基準

パーツ（フルネーム）にするかどうか：
- **独立したUIブロック**として認識できる → フルネーム（`chat-header`）
- **親要素の一部**として認識される → スコープド（`.__title`）

例：
- ヘッダー、メッセージエリア、入力欄 → 独立ブロック → `chat-header`, `chat-messages`, `chat-input`
- タイトル、アイコン、ボタン → 親の一部 → `.__title`, `.__icon`, `.__btn`

---

#### HTML例

**❌ 悪い例（冗長）:**
```html
<section class="chat">
  <header class="chat__header">
    <button class="chat__back-btn">
      <img class="chat__icon">
    </button>
    <h1 class="chat__title">Brooke Davis</h1>
  </header>
  <div class="chat__messages">
    <div class="chat__message chat__message--received">
      <div class="chat__bubble chat__bubble--with-name">
        <span class="chat__sender">Brooke</span>
        <p class="chat__text">Hey!</p>
      </div>
    </div>
  </div>
</section>
```

**✅ 良い例（階層ルール適用）:**
```html
<section class="chat">
  <!-- 第1階層: フルネーム -->
  <header class="chat-header">
    <!-- 第2階層以下: スコープド -->
    <button class="__back-btn">
      <img class="__icon">
    </button>
    <h1 class="__title">Brooke Davis</h1>
  </header>

  <!-- 第1階層: フルネーム -->
  <div class="chat-messages">
    <!-- 第2階層以下: スコープド + Modifier -->
    <div class="__message __received">
      <div class="__bubble __with-name">
        <span class="__sender">Brooke</span>
        <p class="__text">Hey!</p>
      </div>
    </div>
    <div class="__message __sent">
      <div class="__bubble">
        <p class="__text">Hi!</p>
      </div>
    </div>
  </div>

  <!-- 第1階層: フルネーム -->
  <div class="chat-input">
    <button class="__add-btn">
      <img class="__icon">
    </button>
    <input class="__field" type="text">
  </div>
</section>
```

---

#### SCSS対応

```scss
// セクション
.chat {
  max-width: 375px;
  margin: 0 auto;
}

// パーツ（第1階層）
.chat-header {
  display: flex;
  align-items: center;
  padding: 8px 24px;

  // 内部要素（第2階層以下）
  .__back-btn {
    width: 24px;
    height: 24px;
  }

  .__title {
    flex: 1;
    text-align: center;
    font-weight: 700;
  }

  .__icon {
    width: 24px;
    height: 24px;
  }
}

// パーツ（第1階層）
.chat-messages {
  padding: 16px 24px;

  // 内部要素 + Modifier
  .__message {
    display: flex;
    margin-bottom: 16px;

    &.__received { justify-content: flex-start; }
    &.__sent { justify-content: flex-end; }
  }

  .__bubble {
    padding: 12px 16px;
    border-radius: 20px;

    &.__with-name { padding-top: 8px; }
  }

  // received/sent による色分け
  .__message.__received .__bubble {
    background: #f7f9fe;
  }

  .__message.__sent .__bubble {
    background: #006ffd;
    color: #fff;
  }

  .__sender {
    font-size: 12px;
    font-weight: 700;
  }

  .__text {
    font-size: 14px;
  }
}

// パーツ（第1階層）
.chat-input {
  display: flex;
  align-items: center;
  padding: 12px 24px;

  .__add-btn { ... }
  .__field { ... }
}
```

---

#### Modifier（状態変化・バリエーション）

```html
<!-- パーツ + Modifier -->
<div class="accordion-item __open">
  <button class="__header">...</button>
</div>

<!-- 複数Modifier -->
<a href="#" class="set-button __primary __large">
```

```scss
.accordion-item {
  .__header { ... }
  .__content { display: none; }

  // Modifier
  &.__open {
    .__header { background: #fef8db; }
    .__content { display: block; }
  }
}

.set-button {
  &.__primary { background: linear-gradient(...); }
  &.__secondary { border: 2px solid transparent; }
  &.__large { padding: 24px 48px; }
}
```

---

#### 疑似要素の活用（HTML削減）

以下はCSSで実現し、HTMLから削除する：

| 要素 | CSS実装 |
|------|---------|
| アンダーライン | `::after` |
| アイコン（固定） | `background-image` または `::before` |
| 装飾線 | `border` または `::before/::after` |

---

#### まとめ

- **セクション**: ページの大きな区切り（例: `chat`, `home`）
- **パーツ**: セクション名-パーツ名でフルネーム記述（例: `chat-header`, `chat-messages`）
- **内部要素**: `.__` で子要素を表現（例: `.__title`, `.__icon`）
- **Modifier**: `.__` でバリエーション・状態を表現。パーツと並列に付与（例: `__sent`, `__received`）
- **疑似要素**: 装飾的な要素はCSS `::before/::after` で実現

**CSS変数との混同回避**: `--`はCSS Custom Propertiesで使われるため、Modifierには`.__`を採用。

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

### 8. 装飾要素の検出（gap計算補正）
- [ ] リスト間に区切り線（Divider/Separator）があるか
- [ ] 要素間に矢印・アイコンがあるか
- [ ] ドット・ブレットポイント等の装飾があるか

**⚠️ 装飾要素を発見した場合の対応:**

Figmaでは装飾要素（Divider等）が独立した子要素として存在し、親の`gap`が適用される。
しかしCSSで擬似要素（`::before`/`::after`）として実装すると、擬似要素はgap計算に含まれない。

```
Figma構造:
  親要素 (gap: 12px)
  ├── Item      ← gap 12px ↓
  ├── Divider   ← gap 12px ↓  ※独立した子要素
  └── Item

実際の間隔: 12px + Divider + 12px = 24px + α
```

**擬似要素で実装する場合のgap計算式:**
```
CSSのgap値 = 元のgap × 2 + 装飾要素の高さ
擬似要素の位置 = bottom: -(元のgap + 装飾要素の高さ / 2)

例: gap=12px, Divider高さ=1px の場合
- CSSのgap: 12 × 2 + 1 = 25px
- 擬似要素: bottom: -(12 + 0.5) = -12.5px
```

**実装例:**
```scss
// ❌ 間違い: 元のgapをそのまま使用
.items {
  gap: 12px;  // Figmaのgap値
}
.item::after {
  bottom: -6px;  // 適当な位置
}

// ✅ 正解: gap計算を補正
.items {
  gap: 25px;  // 12 × 2 + 1(Divider高さ)
}
.item:not(:last-child)::after {
  content: '';
  position: absolute;
  bottom: -12.5px;  // -(12 + 0.5)
  left: 0;
  right: 0;
  height: 1px;
  background: rgb(212, 214, 221);
}
```

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

## JSON前処理スクリプト（大容量JSON対策）

### 問題
- Figma JSONは数MB〜数十MBになることがある
- AIのコンテキスト制限により、大きなJSONは全て読み込めない
- 読み込めないと値の取りこぼしが発生する

### 解決策
Pythonスクリプトで事前にJSONを軽量なMarkdownに変換する。

### スクリプトの場所
```
/Users/fukumorikei/figma-to-code/scripts/extract_figma.py
```

### 使用方法
```bash
python3 scripts/extract_figma.py {JSONファイルパス}
```

### 出力例
```
Reading: figma-assets/sample/figma-data.json
Extracting...

✅ Output: figma-assets/sample/extracted.md
   Texts: 32
   Frames: 52
   Vectors: 64

✅ No warnings
```

### 出力ファイル（extracted.md）の内容
- **Texts**: テキスト要素（fontSize, fontWeight, lineHeight, color）
- **Frames**: フレーム/コンポーネント（width, height, padding, gap, cornerRadius, backgroundColor）
- **Vectors**: アイコン（width, height, fill, stroke）

### 効果
| 項目 | Before | After |
|------|--------|-------|
| ファイルサイズ | 5.5MB | 10KB |
| 行数 | 79,689行 | 176行 |
| 削減率 | - | **99.8%** |

### 警告機能
スクリプトが値を取得できなかった場合、警告を出力する：
```
⚠️ fontSize未取得: Title (path: /Pricing/Header/Title)
```

警告が出た場合：
1. grepで該当箇所を調査
2. スクリプトを修正（パスの変更等）
3. 再実行して警告が消えることを確認

### ワークフロー統合
`auto-figma` コマンド実行時、最初にこのスクリプトが自動実行される。
生成された `extracted.md` を読み込んでCSS生成を行う。

---

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

---

## アセット参照（sections.json）

Figmaデータ取得時（`1A-fetch-figma.js`実行時）に、ダウンロードしたアセット情報が`sections.json`に自動記録される。
HTML生成時はこの情報を参照してアイコンパスを取得する。

### sections.jsonの構造

```json
{
  "sections": [{
    "name": "cart",
    "originalName": "Cart",
    "nodeId": "1:100",
    "path": "sections/cart",
    "addedAt": "2025-12-10T...",
    "assets": {
      "capture": {
        "png": "figma-capture.png",
        "webp": "figma-capture.webp"
      },
      "icons": [
        {
          "name": "Arrow",
          "file": "icons/arrow.svg",
          "nodeId": "1:200",
          "type": "VECTOR"
        },
        {
          "name": "Plus",
          "file": "icons/plus.svg",
          "nodeId": "1:201",
          "type": "VECTOR"
        }
      ]
    }
  }]
}
```

### レスポンシブ対応時の構造

```json
{
  "sections": [{
    "name": "hero",
    "devices": {
      "desktop": {
        "nodeId": "1:100",
        "dataFile": "desktop/figma-data.json",
        "captureFile": "desktop/figma-capture.png",
        "assets": {
          "capture": { "png": "figma-capture.png", "webp": "figma-capture.webp" },
          "icons": [...]
        }
      },
      "mobile": {
        "nodeId": "2:100",
        "dataFile": "mobile/figma-data.json",
        "captureFile": "mobile/figma-capture.png",
        "assets": {
          "capture": { "png": "figma-capture.png", "webp": "figma-capture.webp" },
          "icons": [...]
        }
      }
    }
  }]
}
```

### HTML生成時のアイコン参照

```html
<!-- sections.jsonのicons[].fileの値をそのまま使用 -->
<img src="icons/arrow.svg" alt="">
<img src="icons/plus.svg" alt="">
```

### ワークフロー

1. `node 1A-fetch-figma.js` 実行時にSVGが自動ダウンロードされる
2. ダウンロードされたSVGのパスが`sections.json`の`assets.icons`に記録される
3. HTML生成時、`sections.json`を参照してアイコンパスを取得
4. AIがSVGを生成する必要はない（Figmaから直接取得済み）

### 注意事項

- `sections.json`はFigma取得時に自動更新される
- 手動でSVGを追加した場合は`sections.json`に反映されない
- アイコンのファイル名はFigma上の要素名から自動生成（小文字+ハイフン区切り）
- 同名のアイコンがある場合は連番が付与される（`arrow.svg`, `arrow-1.svg`, `arrow-2.svg`）

---

## ⛔ 実装開始前の必須ゲート（CSS/HTML生成禁止条件）

> **重要**: 以下の条件を満たすまで、CSS/HTMLの生成を開始してはならない。
> このゲートを省略した場合、JSONの値を「だいたい」で丸めてしまい、設計との乖離が発生する。

### 必須完了条件

1. **PC用マッピング表の作成・出力**
   - desktop/figma-data.json の全要素を表形式で出力済み
   - サイズ・余白・色・フォントの具体的な数値を全て記載済み

2. **SP用マッピング表の作成・出力**（mobileフォルダが存在する場合）
   - mobile/figma-data.json の全要素を表形式で出力済み
   - PC版との差異を明確に記載済み

3. **要素幅の確認**（グリッドレイアウトの場合）
   - 各カラムの実際の幅（px）をJSONから取得済み
   - 全幅均等分割なのか、固定幅なのかを判断済み

### 禁止事項

- マッピング表を作成せずにCSSを書き始めること
- JSONの数値を確認せずに「だいたい○○px」と丸めること
- PC版のみ確認してSP版を後回しにすること

---

## モバイル素材がない場合のルール

### 優先順位（絶対遵守）

1. **mobile/フォルダが存在する** → **必ず** mobile/figma-data.jsonの値を使用する
2. **mobile/フォルダが存在しない** → PC版を元に推測でレスポンシブ対応を実装する

### SP素材がある場合（最優先）

mobile/フォルダが存在する場合、**必ずその値に従う**。推測で上書きしてはならない。

```scss
// ✅ 正しい例: SP素材の値をそのまま使用
@media (max-width: 767px) {
  .section-name {
    padding: 16px 20px; // mobile/figma-data.jsonの値
    gap: 12px;          // mobile/figma-data.jsonの値
  }
}
```

### SP素材がない場合（フォールバック）

mobile/フォルダが存在しない場合、PC版を元に推測でレスポンシブ対応を実装する。

```scss
// SP素材なしのため推測で実装
@media (max-width: 767px) {
  .section-name {
    padding: 0 20px;

    .__list {
      grid-template-columns: 1fr;
    }
  }
}
```

### 推測実装の基本ルール

SP素材がない場合の推測基準：
- **カラム数**: 2列以上 → 1列に変更
- **横並び**: flex-direction: row → column に変更
- **フォントサイズ**: PC版の80-90%程度に縮小（最小14px）
- **余白**: PC版の60-80%程度に縮小
- **max-width**: 100%に変更し、左右に20px程度のpadding

> **注意**: SP素材が後から追加された場合は、推測部分を素材の値で上書きすること。

### チェックリスト（全て完了するまでCSS生成禁止）

- [ ] PC用JSONを読み込み、マッピング表を出力した
- [ ] SP用JSONを読み込み、マッピング表を出力した（存在する場合）
- [ ] 全てのpadding/margin/gap/width値を数値で記載した
- [ ] マッピング表に空欄がない

---

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

---

## Gulpビルドシステム

### ディレクトリ構造（プロジェクト単位）

```
figma-to-code/
├── figma-assets/                    ← Figma素材（JSON/captures）- 参照のみ
│   └── [project-name]/
│       ├── sections.json
│       └── sections/
│           ├── hero/
│           │   ├── desktop/
│           │   │   ├── figma-data.json
│           │   │   └── figma-capture.png
│           │   └── mobile/          ← 存在する場合のみ
│           │       ├── figma-data.json
│           │       └── figma-capture.png
│           └── cart/
│               └── desktop/
│                   ├── figma-data.json
│                   └── figma-capture.png
├── src/                             ← コーディング成果物（プロジェクト単位）
│   └── [project-name]/
│       ├── index.html               ← メインHTML（Gulpで統合）
│       ├── _includes/               ← セクション（サブディレクトリ形式）
│       │   ├── hero/
│       │   │   ├── index.html       ← 本番用HTML（Gulp統合対象）
│       │   │   ├── style.scss       ← 本番用SCSS（base含む）
│       │   │   ├── preview.html     ← プレビュー用HTML（ビルド不要で即確認）
│       │   │   └── style.css        ← プレビュー用CSS（SCSSコンパイル済）
│       │   └── cart/
│       │       ├── index.html
│       │       ├── style.scss
│       │       ├── preview.html
│       │       └── style.css
│       ├── scss/                    ← Gulpビルド用（統合SCSS）
│       │   ├── style.scss           ← エントリーポイント
│       │   ├── _base.scss           ← 共通スタイル
│       │   ├── _hero.scss           ← セクション別SCSS（_includes/から同期）
│       │   └── _cart.scss
│       └── icons/                   ← SVGアイコン
│           └── arrow-right.svg
├── dist/                            ← ビルド出力（プロジェクト単位）
│   └── [project-name]/
│       ├── index.html
│       ├── css/
│       │   ├── style.css
│       │   └── style.min.css
│       └── icons/
├── package.json
└── gulpfile.js
```

### ファイルの役割（重要）

| ファイル | 役割 | 用途 |
|----------|------|------|
| `_includes/{section}/index.html` | 本番用HTML | Gulpでindex.htmlに統合 |
| `_includes/{section}/style.scss` | 本番用SCSS | base含む。preview.html用にコンパイル |
| `_includes/{section}/preview.html` | プレビュー用 | ビルド不要で即確認。開発中の視覚チェック |
| `_includes/{section}/style.css` | プレビュー用CSS | npx sassでコンパイル |
| `scss/_{section}.scss` | Gulp統合用 | style.scssからimport。base含まない |

> **注意**: `capture.png` はsrcにコピーしない。確認時は `figma-assets/` 内のキャプチャを直接参照する。

### 出力先ルール（重要）

AIがHTML/SCSSを生成する際、**プロジェクト名は `figma-assets/{project-name}/` から自動判定**する。

| 素材パス | 出力先 |
|---------|--------|
| `figma-assets/project-a/sections/cart/desktop/` | `src/project-a/_includes/cart/index.html`<br>`src/project-a/_includes/cart/style.scss`<br>`src/project-a/_includes/cart/preview.html`<br>`src/project-a/_includes/cart/style.css` |

### 新ワークフロー（セクション単位での即時確認）

```
Step 1: 素材の読み込み
  場所: figma-assets/{project}/sections/{section}/desktop/
  - figma-data.json を読み込む
  - figma-capture.png を確認する
  ↓
Step 2: マッピング表作成（CSS生成前の必須ゲート）
  - JSONの全要素を表形式で出力
  ↓
Step 3: セクションフォルダに出力
  出力先: src/{project}/_includes/{section}/
  - index.html     ← 本番用HTML
  - style.scss     ← SCSS（base含む）
  ↓
Step 4: プレビューファイル生成
  - preview.html   ← 即確認用HTML
  - style.css      ← npx sass でコンパイル
  ↓
Step 5: 即時視覚確認（Gulpビルド不要！）
  preview.html をブラウザで開き、figma-assets内のキャプチャと比較して確認
  ↓
Step 6: 修正（差異があった場合）
  style.scss を修正 → npx sass で再コンパイル → 即確認
  ↓
Step 7: 統合（全セクション完了後）
  - scss/_{section}.scss に本体部分をコピー
  - npm run build で全体統合
```

### プレビューファイルのコンパイル方法

**重要**: Claude Codeのシェルではnvmのパスが通っていないため、必ず`source ~/.nvm/nvm.sh &&`を先頭に付けること。

```bash
# セクション単位でSCSSをコンパイル
source ~/.nvm/nvm.sh && npx sass src/{project}/_includes/{section}/style.scss src/{project}/_includes/{section}/style.css

# 例
source ~/.nvm/nvm.sh && npx sass src/myproject/_includes/gravity/style.scss src/myproject/_includes/gravity/style.css
```

### セクション単体チェックの方法（新フロー）

各セクションの `_includes/{セクション名}/` ディレクトリを開き：
1. `preview.html` をブラウザで表示（ビルド不要）
2. `figma-assets/` 内のキャプチャと比較して確認
3. JSONの値とCSSが1対1で一致しているか検証
4. 差異があれば `style.scss` を修正 → `source ~/.nvm/nvm.sh && npx sass` で再コンパイル → 即確認

> **重要**: preview.html内にキャプチャ画像を埋め込まない。HTMLは本番で使う純粋なコードのみを記述する。

**メリット**:
- Gulpビルドを待たずに即座に確認できる
- 複数ターミナルで並列開発可能

### コマンド

**重要**: Claude Codeから実行する場合は`source ~/.nvm/nvm.sh &&`を先頭に付けること。

| コマンド | 用途 | 動作 |
|----------|------|------|
| `source ~/.nvm/nvm.sh && npm run dev` | 開発用 | ビルド → サーバー起動 → ファイル監視 → 自動リロード |
| `source ~/.nvm/nvm.sh && npm run build` | 本番用 | ビルドのみ（サーバー起動なし） |

### 新しいセクションの追加手順

1. **セクションディレクトリを作成**
   ```
   src/{project-name}/_includes/新セクション名/
   ```

2. **HTMLファイルを作成**
   ```
   src/{project-name}/_includes/新セクション名/index.html
   ```

3. **Sassファイルを作成**
   ```
   src/{project-name}/scss/_新セクション名.scss
   ```

4. **style.scssにインポート追加**
   ```scss
   @import '新セクション名';
   ```

5. **メインindex.htmlにインクルード追加**
   ```html
   @@include('_includes/新セクション名/index.html')
   ```

6. **必要ならアイコンを追加**
   ```
   src/{project-name}/icons/アイコン名.svg
   ```

### メリット

- **プロジェクト分離**: 複数案件が混在しない
- **CSS競合なし**: 各セクションが独立したSassファイル
- **並列作業可能**: 複数ターミナルで別セクションを同時編集可能
- **自動統合**: ビルド時に全セクションが1つのHTML/CSSに統合
- **ホットリロード**: 変更が即座にブラウザに反映

### 注意事項

- `figma-assets/` 内のファイルは参照のみ（編集しない）
- コーディング成果物は必ず `src/{project-name}/` 内に作成
- ブラウザ確認は `dist/{project-name}/index.html` で行う
- `npm install` は初回のみ必要（パッケージ追加時も実行）