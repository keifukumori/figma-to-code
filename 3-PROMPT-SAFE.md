# Figma to セマンティック・レスポンシブHTML/CSS 生成プロンプト（安全版）

## 使い方
ページディレクトリ内でClaude Codeを起動し、以下のプロンプトを実行。
**元のfigma-data.jsonを優先的に使用し、100%の忠実度を保証します。**

---

## プロンプト（そのままコピー）

```
このディレクトリのfigma-data.json（またはfigma-data-simplified.json）とfigma-capture.pngから
**セマンティック・アクセシブル・レスポンシブ対応**のHTML/CSSファイルセットを生成してください。

## 実行ステップ

### 1. データ選択
優先順位：
1. **figma-data.json**（元データ）を優先使用 ← 推奨
2. figma-data-simplified.json（既に存在する場合のみ）

※ 元データが大きすぎる場合のみ、手動で簡略化を検討

### 2. HTML/CSS生成
Figmaデータから以下を生成：
- `index.html` - セマンティックHTML（BEM命名規則）
- `[セクション名].css` - ピクセル完璧なCSS

### 3. 設計忠実度検証（必須）

> **注意**: 外部ツール不要。AI自身が検証を実行します（環境非依存）。

生成後、AI自身が以下の検証を実行：
1. JSONから期待される色・フォント・サイズを抽出
2. CSSから実装済みの値を抽出
3. 差分を検出し忠実度スコアを計算
4. 95%未満の場合は自動修正サイクルを実行

詳細は「品質保証（必須）」セクションを参照。

## ルール

### 最優先事項
- **元のfigma-data.jsonを可能な限り使用**
- **色・フォントサイズ・文字属性はFigmaデータを100%忠実に再現**
- **レイアウト構造はキャプチャ画像との整合性を優先**
- **設計忠実度95%以上を目標に自動修正**
- **JSON未記載の実装は必ずコメントで理由明記**

### データ処理の注意点

#### 大容量データの扱い
- 1MB以下：そのまま処理 ✅
- 1-2MB：処理を試みる（多くの場合可能）
- 2MB以上：エラーが出た場合のみ簡略化を検討

#### 簡略化が必要な場合（最終手段）
```bash
# 手動で実行（プロンプト外）
node ../../simplify-figma-json.js figma-data.json

# ⚠️ 警告：レイアウト情報が失われる可能性
# 検証で忠実度が低い場合は元データに戻す
```

### HTML構造（必須要素）

#### 完全なHTMLファイル（必須）
**ブラウザで直接開ける完全なHTMLファイルとして作成**
- `<!DOCTYPE html>`、`<html>`、`<head>`、`<meta>`、`<body>`を含む
- `<link rel="stylesheet" href="[セクション名].css">`でCSSを読み込み
- メインコンテンツは`<section class="セクション名">`で構成

#### セマンティック要素の優先順位
1. `<section>` - メインコンテンツの区分
2. `<article>` - 独立したコンテンツ
3. `<header>` / `<footer>` - ヘッダー/フッター
4. `<nav>` - ナビゲーション
5. `<figure>` / `<figcaption>` - 画像とキャプション
6. `<h1>` ~ `<h6>` - 見出し階層（適切なレベルで使用）

#### シンプル命名規則（必須）
```html
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Section Title</title>
    <link rel="stylesheet" href="section-name.css">
</head>
<body>
    <section class="pricing">
      <div class="pricing_header">
        <h1 class="pricing_title">タイトル</h1>
        <p class="pricing_subtitle">説明文</p>
      </div>
      <div class="pricing_plans">
        <div class="pricing-plan">
          <div class="__header">
            <h2 class="__name">プラン名</h2>
            <span class="__price">値段</span>
          </div>
          <ul class="__features">
            <li class="__feature">機能</li>
          </ul>
          <button class="__button">ボタン</button>
        </div>
      </div>
    </section>
