#!/usr/bin/env node

const fs = require('fs');
const path = require('path');

/**
 * Figma JSONとCSS/HTMLの設計忠実度検証ツール
 * JSONから期待される色・フォント・サイズを抽出し、生成されたCSS/HTMLと比較
 */

class DesignFidelityValidator {
  constructor() {
    this.report = {
      colors: { expected: [], found: [], missing: [] },
      fonts: { expected: [], found: [], missing: [] },
      sizes: { expected: [], found: [], missing: [] },
      warnings: [],
      summary: {}
    };
  }

  // RGB値をrgba文字列に変換
  rgbToRgba(rgbObj, alpha = 1) {
    const r = Math.round(rgbObj.r * 255);
    const g = Math.round(rgbObj.g * 255);
    const b = Math.round(rgbObj.b * 255);
    return `rgba(${r}, ${g}, ${b}, ${alpha})`;
  }

  // HEX色に変換
  rgbToHex(rgbObj) {
    const r = Math.round(rgbObj.r * 255).toString(16).padStart(2, '0');
    const g = Math.round(rgbObj.g * 255).toString(16).padStart(2, '0');
    const b = Math.round(rgbObj.b * 255).toString(16).padStart(2, '0');
    return `#${r}${g}${b}`;
  }

  // Figma JSONから設計要素を抽出
  extractFromFigmaJson(jsonData, filename = 'unknown') {
    console.log(`📊 ${filename} から設計要素を抽出中...`);

    const traverse = (node, depth = 0) => {
      if (!node) return;

      // 色の抽出
      if (node.fills && Array.isArray(node.fills)) {
        node.fills.forEach(fill => {
          if (fill.type === 'SOLID' && fill.color) {
            const rgba = this.rgbToRgba(fill.color, fill.opacity || 1);
            const hex = this.rgbToHex(fill.color);
            this.report.colors.expected.push({
              rgba: rgba,
              hex: hex,
              element: node.name || 'unnamed',
              type: 'fill',
              source: filename
            });
          }
        });
      }

      // テキスト色の抽出
      if (node.style && node.style.fills) {
        node.style.fills.forEach(fill => {
          if (fill.type === 'SOLID' && fill.color) {
            const rgba = this.rgbToRgba(fill.color, fill.opacity || 1);
            const hex = this.rgbToHex(fill.color);
            this.report.colors.expected.push({
              rgba: rgba,
              hex: hex,
              element: node.name || node.characters || 'text',
              type: 'text',
              source: filename
            });
          }
        });
      }

      // フォント情報の抽出
      if (node.style && node.style.fontFamily) {
        this.report.fonts.expected.push({
          family: node.style.fontFamily,
          weight: node.style.fontWeight || 'normal',
          size: node.style.fontSize || 'unknown',
          element: node.name || node.characters || 'text',
          source: filename
        });
      }

      // サイズ情報の抽出
      if (node.absoluteBoundingBox) {
        this.report.sizes.expected.push({
          width: node.absoluteBoundingBox.width,
          height: node.absoluteBoundingBox.height,
          element: node.name || 'unnamed',
          type: node.type,
          source: filename
        });
      }

      // 子要素を再帰処理
      if (node.children) {
        node.children.forEach(child => traverse(child, depth + 1));
      }
    };

    // JSONデータの形式を判定
    let rootNode;
    if (jsonData.nodes) {
      // Figma API形式
      const nodeId = Object.keys(jsonData.nodes)[0];
      rootNode = jsonData.nodes[nodeId].document;
    } else if (jsonData.document) {
      // ドキュメント形式
      rootNode = jsonData.document;
    } else if (jsonData.type && jsonData.name) {
      // 直接ノード形式
      rootNode = jsonData;
    } else {
      console.warn(`⚠️ 不明なJSON形式: ${filename}`);
      return;
    }

    traverse(rootNode);
  }

