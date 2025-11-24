# Figma to Code - 開発経緯と今後の実装方針

## 📋 概要

このドキュメントは、Figmaデザインから自動的にHTML/CSSを生成するツールの開発過程で直面した課題と、その解決策についてまとめたものです。特に、レスポンシブ対応（デスクトップ・モバイル）の実装において発見された技術的課題と、今後の改善案を詳細に記録しています。

---

## 🎯 プロジェクトの目標

### 当初の目標
1. Figmaデザインから自動的にHTML/CSSを生成
2. 単一デバイス（主にモバイル）のデザインをコード化
3. セマンティックHTMLとアクセシビリティ対応

### 拡張された目標
1. **レスポンシブ対応**: デスクトップとモバイルの両デザインから統合されたレスポンシブコードを生成
2. **デスクトップファースト**: PC版をベースに、モバイル版との差分をメディアクエリで対応
3. **自動マッピング**: 両デバイスの対応する要素を自動的に紐付け

---

## 🏗️ 現在の実装状況

### 1. ディレクトリ構造

```
figma-to-code/
├── fetch-figma.js           # メインの取得スクリプト（レスポンシブ対応済み）
├── fetch-figma-batch.js     # CSV一括処理用
├── .env                     # FIGMA_URL_DESKTOP / FIGMA_URL_MOBILE
├── PROMPT-COMPLETE.md       # セマンティック対応プロンプト
└── output/
    └── templates/           # プロジェクト名（pageName）
        ├── sections.json    # セクション管理ファイル
        └── sections/
            └── cart/        # セクション名（sectionName）
                ├── index.html
                ├── cart.scss
                ├── desktop/
                │   ├── figma-data.json
                │   └── figma-capture.png
                └── mobile/
                    ├── figma-data.json
                    └── figma-capture.png
```

### 2. 実装済み機能

#### **レスポンシブ対応のfetch-figma.js**
```bash
# .envにDESKTOP/MOBILE URLsを設定後
node fetch-figma.js "" templates

# 処理フロー:
# 1. FIGMA_URL_DESKTOP → desktop/figma-data.json
# 2. FIGMA_URL_MOBILE  → mobile/figma-data.json
```

#### **セマンティックHTML生成（PROMPT-COMPLETE.md）**
- `<main>`, `<article>`, `<section>`, `<ul><li>` 等の適切な要素使用
- アクセシビリティ属性（`aria-*`, `role`）
- BEM命名規則とSCSS構造
- debugディレクトリでのCSS管理

#### **CSV一括処理（fetch-figma-batch.js）**
```csv
page_name,desktop_url,mobile_url
portfolio,https://...,https://...
ecommerce,https://...,https://...
```

---

## 🚧 直面した課題

### 1. Figma API制限（429エラー）

#### **問題**
- 無料プランでは厳しいレート制限がある
- 個別ノード取得方式だと、複数セクションで制限に到達
- 具体的な制限数は非公開だが、1日5リクエスト程度の可能性

#### **現在の対処法**
- API呼び出し間に待機時間を設定
- `Retry-After`ヘッダーの確認
- 翌日まで待つ（日次制限の場合）

### 2. デスクトップ・モバイルのマッピング問題

#### **根本的な問題**
デスクトップ版とモバイル版で、同じコンテンツでも異なるnode-idと名前を持つ：

```json
// Desktop
{"id": "240:6223", "name": "Cart"}

// Mobile
{"id": "350:7891", "name": "Cart Mobile"}
```

#### **試みた解決策と結果**

**a) Component IDによる対応付け**
- 期待: 同じコンポーネントなら共通のcomponentId
- 結果: 別フレームだとIDが異なる場合が多い

**b) 名前の類似度マッチング**
- 期待: "Cart" ↔ "Cart Mobile"を自動判定
- 結果: 誤マッチングのリスクが高い

**c) 階層位置による対応付け**
- 期待: 同じ順番の要素を対応付け
- 結果: デバイスによって要素の順序が変わる

**d) コンテンツベースマッチング（最も有望）**
- テキスト内容（商品名、価格等）で照合
- 1セクション内に限定すれば高精度
- ただし、コンテンツがない場合は困難

### 3. 運用上の判断

#### **1セクション特化アプローチの採用理由**

複数セクションを含む全体ページではなく、1セクションに絞ることで：

1. **マッピング精度の向上**
   - 要素数が限定される（5-10個程度）
   - コンテンツの重複が少ない
   - 誤マッチングのリスク低減

2. **実用性の確保**
   - Cart, Home, Chatなど、機能単位で処理
   - 各セクションは独立して開発可能
   - 段階的な実装が可能