</body>
</html>
```

**命名ルール:**
- **親要素**: ブロック名のみ（例：`pricing`, `hero`, `footer`）
- **直接の子要素**: `親_要素名`（例：`pricing_title`, `pricing_subtitle`）アンダースコア1つ
- **論理グループ**: `親-グループ名`（例：`pricing-plan`, `pricing-feature`）ハイフン
- **グループ内要素**: `__要素名`のみ（例：`__header`, `__name`, `__price`）アンダースコア2つ、プレフィックスなし
- **状態・種類**: 通常のクラス名（例：`highlight`, `active`, `disabled`）
- **モディファイア**: `--`は使わず、分かりやすいクラス名を併用

**利点:**
- HTMLが格段に読みやすい
- 冗長な繰り返しを排除
- SCSSのネストと相性が良い

### CSS実装（必須）

#### 3. JSONの全プロパティを網羅的に適用
```css
/* ❌ 悪い例：部分的なJSON参照 */
.element {
  font-size: 16px; /* JSONから */
  width: 300px;    /* 推測値 */
}

/* ✅ 良い例：JSONの全プロパティを適用 */
.element {
  /* JSON absoluteBoundingBox */
  width: 620px;
  height: 413.3332214355469px;

  /* JSON padding */
  padding: 96px 64px;

  /* JSON itemSpacing */
  gap: 40px;

  /* JSON cornerRadius */
  border-radius: 6px;

  /* JSON style */
  font-size: 18px;
  font-weight: 700;
  letter-spacing: -0.18px;

  /* JSON fills[0].color を RGB変換 */
  /* r:0.8235 g:0 b:0.0157 → rgb(210, 0, 4) */
  color: rgb(210, 0, 4);
}
```

#### Figmaデータからの正確な抽出
```css
:root {
  /* Figmaから抽出した正確な色 */
  --color-text: rgba(r*255, g*255, b*255, a);

  /* Figmaから抽出した正確なサイズ */
  --font-size: [fontSize]px;
  --line-height: [lineHeight.value]px;

  /* Figmaから抽出した正確なレイアウト */
  --width: [width]px;
  --height: [height]px;
}
```

#### ⚠️ 推測による実装の禁止（重要追加）

**絶対禁止事項（色・サイズ・文字属性）:**
- 「このボタンは青色だろう」という色の憶測
- 「フォントサイズは24pxぐらい」という目測
- 「フォントはBoldだろう」という推測

**必須確認項目（JSON必須）:**
1. **色** - 必ず`fills`または親要素の`fills`を確認
   ```json
   "fills": [{"color": {"r": 0.xxx, "g": 0.xxx, "b": 0.xxx, "a": 1}}]
   ```
2. **フォントサイズ** - 必ず`fontSize`を確認
   ```json
   "fontSize": 24
   ```
3. **文字配置** - 必ず`textAlignHorizontal`を確認
   ```json
   "textAlignHorizontal": "LEFT" | "CENTER" | "RIGHT"
   ```
4. **フォント太さ** - 必ず`fontWeight`を確認
   ```json
   "fontWeight": 700
   ```

#### ✅ レイアウト構造の例外規定（キャプチャ参考許可）

**キャプチャ画像を参考にして良い項目:**
- 全体的なページ構造・配置
- 要素間のマージン・パディング
- モバイル/デスクトップでのレイアウト判断
- ナビゲーション構造
- グリッドシステムの配置

**理由:** FigmaのJSONには個々の要素情報はあるが、全体的なUI構造やページレイアウトは含まれないため

**実装例:**
```css
/* ✅ 正解：キャプチャ参考によるレイアウト */
.cart__header {
  display: flex; /* キャプチャで横並び確認 */
  justify-content: space-between; /* キャプチャで配置確認 */
  padding: 20px; /* キャプチャで余白確認 */
}

/* ❌ 間違い：色の推測 */
.cart__title {
  color: #333; /* 推測 - JSONで確認必要 */
}