  // CSS/HTMLファイルから使用されている色・フォント・サイズを抽出
  extractFromCssHtml(cssContent, htmlContent = '') {
    console.log(`🔍 CSS/HTMLから実際の値を抽出中...`);

    const content = cssContent + ' ' + htmlContent;

    // 色の抽出（rgba, rgb, hex）
    const colorRegexes = [
      /rgba?\(\s*(\d+)\s*,\s*(\d+)\s*,\s*(\d+)\s*(?:,\s*([\d.]+))?\s*\)/gi,
      /#([0-9a-f]{6}|[0-9a-f]{3})/gi
    ];

    colorRegexes.forEach(regex => {
      let match;
      while ((match = regex.exec(content)) !== null) {
        if (match[0].includes('rgba') || match[0].includes('rgb')) {
          const r = parseInt(match[1]);
          const g = parseInt(match[2]);
          const b = parseInt(match[3]);
          const a = match[4] ? parseFloat(match[4]) : 1;
          this.report.colors.found.push(`rgba(${r}, ${g}, ${b}, ${a})`);
        } else {
          this.report.colors.found.push(match[0].toLowerCase());
        }
      }
    });

    // フォントサイズの抽出
    const fontSizeRegex = /font-size:\s*([\d.]+)(px|em|rem|%)/gi;
    let match;
    while ((match = fontSizeRegex.exec(content)) !== null) {
      this.report.sizes.found.push({
        value: match[1] + match[2],
        type: 'font-size',
        unit: match[2]
      });
    }

    // フォントファミリーの抽出
    const fontFamilyRegex = /font-family:\s*([^;]+)/gi;
    while ((match = fontFamilyRegex.exec(content)) !== null) {
      this.report.fonts.found.push(match[1].trim());
    }

    // 重複を削除
    this.report.colors.found = [...new Set(this.report.colors.found)];
    this.report.fonts.found = [...new Set(this.report.fonts.found)];
  }

  // 比較分析を実行
  analyzeDiscrepancies() {
    console.log(`📋 差分分析を実行中...`);

    // 色の比較
    const expectedColors = this.report.colors.expected.map(c => c.rgba);
    const foundColors = this.report.colors.found;

    this.report.colors.missing = this.report.colors.expected.filter(expected => {
      return !foundColors.some(found => {
        return found.toLowerCase().includes(expected.rgba.toLowerCase()) ||
               found.toLowerCase().includes(expected.hex.toLowerCase());
      });
    });

    // フォントサイズの比較
    const expectedSizes = this.report.fonts.expected
      .filter(f => f.size !== 'unknown')
      .map(f => f.size + 'px');

    const foundSizes = this.report.sizes.found
      .filter(s => s.type === 'font-size')
      .map(s => s.value);

    const missingSizes = expectedSizes.filter(size => !foundSizes.includes(size));
    if (missingSizes.length > 0) {
      this.report.warnings.push(`Missing font sizes: ${missingSizes.join(', ')}`);
    }

    // サマリー生成
    this.report.summary = {
      totalColorsExpected: this.report.colors.expected.length,
      totalColorsFound: this.report.colors.found.length,
      missingColors: this.report.colors.missing.length,
      totalFontsExpected: this.report.fonts.expected.length,
      totalFontsFound: this.report.fonts.found.length,
      fidelityScore: this.calculateFidelityScore()
    };
  }

  // 忠実度スコア計算
  calculateFidelityScore() {
    const totalExpected = this.report.colors.expected.length;
    const totalMissing = this.report.colors.missing.length;

    if (totalExpected === 0) return 100;

    return Math.round((1 - (totalMissing / totalExpected)) * 100);
  }

  // レポートを生成
  generateReport() {
    console.log(`\n🎯 設計忠実度検証レポート`);
    console.log(`${'='.repeat(50)}\n`);

    // サマリー
    console.log(`📊 サマリー:`);
    console.log(`   忠実度スコア: ${this.report.summary.fidelityScore}%`);
    console.log(`   期待色数: ${this.report.summary.totalColorsExpected}`);
    console.log(`   発見色数: ${this.report.summary.totalColorsFound}`);
    console.log(`   未実装色数: ${this.report.summary.missingColors}\n`);

    // 未実装の色
    if (this.report.colors.missing.length > 0) {
      console.log(`❌ 未実装の色 (${this.report.colors.missing.length}件):`);
      this.report.colors.missing.forEach(color => {
        console.log(`   🎨 ${color.rgba} (${color.hex}) - ${color.element} (${color.type}) [${color.source}]`);
      });
      console.log('');
    }

    // 警告
    if (this.report.warnings.length > 0) {
      console.log(`⚠️ 警告 (${this.report.warnings.length}件):`);
      this.report.warnings.forEach(warning => {
        console.log(`   ${warning}`);
      });
      console.log('');
    }

    // 実装済みの色（参考）
    console.log(`✅ 実装済みの色 (${this.report.colors.found.length}件):`);
    this.report.colors.found.slice(0, 10).forEach(color => {
      console.log(`   🎨 ${color}`);
    });
    if (this.report.colors.found.length > 10) {
      console.log(`   ... および ${this.report.colors.found.length - 10} 件の追加色\n`);
    } else {
      console.log('');
    }

    return this.report;
  }

