import { readFileSync, writeFileSync } from 'fs';

/**
 * CSS自動修正機能
 * 検証結果に基づいてCSSファイルを自動修正
 */
export class AutoFixer {
  constructor() {
    this.appliedFixes = [];
  }

  /**
   * 修正提案をCSSファイルに自動適用
   */
  async applyFixes(cssPath, suggestions) {
    try {
      let cssContent = readFileSync(cssPath, 'utf8');
      const originalContent = cssContent;

      this.appliedFixes = [];

      // 色の修正を適用
      const colorFixes = suggestions.filter(s => s.type === 'color');
      cssContent = this.applyColorFixes(cssContent, colorFixes);

      // フォントの修正を適用
      const fontFixes = suggestions.filter(s => s.type === 'font');
      cssContent = this.applyFontFixes(cssContent, fontFixes);

      // レイアウトの修正を適用
      const layoutFixes = suggestions.filter(s => s.type === 'layout');
      cssContent = this.applyLayoutFixes(cssContent, layoutFixes);

      // ファイルを更新
      if (cssContent !== originalContent) {
        writeFileSync(cssPath, cssContent, 'utf8');
      }

      return {
        success: true,
        appliedFixes: this.appliedFixes,
        totalFixes: this.appliedFixes.length,
        message: `${this.appliedFixes.length}件の修正を適用しました`
      };

    } catch (error) {
      return {
        success: false,
        error: error.message,
        appliedFixes: []
      };
    }
  }

  /**
   * 色の修正を適用
   */
  applyColorFixes(cssContent, colorFixes) {
    colorFixes.forEach(fix => {
      const className = fix.element ? this.sanitizeClassName(fix.element) : 'unknown-element';

      // クラスが既に存在するかチェック
      const classPattern = new RegExp(`\\.${className}\\s*\\{[^}]*\\}`, 'g');
      const classExists = classPattern.test(cssContent);

      if (classExists) {
        // 既存のクラスに背景色を追加/更新
        cssContent = cssContent.replace(
          new RegExp(`(\\.${className}\\s*\\{[^}]*?)\\}`, 'g'),
          (match, beforeBrace) => {
            // 既存の background-color を削除
            const withoutBgColor = beforeBrace.replace(/background-color:[^;]*;?/g, '');
            return `${withoutBgColor.trim()}
  background-color: ${fix.expected}; /* ${fix.hex} - Auto-fixed */
}`
          }
        );
      } else {
        // 新しいクラスを追加
        const newRule = `
/* Auto-generated: ${fix.element} */
.${className} {
  background-color: ${fix.expected}; /* ${fix.hex} */
}`;
        cssContent += newRule;
      }

      this.appliedFixes.push({
        type: 'color',
        element: fix.element,
        className: className,
        property: 'background-color',
        value: fix.expected,
        action: classExists ? 'updated' : 'created'
      });
    });

    return cssContent;
  }

  /**
   * フォントの修正を適用
   */
  applyFontFixes(cssContent, fontFixes) {
    fontFixes.forEach(fix => {
      const className = fix.element ? this.sanitizeClassName(fix.element) : 'unknown-element';

      const classPattern = new RegExp(`\\.${className}\\s*\\{[^}]*\\}`, 'g');
      const classExists = classPattern.test(cssContent);

      if (classExists) {
        // 既存のクラスにフォントサイズを追加/更新
        cssContent = cssContent.replace(
          new RegExp(`(\\.${className}\\s*\\{[^}]*?)\\}`, 'g'),
          (match, beforeBrace) => {
            let updatedClass = beforeBrace;

            // 既存の font-size を削除
            updatedClass = updatedClass.replace(/font-size:[^;]*;?/g, '');

            return `${updatedClass.trim()}
  font-size: ${fix.expected}; /* Auto-fixed */
}`
          }
        );
      } else {
        // 新しいクラスを追加
        const newRule = `
/* Auto-generated: ${fix.element} */
.${className} {
  font-size: ${fix.expected};
}`;
        cssContent += newRule;
      }

      this.appliedFixes.push({
        type: 'font',
        element: fix.element,
        className: className,
        property: 'font-size',
        value: fix.expected,
        action: classExists ? 'updated' : 'created'
      });
    });

    return cssContent;
  }

