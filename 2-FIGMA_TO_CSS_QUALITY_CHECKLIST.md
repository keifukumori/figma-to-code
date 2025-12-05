---

# Figma to CSS実装 品質保証チェックリスト

> **目的**: Figma JSONデータから100%正確なCSS実装を行うための包括的チェックリスト
> **対象**: デザイン→コード変換時の品質管理・見落とし防止

## 🚨 実装前 必須確認（STOP & CHECK）

### **A. JSON値抽出の徹底**

**全ての数値・色・文字属性はJSONから抽出必須**

- [ ] 全要素の`absoluteBoundingBox` (width/height) をJSONから抽出済み
- [ ] 全テキストの`fontSize`/`fontWeight`/`lineHeight` をJSONから抽出済み
- [ ] 全色要素の`fills[0].color` をJSONから抽出済み（r,g,b→RGB変換）
- [ ] 全ボタンのbackground色をJSONから抽出済み
- [ ] 全アイコンの`color`値をJSONから抽出済み
- [ ] `padding`/`margin`/`itemSpacing` をJSONから抽出済み
- [ ] `cornerRadius`/`borderRadius` をJSONから抽出済み

**❌ 推測値使用禁止**: 「だいたい○○px」「○○色っぽい」は絶対NG

### **B. 類似要素の比較確認**

**同種要素の仕様統一確認（推測実装防止）**

- [ ] 同じ種類のボタンは全て色を比較確認（推測実装防止）
- [ ] 同じ種類のテキストは全てサイズを比較確認
- [ ] 同じ種類のアイコンは全て色・サイズを比較確認
- [ ] リスト系要素は境界線/間隔を全て比較確認
- [ ] 状態違い要素（active/inactive等）は全て比較確認

**例: +/-ボタンがある場合**
```
確認必須項目:
- +ボタンの fills[0].color = ?
- -ボタンの fills[0].color = ?
- +アイコンの color = ?
- -アイコンの color = ?
→ 全て確認してから実装開始
```

## 📏 サイズ・レイアウト確認

### **C. 寸法の精密確認**

- [ ] 全要素の実サイズ（小数点以下まで）をJSONから取得
- [ ] 親子関係の寸法整合性を確認
- [ ] レスポンシブ時の計算式を確認
- [ ] auto-layoutの`itemSpacing`を正確に反映
- [ ] paddingの上下左右個別値を確認

**⚠️ 注意**: キャプチャの目視サイズではなく、JSON数値を優先

### **D. 配置・間隔の確認**

- [ ] `layoutMode` (VERTICAL/HORIZONTAL) をJSONから確認
- [ ] `itemSpacing`値をJSONから確認
- [ ] `alignItems`/`justifyContent`設定をJSONから確認
- [ ] `absolutePosition`座標をJSONから確認
- [ ] z-index/layer順序をJSONから確認

## 🎨 色・スタイル確認

### **E. 色の厳密確認**

- [ ] 背景色: `fills[0].color` のr,g,b値を255倍してRGB値算出
- [ ] テキスト色: `fills[0].color` のr,g,b値を255倍してRGB値算出
- [ ] ボーダー色: `strokes[0].color` のr,g,b値を255倍してRGB値算出
- [ ] アイコン色: `fill`/`color`値のr,g,b値を255倍してRGB値算出
- [ ] グラデーション: `gradientStops`全てのposition/colorを確認

**計算例**: `r:0.83` → `0.83 × 255 = 211.65` → `212`

### **F. タイポグラフィの確認**

- [ ] `fontSize`: JSON値そのまま（推測禁止）
- [ ] `fontWeight`: JSON値そのまま（400,700等）
- [ ] `lineHeight`: `lineHeightPx`値を使用（単位確認）
- [ ] `letterSpacing`: JSON値をそのまま使用
- [ ] `fontFamily`: JSON値をそのまま使用
- [ ] `textAlign`: `textAlignHorizontal`をCSS `text-align`に変換

## 🔗 構造・インタラクション確認

### **G. HTML構造の確認**

- [ ] JSON階層構造をHTMLの親子関係で正確に再現
- [ ] `componentId`要素を適切なHTMLタグに変換
- [ ] セマンティックHTML (article/section/header/footer) を適用
- [ ] ARIA属性/accessibility を考慮
- [ ] class命名規則（BEM的）を統一適用

