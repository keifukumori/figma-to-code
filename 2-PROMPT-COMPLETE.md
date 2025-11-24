# Figma to セマンティック・レスポンシブHTML/CSS 生成プロンプト（完全版）

## 使い方
ページディレクトリ内でClaude Codeを起動し、以下のプロンプトを実行。
デスクトップとモバイル両方のデザインデータから、セマンティック・アクセシブル・レスポンシブ対応のHTML/SCSS/CSSを生成します。

---

## プロンプト（そのままコピー）

```
sections.json を読み込み、各セクションのdesktop/とmobile/データから
**セマンティック・アクセシブル・レスポンシブ対応**のファイルセットを生成してください。

## ルール

### 最優先事項
- **Figmaデザインデータを忠実に再現することが絶対の使命**
- **セマンティックHTMLでアクセシビリティを最大化**
- **desktop版をベース、mobile版との差分でレスポンシブ対応**
- **推測値は必ずコメントで明記し、手動修正を容易にする**

### ファイル構成・命名規則
生成するファイル：
```
sections/セクション名/
├── index.html                    # セマンティックHTML
├── セクション名.scss              # SCSSマスター（BEMネスト構造）
├── desktop/
│   ├── figma-data.json          # PC版デザインデータ（既存）
│   └── figma-capture.png        # PC版キャプチャ（既存）
└── mobile/
    ├── figma-data.json          # SP版デザインデータ（既存）
    └── figma-capture.png        # SP版キャプチャ（既存）

sections/
├── debug/
│   └── セクション名.css           # デバッグ用CSS（SCSSコンパイル結果）
├── _variables.scss              # 共通変数
└── _mixins.scss                 # 共通mixin
```

HTMLの読み込みパス：
```html
<link rel="stylesheet" href="../debug/セクション名.css">
```

### セマンティックHTML（必須要素）

#### 構造要素の使い分け
```html
<!-- コンテンツ構造 -->
<main>           <!-- メインコンテンツ（1ページ1つ） -->
<header>         <!-- ヘッダー -->
<footer>         <!-- フッター -->
<section>        <!-- 機能別セクション（見出し必須） -->
<article>        <!-- 独立コンテンツ（商品カード、投稿等） -->
<aside>          <!-- 補足情報 -->
<nav>            <!-- ナビゲーション -->

<!-- 決してdivで代替しない -->
```

#### リスト要素（超重要）
```html
<!-- 商品リスト、カートアイテム、メニュー等は必ずリスト化 -->
<ul class="cart-items">
  <li>
    <article class="cart-item">
      <!-- 各アイテムはarticleで独立性を表現 -->
    </article>
  </li>
</ul>

<!-- 順序のあるリスト -->
<ol class="checkout-steps">
  <li>配送先入力</li>
  <li>支払い方法</li>
</ol>

<!-- 定義リスト -->
<dl class="product-specs">
  <dt>サイズ</dt>
  <dd>M</dd>
</dl>
```

#### 見出し階層（必須）
```html
<!-- 正しい階層順序を必ず守る -->
<h1>ページタイトル</h1>
  <h2>セクションタイトル</h2>
    <h3>アイテムタイトル</h3>
      <h4>詳細項目</h4>

<!-- 視覚的に不要な見出しは非表示化 -->
<h2 class="visually-hidden">商品一覧</h2>
```

#### メディア要素
```html
<!-- 商品画像、説明図等 -->
<figure class="product-image">
  <img src="..." alt="具体的な説明">
  <figcaption class="visually-hidden">商品メイン画像</figcaption>
</figure>

<!-- アイコン・装飾画像 -->
<img src="..." alt="" aria-hidden="true" role="presentation">
<!-- または -->
<span class="icon" aria-hidden="true">SVG</span>
```

#### フォーム要素
```html
<form class="message-form">
  <fieldset class="form-group">
    <legend class="visually-hidden">メッセージ送信</legend>

    <label for="message-input" class="visually-hidden">メッセージを入力</label>
    <input type="text"
           id="message-input"
           name="message"
           aria-describedby="message-help"
           autocomplete="off">

    <span id="message-help" class="visually-hidden">
      メッセージを入力してEnterキーで送信
    </span>

    <button type="submit" aria-label="メッセージを送信">送信</button>
  </fieldset>
</form>
```

### アクセシビリティ（必須対応）

#### ARIA属性
```html
<!-- ライブリージョン -->
<ul role="log" aria-live="polite" aria-label="チャットメッセージ">