  // JSONレポートを保存
  saveJsonReport(outputPath) {
    fs.writeFileSync(outputPath, JSON.stringify(this.report, null, 2));
    console.log(`📄 詳細レポートを保存: ${outputPath}`);
  }

  // 修正提案を生成
  generateFixSuggestions() {
    const suggestions = [];

    this.report.colors.missing.forEach(color => {
      suggestions.push({
        type: 'color',
        element: color.element,
        expected: color.rgba,
        hex: color.hex,
        suggestion: `Add missing color: ${color.element} should have background-color: ${color.rgba}; /* ${color.hex} */`
      });
    });

    return suggestions;
  }
}

// コマンドライン実行
async function validateDesignFidelity(figmaJsonPath, cssPath, htmlPath = null, outputDir = null) {
  const validator = new DesignFidelityValidator();

  try {
    // Figma JSONファイル読み込み
    console.log(`📂 Figma JSONファイルを読み込み: ${figmaJsonPath}`);
    const jsonData = JSON.parse(fs.readFileSync(figmaJsonPath, 'utf8'));
    const jsonFilename = path.basename(figmaJsonPath);
    validator.extractFromFigmaJson(jsonData, jsonFilename);

    // CSS読み込み
    console.log(`📂 CSSファイルを読み込み: ${cssPath}`);
    const cssContent = fs.readFileSync(cssPath, 'utf8');

    // HTML読み込み（オプション）
    let htmlContent = '';
    if (htmlPath && fs.existsSync(htmlPath)) {
      console.log(`📂 HTMLファイルを読み込み: ${htmlPath}`);
      htmlContent = fs.readFileSync(htmlPath, 'utf8');
    }

    validator.extractFromCssHtml(cssContent, htmlContent);
    validator.analyzeDiscrepancies();

    // レポート生成
    const report = validator.generateReport();

    // 修正提案
    const suggestions = validator.generateFixSuggestions();
    if (suggestions.length > 0) {
      console.log(`🔧 修正提案 (${suggestions.length}件):`);
      suggestions.forEach((s, i) => {
        console.log(`   ${i + 1}. ${s.suggestion}`);
      });
      console.log('');
    }

    // JSONレポート保存
    if (outputDir) {
      if (!fs.existsSync(outputDir)) {
        fs.mkdirSync(outputDir, { recursive: true });
      }
      const reportPath = path.join(outputDir, 'design-fidelity-report.json');
      validator.saveJsonReport(reportPath);
    }

    return { report, suggestions };

  } catch (error) {
    console.error('❌ 検証エラー:', error.message);
    process.exit(1);
  }
}

// コマンドライン実行
if (require.main === module) {
  const args = process.argv.slice(2);

  if (args.length < 2) {
    console.log(`
📋 設計忠実度検証ツール - Figma JSON vs CSS/HTML比較

使用方法:
  node validate-design-fidelity.js <figma-json-path> <css-path> [html-path] [output-dir]

例:
  node validate-design-fidelity.js ./desktop/figma-data.json ./styles.css ./index.html ./reports
  node validate-design-fidelity.js ./figma-data-simplified.json ./component.css

引数:
  figma-json-path  Figma JSONファイルパス（必須）
  css-path         CSSファイルパス（必須）
  html-path        HTMLファイルパス（オプション）
  output-dir       レポート出力ディレクトリ（オプション）

機能:
  ✅ 色の比較（background-color, color, fills）
  ✅ フォントサイズ・ファミリーの比較
  ✅ 未実装要素の検出
  ✅ 忠実度スコア算出
  ✅ 修正提案の生成
    `);
    process.exit(1);
  }

  const figmaJsonPath = args[0];
  const cssPath = args[1];
  const htmlPath = args[2] || null;
  const outputDir = args[3] || path.dirname(cssPath); // デフォルトでCSS同じディレクトリに保存

  validateDesignFidelity(figmaJsonPath, cssPath, htmlPath, outputDir);
}

module.exports = { DesignFidelityValidator, validateDesignFidelity };