/* ✅ 正解：JSONから正確な色 */
.cart__title {
  color: rgba(31, 32, 36, 1); /* r: 0.12, g: 0.125, b: 0.14 from JSON */
}
```

**確認手順:**
1. **キャプチャ詳細分析**（最優先・最初に実行）
2. **色・サイズ・文字属性**: JSONで要素名検索
3. **実装**: キャプチャ構造 + JSON値で作成
4. **段階的キャプチャ再確認**: 実装中に構造一致確認
5. **推測値は一切使用しない（色・サイズ・文字のみ）**
6. **JSONに記載がない場合のみコメントで理由明記**

#### 🔍 キャプチャ詳細分析手順（必須）

**Read toolでキャプチャ確認時に必ず実行:**

1. **全体構造の把握**
   ```markdown
   ## 構造分析
   - ヘッダー部分: どこに何があるか（ボタン位置・テキスト配置）
   - メインエリア: コンテンツの配置・順序
   - フッター部分: 要素の配置・ボタンサイズ
   ```

2. **個別パーツの詳細分析**
   ```markdown
   ## パーツ詳細
   - 各要素の独立性: 結合しているか・分離しているか
   - 背景色の適用範囲: 個別要素か・グループ全体か
   - ボタン形状: 角丸・円形・四角
   - 視覚的グループ化: どこまでが1つのまとまりか
   ```

3. **配置関係の正確な把握**
   ```markdown
   ## 配置詳細
   - 要素間の間隔: 密着・狭い・広い
   - 整列方法: 左寄せ・中央・右寄せ・均等配置
   - アイテム境界: セパレーター・余白・線
   ```

**例：数量選択ボタンの正しい分析**
```markdown
❌ 間違った分析:「数量選択エリアがある」
✅ 正しい分析:「−（独立丸ボタン・薄い背景）1（数字のみ・背景なし）+（独立丸ボタン・薄い背景）が横に配置」
```

**段階的確認ポイント:**
- HTML構造作成後 → キャプチャで配置確認
- 基本CSS作成後 → キャプチャで見た目確認
- 詳細調整後 → キャプチャで最終確認

**例：正しい実装（新しい命名規則）**
```css
/* ❌ 間違い：推測による実装 */
.pricing-plan__header {
  text-align: center; /* 推測 */
}

/* ✅ 正解：Figmaデータに基づく実装 */
.pricing-plan__header {
  text-align: left; /* textAlignHorizontal: "LEFT" from Figma */
}
```

**実装例（完全なHTMLファイル）:**
```html
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Choose Your Plan</title>
    <link rel="stylesheet" href="pricing.css">
</head>
<body>
    <section class="pricing">
      <div class="pricing_header">
        <h1 class="pricing_title">Choose Your Plan</h1>
        <p class="pricing_subtitle">説明文</p>
      </div>
      <div class="pricing_plans">
        <div class="pricing-plan highlight">
          <div class="__header">
            <h2 class="__name">Personal</h2>
            <span class="__price">$11.99</span>
          </div>
          <button class="__button">Get Started</button>
        </div>
      </div>
    </section>
</body>
</html>
```

**CSSの実装例:**
```css
body {
  margin: 0;
  padding: 0;
  font-family: system-ui, sans-serif;
}

.pricing {
  padding: 80px 40px;
}

.pricing_title {
  font-size: 72px; /* JSON値 */
  color: rgba(33, 38, 41, 1); /* JSON値 */
}

.pricing-plan {
  background: white;
  border-radius: 12px;

  .__name {
    font-size: 24px; /* JSON値 */
    color: rgba(33, 38, 41, 1); /* JSON値 */
  }

  &.highlight {
    background: rgba(5, 56, 115, 1); /* JSON値 */
  }
}
```

#### レスポンシブ対応（SCSSネスト推奨）
```scss
// SCSS変数でブレイクポイントを定義
$sp: 768px;

// ミックスインでメディアクエリを管理
@mixin media-sp {
  @media (max-width: $sp) {
    @content;
  }
}

// 使用例（シンプル命名規則）
.gravity-team {
  .__stats-grid {
    grid-template-columns: repeat(4, 1fr); /* デスクトップ：4列 */

    @include media-sp {
      grid-template-columns: 1fr; /* スマートフォン対応：1列スタック */
    }
  }

  .__title {
    font-size: 24px;

    @include media-sp {
      font-size: 18px;
    }
  }
}
```

**通常のCSSの場合:**
```css
:root {
  --breakpoint-sp: 768px;
}

.gravity-team {
  /* 親要素のスタイル */
}

.gravity-team .__stats-grid {
  grid-template-columns: repeat(4, 1fr);
}

.gravity-team .__title {
  font-size: 24px;
}

