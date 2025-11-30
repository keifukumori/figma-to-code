#!/usr/bin/env node

import { DesignFidelityValidator } from './mcp-design-validator/src/design-validator.js';
import { AutoFixer } from './mcp-design-validator/src/auto-fixer.js';
import { readFileSync, writeFileSync, existsSync } from 'fs';
import { basename, dirname, join } from 'path';

/**
 * 完全ワークフロー: 設計検証 → 自動修正 → 再検証
 * IMPROVED-WORKFLOW.mdに統合するスクリプト
 */
class CompleteDesignWorkflow {
  constructor() {
    this.validator = new DesignFidelityValidator();
    this.autoFixer = new AutoFixer();
  }

  /**
   * 完全ワークフロー実行
   */
  async run({ figmaJsonPath, cssPath, htmlPath, targetScore = 95 }) {
    try {
      console.log('🚀 完全ワークフロー開始');
      console.log(`🎯 目標忠実度スコア: ${targetScore}%`);
      console.log('');

      let currentScore = 0;
      let iterations = 0;
      const maxIterations = 3;

      while (currentScore < targetScore && iterations < maxIterations) {
        iterations++;
        console.log(`📋 第${iterations}回検証・修正サイクル`);
        console.log('─'.repeat(30));

        // 1. 検証実行
        console.log('🔍 設計忠実度を検証中...');
        const validationResult = await this.validator.validate(figmaJsonPath, cssPath, htmlPath);

        if (!validationResult.success) {
          throw new Error(validationResult.error);
        }

        currentScore = validationResult.fidelityScore;
        console.log(`📊 現在のスコア: ${currentScore}%`);
        console.log(`🎨 未実装色数: ${validationResult.missingColors?.length || 0}件`);
        console.log(`📝 修正提案数: ${validationResult.suggestions?.length || 0}件`);

        // 詳細レポート保存
        const reportPath = join(dirname(cssPath), 'design-fidelity-report.json');
        writeFileSync(reportPath, JSON.stringify(validationResult, null, 2));
        console.log(`📄 詳細レポートを保存: ${reportPath}`);

        if (currentScore >= targetScore) {
          console.log(`✅ 目標スコア達成！`);
          break;
        }

        // 2. 自動修正実行
        if (validationResult.suggestions && validationResult.suggestions.length > 0) {
          console.log(`🔧 自動修正を実行中...`);

          // バックアップ作成
          const backupPath = cssPath + '.backup';
          const cssContent = readFileSync(cssPath, 'utf8');
          writeFileSync(backupPath, cssContent);
          console.log(`💾 バックアップ作成: ${basename(backupPath)}`);

          const fixResult = await this.autoFixer.applyFixes(cssPath, validationResult.suggestions);

          if (fixResult.success) {
            console.log(`✅ ${fixResult.totalFixes}件の修正を適用`);
            fixResult.appliedFixes.forEach((fix, i) => {
              console.log(`   ${i + 1}. ${fix.type}: ${fix.element} → ${fix.property}: ${fix.value}`);
            });
          } else {
            console.log(`❌ 修正エラー: ${fixResult.error}`);
          }
        } else {
          console.log(`ℹ️ 修正提案がありません`);
        }

        console.log('');
      }

      // 最終結果
      console.log('🏁 ワークフロー完了');
      console.log('─'.repeat(30));
      console.log(`🎯 最終スコア: ${currentScore}%`);
      console.log(`🔄 実行サイクル数: ${iterations}回`);

      if (currentScore >= targetScore) {
        console.log(`🎉 目標達成！品質保証完了`);
        return { success: true, finalScore: currentScore, targetReached: true };
      } else {
        console.log(`⚠️ 目標未達成 (${maxIterations}回制限)`);
        return { success: true, finalScore: currentScore, targetReached: false };
      }

    } catch (error) {
      console.error(`❌ ワークフローエラー: ${error.message}`);
      return { success: false, error: error.message };
    }
  }
}

// スクリプト実行
if (import.meta.url === `file://${process.argv[1]}`) {
  const args = process.argv.slice(2);

  if (args.length < 2) {
    console.error('使用法: node complete-workflow.js <figmaJsonPath> <cssPath> [htmlPath] [targetScore]');
    console.error('');
    console.error('例:');
    console.error('  node complete-workflow.js output/templates/sections/cart/figma-data-simplified.json output/templates/sections/cart/cart.css');
    console.error('  node complete-workflow.js output/templates/sections/home/figma-data-simplified.json output/templates/sections/home/style.css output/templates/sections/home/index.html 98');
    process.exit(1);
  }

  const [figmaJsonPath, cssPath, htmlPath, targetScore] = args;

  if (!existsSync(figmaJsonPath)) {
    console.error(`❌ Figma JSONファイルが見つかりません: ${figmaJsonPath}`);
    process.exit(1);
  }

  if (!existsSync(cssPath)) {
    console.error(`❌ CSSファイルが見つかりません: ${cssPath}`);
    process.exit(1);
  }

  const workflow = new CompleteDesignWorkflow();

  workflow.run({
    figmaJsonPath,
    cssPath,
    htmlPath: htmlPath && existsSync(htmlPath) ? htmlPath : null,
    targetScore: targetScore ? parseInt(targetScore) : 95
  }).then(result => {
    if (result.success && result.targetReached) {
      console.log('\n🎊 ワークフロー成功！100%の設計忠実度を達成しました。');
      process.exit(0);
    } else if (result.success) {
      console.log('\n⚠️ ワークフローは完了しましたが、目標スコアに達しませんでした。');
      process.exit(1);
    } else {
      console.log('\n💥 ワークフロー実行中にエラーが発生しました。');
      process.exit(1);
    }
  }).catch(error => {
    console.error(`💥 実行エラー: ${error.message}`);
    process.exit(1);
  });
}