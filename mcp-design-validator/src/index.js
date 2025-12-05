#!/usr/bin/env node

import { Server } from '@modelcontextprotocol/sdk/server/index.js';
import { StdioServerTransport } from '@modelcontextprotocol/sdk/server/stdio.js';
import { DesignFidelityValidator } from './design-validator.js';
import { AutoFixer } from './auto-fixer.js';
import { readFileSync, writeFileSync, existsSync } from 'fs';
import { basename, dirname, join } from 'path';

/**
 * MCP Design Validation Server
 * Figma設計忠実度検証と自動修正のMCPサーバー
 */
class DesignValidationServer {
  constructor() {
    this.server = new Server({
      name: "design-validation-server",
      version: "1.0.0"
    }, {
      capabilities: {
        tools: {}
      }
    });

    this.validator = new DesignFidelityValidator();
    this.autoFixer = new AutoFixer();
    this.setupHandlers();
  }

  setupHandlers() {
    // ツール一覧の設定
    this.server.setRequestHandler('tools/list', { description: "List available tools" }, async () => {
      return {
        tools: [
          {
            name: "validate_design_fidelity",
            description: "Figma JSONとCSS/HTMLの設計忠実度を検証し、詳細レポートを生成",
            inputSchema: {
              type: "object",
              properties: {
                figmaJsonPath: {
                  type: "string",
                  description: "Figma JSONファイルパス (figma-data.json or figma-data-simplified.json)"
                },
                cssPath: {
                  type: "string",
                  description: "CSSファイルパス (style.css, cart.css, etc.)"
                },
                htmlPath: {
                  type: "string",
                  description: "HTMLファイルパス (オプション)"
                }
              },
              required: ["figmaJsonPath", "cssPath"]
            }
          },
          {
            name: "auto_fix_design_issues",
            description: "検証で発見された設計の問題を自動修正",
            inputSchema: {
              type: "object",
              properties: {
                cssPath: {
                  type: "string",
                  description: "修正対象のCSSファイルパス"
                },
                suggestions: {
                  type: "array",
                  description: "validate_design_fidelityからの修正提案配列"
                },
                backupOriginal: {
                  type: "boolean",
                  description: "元ファイルのバックアップを作成するか",
                  default: true
                }
              },
              required: ["cssPath", "suggestions"]
            }
          },
          {
            name: "complete_design_workflow",
            description: "設計検証→自動修正→再検証の完全ワークフローを実行",
            inputSchema: {
              type: "object",
              properties: {
                figmaJsonPath: {
                  type: "string",
                  description: "Figma JSONファイルパス"
                },
                cssPath: {
                  type: "string",
                  description: "CSSファイルパス"
                },
                htmlPath: {
                  type: "string",
                  description: "HTMLファイルパス (オプション)"
                },
                targetScore: {
                  type: "number",
                  description: "目標忠実度スコア (デフォルト: 95)",
                  default: 95
                }
              },
              required: ["figmaJsonPath", "cssPath"]
            }
          }
        ]
      };
    });

    // ツール実行ハンドラー
    this.server.setRequestHandler('tools/call', { description: "Execute a tool" }, async (request) => {
      const { name, arguments: args } = request.params;

      try {
        switch (name) {
          case 'validate_design_fidelity':
            return await this.validateDesignFidelity(args);

          case 'auto_fix_design_issues':
            return await this.autoFixDesignIssues(args);

          case 'complete_design_workflow':
            return await this.completeDesignWorkflow(args);

          default:
            throw new Error(`Unknown tool: ${name}`);
        }
      } catch (error) {
        return {
          content: [{
            type: "text",
            text: `❌ エラー: ${error.message}`
          }],
          isError: true
        };
      }
    });
  }

  /**
   * 設計忠実度検証
   */
  async validateDesignFidelity({ figmaJsonPath, cssPath, htmlPath }) {
    try {
      // パス存在確認
      if (!existsSync(figmaJsonPath)) {
        throw new Error(`Figma JSONファイルが見つかりません: ${figmaJsonPath}`);
      }
      if (!existsSync(cssPath)) {
        throw new Error(`CSSファイルが見つかりません: ${cssPath}`);
      }

      // 検証実行
      const result = await this.validator.validate(figmaJsonPath, cssPath, htmlPath);

      if (!result.success) {
        throw new Error(result.error);
      }

      // 結果をレポートファイルに保存
      const reportPath = join(dirname(cssPath), 'design-fidelity-report.json');
      writeFileSync(reportPath, JSON.stringify(result, null, 2));

      // 結果表示
      const summary = this.formatValidationSummary(result);

      return {
        content: [{
          type: "text",
          text: summary
        }],
        result: result
      };

    } catch (error) {
      throw new Error(`検証エラー: ${error.message}`);
    }
  }