@media (max-width: 768px) {
  .gravity-team .__stats-grid {
    grid-template-columns: 1fr; /* スマートフォン対応：1列スタック */
  }

  .gravity-team .__title {
    font-size: 18px;
  }
}
```

#### グラデーション処理
```css
/* gradientStops配列から正確に変換 */
/* r, g, b は 0-1 の値なので 255 を掛ける */
--gradient: linear-gradient(
  [angle]deg,
  rgba([r*255], [g*255], [b*255], [a]) [position*100]%,
  ...
);
```

#### 4. 実装後のキャプチャー照合
```bash
# 実装したHTMLを開く（ブラウザで確認）
open sections/セクション名/index.html

# 元のFigmaキャプチャーと比較（AIが視覚的に認識可能）
# AIが元の画像ファイルを読み込んで、実装結果と視覚的に照合

# チェックリスト（AIが視覚的に確認）：
# □ 色がキャプチャーと一致しているか
# □ 要素の大きさが正確か
# □ 余白・間隔が適切か
# □ テキスト内容が正しいか
# □ フォントサイズ・太さが一致しているか
```

#### 5. 自律的な修正サイクル
```
キャプチャーと差異がある場合：
1. JSONを再確認 → 見落としたプロパティがないか
2. 単位の変換を確認 → RGB値の計算、px値の精度
3. レイアウトモードを確認 → layoutMode, itemSpacing, alignItems
4. 修正を適用 → 再度キャプチャーと照合
5. 完全一致するまで1-4を繰り返す
```

### 🎯 視覚的一致度100%達成プロセス

#### 自動品質保証フロー
```bash
# 1. 実装完了後、元キャプチャーと視覚的に比較
AIが元のfigma-capture.pngを読み込み、実装結果と照合

# 2. 一致度レポートを作成
視覚的一致度チェック:
├── レイアウト: XX%
├── 色: XX%
├── テキスト: XX%
├── フォント: XX%
└── 画像: プレースホルダー使用中か確認

# 3. 画像以外を100%まで自動修正
- 差異を検出 → JSONから正確な値を取得 → 自動修正を適用

# 4. ユーザーへの確認（画像部分のみ）
```

#### 視覚的一致度レポート（例）
```markdown
🎨 視覚的一致度レポート
━━━━━━━━━━━━━━━━━━
✅ 完全一致（100%）:
- テキスト内容
- セクション構造
- 背景色とグラデーション

🔧 自動修正済み:
- 余白: padding 60px → 96px（JSON準拠）
- 間隔: gap 30px → 40px（JSON準拠）
- フォント: weight 500 → 700（JSON準拠）

⚠️ ユーザー確認が必要:
【例】画像ファイル:
- hero-image.jpg
- team-photo.png
- product-1.jpg
→ プレースホルダーのままでよろしいですか？
→ 実際の画像パスを指定しますか？
```

#### 修正の実例
```css
/* 例：自動修正前（85%一致） */
.section {
    padding: 60px 40px;  /* 推測値 */
    gap: 30px;          /* 推測値 */
}

/* 例：自動修正後（100%一致） */
.section {
    padding: 96px 64px;  /* JSON padding値を正確に適用 */
    gap: 40px;          /* JSON itemSpacing値を正確に適用 */
}
```

### ⚠️ よくある失敗パターンと対策

| 失敗パターン | 原因 | 対策 |
|------------|------|------|
| セクション内容が全く違う | 間違ったJSONを参照 | Y座標とテキスト内容で正しいJSONを特定 |
| 色が微妙に違う | RGB値の変換ミス | r,g,b値を0-255に正確に変換（r * 255） |
| レイアウトがずれる | itemSpacingの見落とし | JSONのlayoutMode, itemSpacing, paddingを全て確認 |
| サイズが合わない | 推測値を使用 | absoluteBoundingBoxの値を小数点まで正確に使用 |
| フォントが違う | fontWeightの見落とし | JSON内の"fontWeight": 700等を確実に反映 |
| 配置がずれる | textAlignの見落とし | "textAlignHorizontal": "LEFT"等を確実に反映 |
| 角丸が違う | cornerRadiusの見落とし | border-radiusにcornerRadius値を正確に適用 |
| 間隔が不自然 | itemSpacingの未適用 | gap: [itemSpacing]pxを適用 |

### 品質保証（必須）

> **注意**: 外部ツール（Node.js等）に依存せず、AI自身が品質検証を行います。
> Claude、ChatGPT、Gemini等どのAIでも実行可能です。

#### 検証の目的
**JSONの全要素がCSSに漏れなく反映されていることを1対1で確認する。**

#### 検証手順（AI自己検証）

**Step 1: JSON要素の全数カウント**
```
対象（visible: trueのみ）:
- テキスト要素（type: "TEXT"）
- 色指定（fills[].color）
- フォント設定（style.fontSize）
- 余白設定（padding*, itemSpacing）
- 角丸設定（cornerRadius）
- グラデーション（type: "GRADIENT_*"）
```

**Step 2: 要素ごとの1対1マッピング表（必須・省略禁止）**
```markdown
### テキスト要素マッピング
| # | JSON要素名 | characters | fontSize | color | → CSSセレクタ | 実装 |
|---|-----------|------------|----------|-------|---------------|------|
| 1 | タイトル | "..." | 16 | rgb(...) | .class | ✅/❌ |

