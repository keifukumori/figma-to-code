# Figma to セマンティック・レスポンシブHTML/SCSS Generator

FigmaデザインからセマンティックHTML + SCSS + レスポンシブ対応のコードを自動生成するツール

## 🎯 特徴

- **レスポンシブ対応**: デスクトップ + モバイルのデザインから統合コード生成
- **セマンティックHTML**: `<main>`, `<article>`, `<section>`, `<ul><li>` 等の適切な要素
- **アクセシビリティ**: `aria-*`, `visually-hidden`, ライブリージョン対応
- **SCSS + BEM**: ネスト構造と命名規則でメンテナブルなCSS
- **一括処理**: CSV形式での複数プロジェクト処理
- **セクション別**: 独立したコンポーネント単位での実装

## 🚀 セットアップ

```bash
# 依存関係インストール
npm install

# 環境変数設定
cp .env.example .env
# .envファイル内でFIGMA_TOKENを設定
```

### .env設定例
```env
FIGMA_TOKEN=your-figma-token

# レスポンシブ対応（推奨）
FIGMA_URL_DESKTOP=https://figma.com/design/...?node-id=desktop-id
FIGMA_URL_MOBILE=https://figma.com/design/...?node-id=mobile-id

# 単一URL（旧方式）
FIGMA_URL=https://figma.com/design/...?node-id=...

OUTPUT_DIR=./output
```

## 🚀 基本的な使い方

### 準備するもの
1. **Figmaトークン** - [Figma設定](https://figma.com/settings) > Developer > Personal access tokens
2. **FigmaのURL** - コード化したいセクションのURL

### 3ステップで完了

```bash
# Step 0: トークン・URL設定
echo 'FIGMA_TOKEN=your-figma-token' > .env
echo 'FIGMA_URL=https://figma.com/design/...?node-id=...' >> .env

# Step 1: Figmaからデータを取得
node 1A-fetch-figma.js

# Step 2: AIでコード生成
claude
# → プロンプト: "output/page-name で 2-PROMPT-COMPLETE.md を実行してください"
```

**以上！** セマンティックHTML + レスポンシブSCSSが生成されます。

---

## 📋 詳細な使い方

### 方法1: 単一セクション処理

```bash
# Step 1A: Figmaデータ取得（環境変数使用）
node 1A-fetch-figma.js

# または直接URL指定
node 1A-fetch-figma.js "https://figma.com/...?node-id=..." page-name

# Step 2: セマンティックHTML/SCSS生成
claude
# → プロンプト: "output/page-name で 2-PROMPT-COMPLETE.md を実行してください"
```

### 方法2: 複数プロジェクト一括処理

**使用例**: 複数のプロジェクト（ポートフォリオ、ECサイト等）のデスクトップ・モバイル版を一度に処理

#### Step 1B-1: urls.csvファイルを手動作成

テキストエディタで `urls.csv` を作成し、以下の形式でURLを記載：

```csv
page_name,desktop_url,mobile_url
portfolio,https://figma.com/design/ABC...?node-id=2444-156,https://figma.com/design/ABC...?node-id=2444-157
ecommerce,https://figma.com/design/ABC...?node-id=2444-158,https://figma.com/design/ABC...?node-id=2444-159
```

**ポイント**:
- `page_name`: 出力ディレクトリ名（英数字推奨）
- `desktop_url`: PC版Figmaの該当セクションURL
- `mobile_url`: SP版Figmaの該当セクションURL
- 同一Figmaファイル内の異なるnode-idを指定

#### Step 1B-2: 一括データ取得

```bash
node 1B-fetch-figma-batch.js urls.csv
```

**処理内容**:
- 各プロジェクトのデスクトップ・モバイル版を順次取得
- API制限対策で自動的に待機時間を設定
- `output/portfolio/`, `output/ecommerce/` 等のディレクトリを生成

#### Step 2: 各プロジェクトでコード生成

```bash
claude
# → プロンプト例: "output/portfolio で 2-PROMPT-COMPLETE.md を実行してください"
# → プロンプト例: "output/ecommerce で 2-PROMPT-COMPLETE.md を実行してください"
```

## 📁 出力構造

```
output/
└── [page-name]/
    ├── sections.json              # セクション管理ファイル
    └── sections/
        ├── _variables.scss        # 共通変数
        ├── _mixins.scss          # 共通mixin
        ├── debug/
        │   └── section.css       # デバッグ用CSS（自動生成）
        └── [section-name]/
            ├── index.html        # セマンティックHTML
            ├── section.scss      # SCSSマスター（BEM構造）
            ├── desktop/
            │   ├── figma-data.json
            │   └── figma-capture.png
            └── mobile/
                ├── figma-data.json
                └── figma-capture.png
```

## 🛠️ 生成されるコード例

### HTML (セマンティック)
```html
<main class="chat">
  <header class="chat__header">
    <h1 class="visually-hidden">チャットアプリ</h1>
  </header>

  <section class="chat__messages" role="log" aria-live="polite">
    <ul class="chat__message-list">
      <li>
        <article class="chat__message">
          <!-- メッセージ内容 -->
        </article>
      </li>
    </ul>
  </section>

  <form class="chat__form">
    <!-- フォーム要素 -->
  </form>
</main>
```

### SCSS (BEM + レスポンシブ)
```scss
@import '../variables';
@import '../mixins';

.chat {
  // Desktop Base Styles（実測値）
  max-width: 1200px; /* ⚠️ 推測値: 要調整 */

  &__messages {
    height: 400px; /* 実測値: desktop/figma-data.jsonより */

    @include mobile {
      height: 300px; /* 実測値: mobile/figma-data.jsonより */
    }
  }
}
```

## ⚠️ API制限について

Figma API（無料版）には厳しい制限があります：
- 1日数回程度のアクセス制限
- 429エラー時は翌日まで待機が必要
- 詳細は `DEVELOPMENT-NOTES.md` を参照

## 📚 ドキュメント

- `2-PROMPT-COMPLETE.md`: AI用プロンプト（現行推奨版）
- `DEVELOPMENT-NOTES.md`: 開発経緯と技術的判断
- `BOTSU-*`: 古いバージョン（使用禁止）

## 🔧 トラブルシューティング

### API制限エラー（429）
```
⚠️ API制限に達しました (429)
   待機時間: 60秒
   時刻: 14:30:25
   ヒント: 無料プランの場合、1日の制限に達している可能性があります
```
→ 翌日まで待機するか、有料プランへのアップグレードを検討

### CSV形式エラー
```csv
page_name,desktop_url,mobile_url
portfolio,https://figma.com/design/...desktop-node,https://figma.com/design/...mobile-node
ecommerce,https://figma.com/design/...desktop-node,https://figma.com/design/...mobile-node
```

## 📅 バージョン履歴

- **v3.0**: セマンティックHTML + アクセシビリティ + SCSS対応
- **v2.0**: レスポンシブ対応（デスクトップファースト）
- **v1.0**: 基本的なHTML/CSS生成