<!-- ボタンラベル -->
<button aria-label="数量を増やす">+</button>
<button aria-label="カートに追加" aria-describedby="price-info">

<!-- 非表示コンテンツ -->
<span aria-hidden="true">🛒</span>
<img src="..." alt="" role="presentation">

<!-- 状態表示 -->
<button aria-expanded="false" aria-controls="menu">メニュー</button>
```

#### スクリーンリーダー対応
```html
<span class="visually-hidden">スクリーンリーダー専用テキスト</span>
```

```css
.visually-hidden {
  position: absolute !important;
  width: 1px !important;
  height: 1px !important;
  padding: 0 !important;
  margin: -1px !important;
  overflow: hidden !important;
  clip: rect(0, 0, 0, 0) !important;
  white-space: nowrap !important;
  border: 0 !important;
}
```

### SCSS設計（デスクトップファースト）

#### ファイル構造
```scss
// セクション名.scss（例：chat.scss）
@import '../variables';
@import '../mixins';

.セクション名 {
  // Desktop Base Styles（実測値）

  &__要素名 {
    // BEMネスト構造

    &--modifier {
      // モディファイア
    }
  }

  // Mobile Adjustments（実測差分のみ）
  @include mobile {
    // mobile/figma-data.jsonからの実測差分
  }
}
```

#### 推測値の明記方法
```scss
// =========================
// 推測値 - 手動修正が必要
// =========================

$container-max-width: 1200px !default; /* ⚠️ 推測値: コンポーネント幅375pxから逆算 TODO: 実際のデザイン幅に調整 */
$breakpoint-mobile: 768px !default;   /* ⚠️ 推測値: 一般的なブレークポイント TODO: デザインに合わせて調整 */

.section {
  max-width: $container-max-width; /* ⚠️ 推測値 */
  padding: 24px; /* 実測値: desktop/figma-data.jsonより */

  @include mobile {
    padding: 16px; /* 実測値: mobile/figma-data.jsonより */
  }
}
```

### データ取得・分析手順
1. **desktop/figma-data.jsonを読み込み** → ベーススタイル生成
2. **mobile/figma-data.jsonを読み込み** → 差分抽出
3. **レイアウト差分を実測比較**
   - 要素配置（横並び→縦並び等）
   - フォントサイズ変化
   - 余白・間隔の変化
   - 要素サイズの変化
4. **コンテナ幅・ブレークポイントを推測**（根拠をコメント記載）

### レスポンシブ対応（実測ベース）
```scss
// Desktop（実測値）
.product-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr); /* 実測: 3列レイアウト */
  gap: 24px; /* 実測値 */
}

// Mobile（実測差分）
@include mobile {
  .product-grid {
    grid-template-columns: repeat(2, 1fr); /* 実測: 2列に変更 */
    gap: 16px; /* 実測: 間隔縮小 */
  }
}
```

### 出力後の報告
```
## 生成完了

### ✅ セクション: セクション名
- **HTML**: セマンティック要素（main, article×N, ul>li×N, figure×N等）
- **SCSS**: BEMネスト構造、実測ベース
- **CSS**: debug/セクション名.css（デバッグ用）

### ⚠️ 推測で設定した値（要手動調整）
1. **コンテナ最大幅**: 1200px
   - 根拠: モバイル幅375pxからの一般的な比率
   - 調整箇所: $container-max-width

2. **ブレークポイント**: 768px
   - 根拠: 一般的なタブレット境界値
   - 調整箇所: $breakpoint-mobile

3. **グリッド変更**: 3列→2列
   - 根拠: desktop/mobile JSON比較による実測
   - 調整箇所: .product-grid メディアクエリ

### 🔧 手動修正推奨箇所
- [ ] _variables.scssのコンテナ幅調整
- [ ] ブレークポイントの微調整
- [ ] レスポンシブ時の余白調整
```

```

---

## Before / After

### Before（従来）
```
sections/cart/
├── index.html          # div多用、非セマンティック
└── style.css           # SP固定、レスポンシブなし
```

### After（完全版）
```
sections/cart/
├── index.html          # セマンティック・アクセシブル
├── cart.scss           # BEM、デスクトップファースト
├── desktop/figma-data.json
├── mobile/figma-data.json
└── （debug/cart.css）    # 自動生成
```