### 色マッピング
| # | JSON要素名 | 種別 | JSON値 | → RGB | CSSセレクタ | 実装 |
|---|-----------|------|--------|-------|-------------|------|
| 1 | arrow | fills | r,g,b | rgb(...) | .class | ✅/❌ |

### サイズ・余白マッピング
| # | JSON要素名 | 属性 | JSON値 | CSSプロパティ | CSSセレクタ | 実装 |
|---|-----------|------|--------|---------------|-------------|------|
| 1 | button | padding | 24 | padding | .class | ✅/❌ |
```

**空欄 = 実装漏れ** と判断する。

**Step 3: 忠実度スコア計算**
```
スコア = (マッピング表の✅数 / 総行数) × 100
```

**Step 4: 検証レポート出力**
```markdown
## 🎨 設計忠実度レポート

### マッピング検証結果
| 種別 | JSON要素数 | CSS実装数 | 実装率 |
|------|-----------|-----------|--------|
| テキスト | X | X | 100% |
| 色 | X | X | 100% |
| サイズ | X | X | 100% |

### 忠実度スコア: XX%

### 未実装項目
（なければ「なし ✅」）

### 詳細マッピング表
（Step 2の全テーブル）
```

#### 成功基準
- 忠実度スコア: **95%以上**
- 全マッピング表に空欄がない
- 色の実装率: 100%
- **視覚的一致度: 100%**

#### 失敗時の対処（自動修正サイクル）
1. マッピング表の❌/空欄を特定
2. JSONから正確な値を再取得
3. CSSに追加
4. Step 1-4を再実行
5. 100%になるまで繰り返し（最大3回）

### トラブルシューティング

#### データが大きすぎる場合
```
エラー: "Content too large"
対処法:
1. 部分的に処理（上半分と下半分を分けて）
2. 最終手段として簡略化を検討
3. ただし忠実度低下のリスクを理解
```

#### 忠実度が低い場合
```
スコア < 95%
対処法:
1. 元データ（figma-data.json）を使用
2. 色の抽出が正確か確認（r,g,b * 255）
3. レイアウト情報が保持されているか確認
```

### 要素別JSON確認の必須手順（省略禁止）

#### ❌ 禁止: 一括検索のみで色を決定
```bash
# これだけで済ませてはいけない
grep -E '"color"' figma-data.json | head -50
```

一括検索で「この色が多いから他も同じだろう」と推測することは**絶対禁止**。

#### ✅ 必須: 要素IDごとの個別確認

**Step 1: CSSで使う全要素のIDをリストアップ**
```bash
# ボタン要素のID一覧
grep -B5 '"name": "Btn' figma-data.json | grep '"id"'

# カード要素のID一覧
grep -B5 '"name": "Card\|Price-board' figma-data.json | grep '"id"'
```

**Step 2: 各IDのfillsを個別に確認（省略禁止）**
```bash
# 全ボタンを1つずつ確認 - 省略してはいけない
grep -A50 '"id": "9:2219"' figma-data.json | grep -A12 '"fills"'
grep -A50 '"id": "9:2257"' figma-data.json | grep -A12 '"fills"'
grep -A50 '"id": "9:2295"' figma-data.json | grep -A12 '"fills"'
```

**Step 3: JSON→CSS対応マッピング表を作成（CSS出力先必須）**

CSS生成前に必ず「要素ごと」のマッピング表を作成。**CSS出力先が空欄 = 反映漏れ**と判断する。

```markdown
### 要素: Minus Button (親フレーム)
ID: I240:6225;234:4075;234:3815