  /**
   * 自動修正実行
   */
  async autoFixDesignIssues({ cssPath, suggestions, backupOriginal = true }) {
    try {
      // バックアップ作成
      if (backupOriginal) {
        const backupPath = cssPath + '.backup';
        const cssContent = readFileSync(cssPath, 'utf8');
        writeFileSync(backupPath, cssContent);
      }

      // 修正適用
      const result = await this.autoFixer.applyFixes(cssPath, suggestions);

      if (!result.success) {
        throw new Error(result.error);
      }

      const summary = `✅ 自動修正完了\\n\\n` +
        `📁 修正ファイル: ${basename(cssPath)}\\n` +
        `🔧 適用修正数: ${result.totalFixes}件\\n\\n` +
        `📋 適用した修正:\\n` +
        result.appliedFixes.map((fix, i) =>
          `${i + 1}. ${fix.type}: ${fix.element} → ${fix.property}: ${fix.value}`
        ).join('\\n');

      return {
        content: [{
          type: "text",
          text: summary
        }],
        result: result
      };

    } catch (error) {
      throw new Error(`自動修正エラー: ${error.message}`);
    }
  }

  /**
   * 完全ワークフロー実行
   */
  async completeDesignWorkflow({ figmaJsonPath, cssPath, htmlPath, targetScore = 95 }) {
    try {
      const workflow = [];
      let currentScore = 0;
      let iterations = 0;
      const maxIterations = 3;

      workflow.push(`🚀 完全ワークフロー開始`);
      workflow.push(`🎯 目標忠実度スコア: ${targetScore}%`);
      workflow.push('');

      while (currentScore < targetScore && iterations < maxIterations) {
        iterations++;
        workflow.push(`📋 第${iterations}回検証・修正サイクル`);
        workflow.push('─'.repeat(30));

        // 1. 検証実行
        const validationResult = await this.validator.validate(figmaJsonPath, cssPath, htmlPath);

        if (!validationResult.success) {
          throw new Error(validationResult.error);
        }

        currentScore = validationResult.fidelityScore;
        workflow.push(`📊 現在のスコア: ${currentScore}%`);
        workflow.push(`🎨 未実装色数: ${validationResult.missingColors?.length || 0}件`);
        workflow.push(`📝 修正提案数: ${validationResult.suggestions?.length || 0}件`);

        if (currentScore >= targetScore) {
          workflow.push(`✅ 目標スコア達成！`);
          break;
        }

        // 2. 自動修正実行
        if (validationResult.suggestions && validationResult.suggestions.length > 0) {
          workflow.push(`🔧 自動修正を実行中...`);

          const fixResult = await this.autoFixer.applyFixes(cssPath, validationResult.suggestions);

          if (fixResult.success) {
            workflow.push(`✅ ${fixResult.totalFixes}件の修正を適用`);
          } else {
            workflow.push(`❌ 修正エラー: ${fixResult.error}`);
          }
        } else {
          workflow.push(`ℹ️ 修正提案がありません`);
        }

        workflow.push('');
      }

      // 最終結果
      workflow.push('🏁 ワークフロー完了');
      workflow.push('─'.repeat(30));
      workflow.push(`🎯 最終スコア: ${currentScore}%`);
      workflow.push(`🔄 実行サイクル数: ${iterations}回`);

      if (currentScore >= targetScore) {
        workflow.push(`🎉 目標達成！品質保証完了`);
      } else {
        workflow.push(`⚠️ 目標未達成 (${maxIterations}回制限)`);
      }

      return {
        content: [{
          type: "text",
          text: workflow.join('\\n')
        }],
        finalScore: currentScore,
        targetReached: currentScore >= targetScore,
        iterations: iterations
      };

    } catch (error) {
      throw new Error(`ワークフローエラー: ${error.message}`);
    }
  }

  /**
   * 検証結果のサマリーフォーマット
   */
  formatValidationSummary(result) {
    return `🎯 設計忠実度検証レポート
${'='.repeat(40)}

📊 総合結果
   忠実度スコア: ${result.fidelityScore}% ${result.fidelityScore >= 95 ? '🎉' : result.fidelityScore >= 85 ? '✅' : '⚠️'}
   期待色数: ${result.summary?.totalColorsExpected || 0}
   発見色数: ${result.summary?.totalColorsFound || 0}
   未実装色数: ${result.summary?.missingColors || 0}

${result.missingColors && result.missingColors.length > 0 ? `
❌ 未実装の色 (${result.missingColors.length}件)
${result.missingColors.slice(0, 5).map(color =>
  `   🎨 ${color.rgba} (${color.hex}) - ${color.element}`
).join('\\n')}${result.missingColors.length > 5 ? `\\n   ... および ${result.missingColors.length - 5}件` : ''}
` : ''}

${result.suggestions && result.suggestions.length > 0 ? `
🔧 修正提案 (${result.suggestions.length}件)
${result.suggestions.slice(0, 3).map((s, i) =>
  `${i + 1}. ${s.description}`
).join('\\n')}${result.suggestions.length > 3 ? `\\n... および ${result.suggestions.length - 3}件` : ''}
` : ''}

💡 次のステップ:
${result.fidelityScore >= 95 ?
  '   🎉 設計忠実度が優秀です！' :
  '   🔧 auto_fix_design_issuesで自動修正を実行してください'
}`;
  }

  /**
   * サーバー開始
   */
  async run() {
    const transport = new StdioServerTransport();
    await this.server.connect(transport);
    console.error("🚀 MCP Design Validation Server が起動しました");
  }
}

// サーバー起動
if (import.meta.url === `file://${process.argv[1]}`) {
  const server = new DesignValidationServer();
  server.run().catch(console.error);
}