### **H. ボタン・インタラクション確認**

- [ ] ボタン要素のhover状態を定義
- [ ] focus状態のアクセシビリティを定義
- [ ] active状態の視覚フィードバックを定義
- [ ] disabled状態（該当する場合）を定義
- [ ] 基本的なJavaScript動作を実装（数量変更等）

## ✅ 実装後 品質確認

### **I. 視覚的一致度確認**

- [ ] キャプチャ画像と実装結果を並べて全要素チェック
- [ ] 色の一致度: 各要素の色を個別確認
- [ ] サイズの一致度: 各要素の大きさを個別確認
- [ ] 間隔の一致度: padding/margin/gapを個別確認
- [ ] 配置の一致度: left/right/center等の配置確認

### **J. レスポンシブ確認**

- [ ] モバイル表示での崩れチェック
- [ ] タブレット表示での崩れチェック
- [ ] デスクトップ表示での崩れチェック
- [ ] 文字サイズ変更時の崩れチェック
- [ ] 長いテキスト入力時の崩れチェック

### **K. クロスブラウザ確認**

- [ ] Chrome での表示確認
- [ ] Safari での表示確認
- [ ] Firefox での表示確認
- [ ] モバイルブラウザでの確認
- [ ] 高DPI/Retina表示での確認

## 🚦 最終品質ゲート

### **L. 実装完了前の最終確認**

- [ ] 推測値を一切使用していないことを確認
- [ ] 全JSON値が正確にCSSに反映されていることを確認
- [ ] キャプチャとの視覚的一致度95%以上を確認
- [ ] HTMLバリデーションをパス
- [ ] CSSバリデーションをパス
- [ ] アクセシビリティチェックをパス
- [ ] パフォーマンス（ファイルサイズ等）をチェック

**🎯 目標**: JSON値100%反映 + キャプチャ95%以上一致

---

## 📋 チェックリスト実行例

### **実装開始前の確認:**

```markdown
✅ +ボタンのJSON fills[0].color = rgba(234,242,255,1) 確認済み
✅ -ボタンのJSON fills[0].color = rgba(234,242,255,1) 確認済み
✅ 両ボタンとも同色と判明、推測実装回避
✅ ボタンサイズ 24px×24px JSON確認済み
✅ 実装開始可能
```

### **実装後の確認:**

```markdown
✅ キャプチャと並べて色確認 - 一致
✅ キャプチャと並べてサイズ確認 - 一致
✅ レスポンシブ確認 - 問題なし
✅ 品質ゲート通過
```

---

## 🛠 よくある失敗パターンと対策

### **失敗パターン1: 推測による色実装**
```css
/* ❌ 間違い */
.button { background: #0066FF; /* 「青っぽい」推測 */ }

/* ✅ 正解 */
.button { background: rgba(234, 242, 255, 1); /* JSON r:0.92, g:0.95, b:1 */ }
```

### **失敗パターン2: 類似要素の仕様確認不足**
```css
/* ❌ 間違い: +/-ボタンを推測で別色実装 */
.minus-btn { background: #EAF2FF; }
.plus-btn { background: #006FFD; } /* 推測実装 */

/* ✅ 正解: JSON確認で同色判明 */
.minus-btn, .plus-btn { background: #EAF2FF; } /* 両方JSON確認済み */
```

### **失敗パターン3: サイズの目視推測**
```css
/* ❌ 間違い */
.button { width: 40px; height: 40px; /* キャプチャ目視推測 */ }

/* ✅ 正解 */
.button { width: 24px; height: 24px; /* JSON absoluteBoundingBox値 */ }
```

---

## 📚 参考リンク

- [3-PROMPT-SAFE.md](./3-PROMPT-SAFE.md) - 基本実装ガイドライン
- [Figma JSON構造解析ガイド](./figma-json-analysis.md)
- [CSS実装ベストプラクティス](./css-best-practices.md)

---

**💡 重要**: このチェックリストを**段階ごとに機械的に実行**することで、推測実装を完全排除し、JSON値の100%正確な反映を実現できます。