| JSON属性 | JSON値 | → CSSプロパティ | CSSセレクタ |
|----------|--------|-----------------|-------------|
| fills | r:0.918,g:0.949,b:1 | background: rgb(234,242,255) | .quantity-control .__btn |
| strokes | [] | border: none | .quantity-control .__btn |
| cornerRadius | 26 | border-radius: 50% | .quantity-control .__btn |

### 要素: Minus Icon (子要素)
ID: I240:6225;234:4075;234:3816;164:1456

| JSON属性 | JSON値 | → CSSプロパティ | CSSセレクタ |
|----------|--------|-----------------|-------------|
| fills | r:0,g:0.435,b:0.992 | color: rgb(0,111,253) | .quantity-control .__btn |
```

#### マッピング表の必須ルール
1. **1要素1テーブル**: 親要素と子要素は別テーブル
2. **全属性を列挙**: fills, strokes, cornerRadius, fontSize, fontWeight等
3. **CSS出力先必須**: 「→ CSSプロパティ」列が空 = 反映漏れ
4. **セレクタ必須**: どのCSSセレクタに書くか明記

#### 要素別確認チェックリスト（CSS生成前に必須）
- [ ] 全ボタン要素の**親フレーム**のfills/strokesを確認した
- [ ] 全ボタン要素の**子要素（アイコン）**のfillsを確認した
- [ ] 全カード要素のfillsを個別にgrepで確認した
- [ ] 全テキスト要素のrangeFillsを個別にgrepで確認した
- [ ] **要素ごとのマッピング表を作成した（CSS出力先必須）**
- [ ] マッピング表の「→ CSSプロパティ」列に空欄がない
- [ ] 「似た要素だから同じ色だろう」という推測を一切していない

---

## 必須チェックリスト

- [ ] 元のfigma-data.jsonを優先的に使用
- [ ] Figmaデータから色を正確に抽出（rgba値、0-1を255に変換）
- [ ] Figmaデータからサイズを正確に抽出（px値）
- [ ] **文字配置をtextAlignHorizontalから正確に抽出**
- [ ] **ボタン背景色を親要素のfillsから正確に抽出**
- [ ] **推測による実装を一切行わない**
- [ ] **JSONの全プロパティを網羅的に適用**（absoluteBoundingBox, padding, itemSpacing, cornerRadius等）
- [ ] **実装後のキャプチャー照合を実行**（ブラウザ表示とfigma-capture.png比較）
- [ ] **自律的な修正サイクルを適用**（差異検出→JSON再確認→修正→再照合）
- [ ] **視覚的一致度100%達成まで修正を継続**
- [ ] グラデーションはgradientStopsから正確に変換
- [ ] **シンプル命名規則を適用**（親要素ブロック名＋子要素__要素名）
- [ ] セマンティックHTMLタグを使用
- [ ] AI自己検証で忠実度レポートを出力
- [ ] 95%以上のスコア達成確認
- [ ] **失敗パターンと対策表を参考に問題解決**

### シンプル命名規則の実装手順

1. **HTML構造設計**: 親要素に意味のあるブロック名を付与
   ```html
   <div class="message-group sent">
     <span class="__sender">Lucas</span>
     <p class="__text">Hi Brooke!</p>
   </div>
   ```

2. **子要素命名**: `__`で始まる要素名で親子関係を明示
3. **状態管理**: 通常のクラス名で状態を表現（`sent`, `received`, `active`等）
4. **CSS実装**: SCSSライクなネスト構造で整理
   ```css
   .message-group {
     margin-bottom: 16px;

     .__sender { font-size: 12px; }
     .__text { padding: 10px 16px; }

     &.sent { text-align: right; }
     &.received { text-align: left; }
   }
   ```

5. **検証**: HTMLの可読性とCSS保守性を確認

⚠️ **重要**: 簡略化は最終手段。可能な限り元データで100%の忠実度を目指してください。
```