---

## 💡 今後の実装案

### 1. ファイル全体取得 + URL指定抽出方式

#### **コンセプト**
API制限を回避するため、最初に1回だけファイル全体を取得し、その後はオフラインで必要な部分を抽出する。

#### **実装フロー**

```bash
# Step 1: ファイル全体を取得（API呼び出し: 2回のみ）
node fetch-figma-full.js
→ output/cache/desktop-full.json (数十MB)
→ output/cache/mobile-full.json  (数十MB)

# Step 2: URLでセクションを指定して抽出（オフライン処理）
node extract-section.js \
  --desktop-node="240-6223" \
  --mobile-node="350-7891" \
  --section-name="cart"

→ sections/cart/desktop/figma-data.json
→ sections/cart/mobile/figma-data.json
```

#### **メリット**
- API呼び出しは最初の2回のみ
- その後は何度でも抽出可能
- URLによる確実なマッピング
- 複数人での並行作業が可能

#### **実装に必要な関数**

```javascript
// ノードIDでJSON内を再帰的に検索
function findNodeById(jsonData, nodeId) {
  // 実装例
  function search(node) {
    if (node.id === nodeId) return node;
    if (node.children) {
      for (const child of node.children) {
        const found = search(child);
        if (found) return found;
      }
    }
    return null;
  }
  return search(jsonData.document);
}
```

### 2. マッピング設定ファイル方式

#### **sections-mapping.json**
```json
{
  "cart": {
    "desktop": "240:6223",
    "mobile": "350:7891",
    "expectedContent": ["Amazing T-shirt", "€ 12.00"]
  },
  "home": {
    "desktop": "240:6070",
    "mobile": "350:7892",
    "expectedContent": ["Perfect for you", "See more"]
  }
}
```

この設定ファイルを使って、確実なマッピングを維持する。

---

## 📊 比較表: 各アプローチのトレードオフ

| アプローチ | API呼び出し数 | マッピング精度 | 実装複雑度 | 運用難易度 |
|---------|------------|------------|----------|----------|
| **現在: 個別ノード取得** | 多い（セクション数×2） | 高（URL指定） | 低 | 中（API制限） |
| **ファイル全体→抽出** | 少ない（2回） | 高（URL指定） | 中 | 低 |
| **自動マッピング** | 少ない（2回） | 低〜中 | 高 | 高（誤判定） |

---

## 🚀 推奨される移行計画

### Phase 1: 現状維持での改善（短期）
1. API制限エラーの詳細表示を実装 ✅
2. 待機時間の自動調整機能を追加
3. 1セクションずつ確実に処理

### Phase 2: ファイル全体取得の試験（中期）
1. fetch-figma-full.jsの実装
2. extract-section.jsの実装
3. 既存プロジェクトでの検証

### Phase 3: 本番移行（長期）
1. マッピング設定ファイルの整備
2. 既存sections.jsonとの統合
3. チーム全体への展開

---

## 📝 備考

### なぜpageNameが必要か？

`pageName`はプロジェクト全体の名前で、出力ディレクトリの第一階層となります。
- 自動取得: Figmaの「Page 1」など無意味な名前になる可能性
- 手動指定: 「templates」「portfolio」など意味のある名前を設定可能

### セクション vs ページの違い

```
output/
└── templates/        ← pageName（プロジェクト名）
    └── sections/
        ├── cart/     ← sectionName（機能単位）
        ├── home/     ← sectionName（機能単位）
        └── chat/     ← sectionName（機能単位）
```

### API制限の回避策まとめ

1. **有料プラン**: 根本的解決だが、コストがかかる
2. **時間分散**: 日を跨いで処理（現実的だが時間がかかる）
3. **ファイル全体取得**: 技術的解決（実装が必要）
4. **複数トークン**: グレーゾーン（推奨しない）

---

## 🔗 関連ファイル

- `fetch-figma.js` - メインの取得スクリプト
- `fetch-figma-batch.js` - CSV一括処理
- `PROMPT-COMPLETE.md` - セマンティックHTML生成プロンプト
- `urls.csv` - 一括処理用URLリスト
- `.env` - 環境変数（FIGMA_URL_DESKTOP/MOBILE）

---

## 📅 更新履歴

- 2024-11-24: 初版作成
- レスポンシブ対応実装
- API制限問題の発覚
- マッピング課題の整理
- 今後の実装方針の策定

---

このドキュメントは、プロジェクトの技術的な判断の経緯を記録し、今後の開発の指針とすることを目的としています。