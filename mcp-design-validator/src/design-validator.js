#!/usr/bin/env node

import { readFileSync } from 'fs';
import { basename } from 'path';

/**
 * 既存のvalidate-design-fidelity.jsのロジックをMCP用に統合
 */
export class DesignFidelityValidator {
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
    const traverse = (node, depth = 0) => {
      if (!node) return;

      // 色の抽出
      if (node.fills && Array.isArray(node.fills)) {
        node.fills.forEach(fill => {
          if (fill.type === 'SOLID' && fill.color) {
            const rgba = this.rgbToRgba(fill.color, fill.opacity || 1);
            const hex = this.rgbToHex(fill.color);
            this.report.colors.expected.push({
              rgba,
              hex,
              element: node.name || 'Unknown',
              type: 'fill',
              source: filename
            });
          }
        });
      }

      // フォントサイズの抽出
      if (node.style && node.style.fontSize) {
        this.report.fonts.expected.push({
          fontSize: node.style.fontSize,
          fontWeight: node.style.fontWeight || 400,
          fontFamily: node.style.fontFamily || 'Unknown',
          element: node.name || 'Unknown',
          source: filename
        });
      }

      // サイズの抽出
      if (node.width !== undefined && node.height !== undefined) {
        this.report.sizes.expected.push({
          width: Math.round(node.width),
          height: Math.round(node.height),
          element: node.name || 'Unknown',
          source: filename
        });
      }

      // 子要素を再帰処理
      const children = node.children || node.child || [];
      children.forEach(child => traverse(child, depth + 1));
    };

    // ルートから開始
    if (jsonData.nodes) {
      const nodeId = Object.keys(jsonData.nodes)[0];
      traverse(jsonData.nodes[nodeId].document);
    } else if (jsonData.document) {
      traverse(jsonData.document);
    } else if (jsonData.type && jsonData.name) {
      traverse(jsonData);
    }
  }

  // CSS/HTMLから実装値を抽出
  extractFromCssHtml(cssContent, htmlContent = '') {
    const content = cssContent + '\n' + htmlContent;

    // 色の抽出（様々な形式に対応）
    const colorPatterns = [
      /(?:background-color|color|border-color|fill):\s*([^;]+);/g,
      /#([0-9a-fA-F]{3,6})/g,
      /rgba?\([^)]+\)/g,
      /hsla?\([^)]+\)/g
    ];

    colorPatterns.forEach(pattern => {
      let match;
      while ((match = pattern.exec(content)) !== null) {
        const color = match[1] || match[0];
        if (color && !this.report.colors.found.includes(color.trim())) {
          this.report.colors.found.push(color.trim());
        }
      }
    });

    // フォントサイズの抽出
    const fontSizePattern = /font-size:\s*([^;]+);/g;
    let fontMatch;
    while ((fontMatch = fontSizePattern.exec(content)) !== null) {
      const fontSize = fontMatch[1].trim();
      if (!this.report.fonts.found.includes(fontSize)) {
        this.report.fonts.found.push(fontSize);
      }
    }
  }

  // 差分分析
  analyzeDiscrepancies() {
    // 期待される色と実装済み色の比較
    this.report.colors.expected.forEach(expectedColor => {
      const found = this.report.colors.found.some(foundColor => {
        return foundColor.includes(expectedColor.rgba) ||
               foundColor.includes(expectedColor.hex) ||
               foundColor.toLowerCase().includes(expectedColor.hex.toLowerCase());
      });

      if (!found) {
        this.report.colors.missing.push(expectedColor);
      }
    });

    // フォントの警告生成
    const expectedSizes = this.report.fonts.expected.map(f => `${f.fontSize}px`);
    const foundSizes = this.report.fonts.found;
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

  // 修正提案生成
  generateFixSuggestions() {
    const suggestions = [];

    this.report.colors.missing.forEach(color => {
      suggestions.push({
        type: 'color',
        element: color.element,
        expected: color.rgba,
        hex: color.hex,
        cssRule: `.${this.sanitizeClassName(color.element)} { background-color: ${color.rgba}; /* ${color.hex} */ }`,
        description: `Add missing color: ${color.element} should have background-color: ${color.rgba}`
      });
    });

    this.report.fonts.expected.forEach(font => {
      const sizeFound = this.report.fonts.found.includes(`${font.fontSize}px`);
      if (!sizeFound) {
        suggestions.push({
          type: 'font',
          element: font.element,
          expected: `${font.fontSize}px`,
          cssRule: `.${this.sanitizeClassName(font.element)} { font-size: ${font.fontSize}px; font-weight: ${font.fontWeight}; }`,
          description: `Add missing font: ${font.element} should have font-size: ${font.fontSize}px`
        });
      }
    });

    return suggestions;
  }

  // クラス名をサニタイズ
  sanitizeClassName(name) {
    return name.toLowerCase()
              .replace(/[^a-z0-9-_]/g, '-')
              .replace(/^-+|-+$/g, '')
              .replace(/-+/g, '-') || 'element';
  }

  // メイン検証関数
  async validate(figmaJsonPath, cssPath, htmlPath = null) {
    try {
      // ファイル読み込み
      const jsonData = JSON.parse(readFileSync(figmaJsonPath, 'utf8'));
      const cssContent = readFileSync(cssPath, 'utf8');
      const htmlContent = htmlPath ? readFileSync(htmlPath, 'utf8') : '';

      const jsonFilename = basename(figmaJsonPath);

      // 抽出と分析
      this.extractFromFigmaJson(jsonData, jsonFilename);
      this.extractFromCssHtml(cssContent, htmlContent);
      this.analyzeDiscrepancies();

      // 修正提案生成
      const suggestions = this.generateFixSuggestions();

      return {
        success: true,
        fidelityScore: this.report.summary.fidelityScore,
        summary: this.report.summary,
        missingColors: this.report.colors.missing,
        missingFonts: this.report.fonts.missing,
        warnings: this.report.warnings,
        suggestions,
        timestamp: new Date().toISOString(),
        report: this.report
      };

    } catch (error) {
      return {
        success: false,
        error: error.message,
        timestamp: new Date().toISOString()
      };
    }
  }
}