  /**
   * レイアウトの修正を適用
   */
  applyLayoutFixes(cssContent, layoutFixes) {
    layoutFixes.forEach(fix => {
      const className = fix.element ? this.sanitizeClassName(fix.element) : 'unknown-element';

      const classPattern = new RegExp(`\\.${className}\\s*\\{[^}]*\\}`, 'g');
      const classExists = classPattern.test(cssContent);

      if (classExists) {
        cssContent = cssContent.replace(
          new RegExp(`(\\.${className}\\s*\\{[^}]*?)\\}`, 'g'),
          (match, beforeBrace) => {
            let updatedClass = beforeBrace;

            // 既存のプロパティを削除
            if (fix.property === 'width') {
              updatedClass = updatedClass.replace(/width:[^;]*;?/g, '');
            } else if (fix.property === 'height') {
              updatedClass = updatedClass.replace(/height:[^;]*;?/g, '');
            }

            return `${updatedClass.trim()}
  ${fix.property}: ${fix.expected}; /* Auto-fixed */
}`
          }
        );
      } else {
        const newRule = `
/* Auto-generated: ${fix.element} */
.${className} {
  ${fix.property}: ${fix.expected};
}`;
        cssContent += newRule;
      }

      this.appliedFixes.push({
        type: 'layout',
        element: fix.element,
        className: className,
        property: fix.property,
        value: fix.expected,
        action: classExists ? 'updated' : 'created'
      });
    });

    return cssContent;
  }

  /**
   * スマート修正: より高度な修正ロジック
   */
  async smartFix(cssPath, validationResult) {
    try {
      let cssContent = readFileSync(cssPath, 'utf8');
      const suggestions = [];

      // 高度な色分析
      if (validationResult.fidelityScore < 90) {
        // カスタム変数の提案
        const missingColors = validationResult.missingColors || [];
        const colorVariables = this.generateColorVariables(missingColors);

        if (colorVariables) {
          cssContent = this.insertColorVariables(cssContent, colorVariables);
          suggestions.push({
            type: 'enhancement',
            description: 'CSS変数を追加してメンテナビリティを向上'
          });
        }
      }

      // レスポンシブ対応の提案
      if (!cssContent.includes('@media')) {
        const responsiveRules = this.generateResponsiveRules(validationResult);
        cssContent += responsiveRules;
        suggestions.push({
          type: 'enhancement',
          description: 'レスポンシブデザインのメディアクエリを追加'
        });
      }

      writeFileSync(cssPath, cssContent, 'utf8');

      return {
        success: true,
        enhancements: suggestions,
        message: 'スマート修正を適用しました'
      };

    } catch (error) {
      return {
        success: false,
        error: error.message
      };
    }
  }

  /**
   * CSS変数を生成
   */
  generateColorVariables(missingColors) {
    if (!missingColors.length) return '';

    const variables = missingColors.map(color =>
      `  --color-${this.sanitizeClassName(color.element)}: ${color.hex};`
    ).join('\n');

    return `:root {
${variables}
}

`;
  }

  /**
   * CSS変数を挿入
   */
  insertColorVariables(cssContent, variables) {
    // 既存の :root があるかチェック
    if (cssContent.includes(':root')) {
      return cssContent.replace(
        /:root\s*\{[^}]*\}/,
        (match) => match.slice(0, -1) + variables.slice(8) // :root { を除去して追加
      );
    } else {
      return variables + cssContent;
    }
  }

  /**
   * レスポンシブルールを生成
   */
  generateResponsiveRules(validationResult) {
    return `

/* Auto-generated responsive rules */
@media (max-width: 768px) {
  .container {
    padding: 1rem;
  }

  .title {
    font-size: 1.5rem;
  }
}

@media (min-width: 1200px) {
  .container {
    max-width: 1200px;
    margin: 0 auto;
  }
}`;
  }

  /**
   * クラス名をサニタイズ
   */
  sanitizeClassName(name) {
    return name.toLowerCase()
              .replace(/[^a-z0-9-_]/g, '-')
              .replace(/^-+|-+$/g, '')
              .replace(/-+/g, '-') || 'element';
  }
}