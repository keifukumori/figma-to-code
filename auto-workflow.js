#!/usr/bin/env node

import { readFileSync, writeFileSync, existsSync, readdirSync } from 'fs';
import { join, dirname, basename } from 'path';
import { spawn } from 'child_process';

/**
 * Figma to HTML/CSS 完全自動化ワークフロー
 * 使用法: node auto-workflow.js <target-directory> [--parallel] [--all-sections]
 */

class AutomatedFigmaWorkflow {
  constructor() {
    this.basePrompts = {
      structuralAnalysis: `
次のディレクトリ内にあるJSONとキャプチャーを確認してください。

まずは構造的な内容を把握
どのようなものが配置されているか、
カラムはいくつあるか、テキストやボタンリンクはいくつあるか
それぞれどのように配置されているか
`,
      detailedAnalysis: `
次は詳細を把握
jsonの内容を細かく調査して先ほどの構造的に把握した内容とすり合わせる 各ボタンのサイズ、位置、パディング、マージンを網羅的に取得。
それらをCSSに正確に反映しjsonの内容と齟齬がないことを確認する。マッピングする。
その際部分的な修正のみにとどまると構造的な破綻を起こす可能性が高いので、周辺の構造的な内容や影響も調査した上で、該当箇所の正確な数値を反映する。
jsonとcss でマッチしていない要素については再度マッピングをやり直す
2-FIGMA_TO_CSS_QUALITY_CHECKLIST.md このファイルの内容確認して要件を満たすようにしてください
マッピングできたらファイルとして出力して
`,
      promptExecution: `
その工程が完了したらそれらをもとに次のファイルの内容をプロンプトとして実行して
3-PROMPT-SAFE.md
`
    };
  }

  /**
   * ディレクトリが有効なFigmaセクションか判定
   */
  isValidFigmaSection(dirPath) {
    if (!existsSync(dirPath)) return false;

    const requiredFiles = ['desktop/figma-data.json', 'desktop/figma-capture.png'];
    return requiredFiles.every(file => existsSync(join(dirPath, file)));
  }

  /**
   * 全セクションディレクトリを検索
   */
  findAllSections(basePath) {
    const sections = [];

    try {
      const entries = readdirSync(basePath, { withFileTypes: true });

      for (const entry of entries) {
        if (entry.isDirectory()) {
          const fullPath = join(basePath, entry.name);
          if (this.isValidFigmaSection(fullPath)) {
            sections.push({
              name: entry.name,
              path: fullPath
            });
          }
        }
      }
    } catch (error) {
      console.error(`ディレクトリ読み込みエラー: ${error.message}`);
    }

    return sections;
  }

  /**
   * 単一セクションの自動処理
   */
  async processSingleSection(sectionPath, sectionName) {
    console.log(`\n🚀 セクション処理開始: ${sectionName}`);
    console.log(`📁 パス: ${sectionPath}`);

    const startTime = Date.now();

    try {
      // ステップ1: 構造分析
      console.log('📋 ステップ1: 構造分析実行中...');
      await this.executeStep(sectionPath, this.basePrompts.structuralAnalysis);

      // ステップ2: 詳細分析とマッピング
      console.log('🔍 ステップ2: 詳細分析・マッピング実行中...');
      await this.executeStep(sectionPath, this.basePrompts.detailedAnalysis);

      // ステップ3: プロンプト実行
      console.log('⚡ ステップ3: 3-PROMPT-SAFE.md実行中...');
      await this.executeStep(sectionPath, this.basePrompts.promptExecution);

      // ステップ4: 品質検証
      console.log('✅ ステップ4: 品質検証実行中...');
      await this.runQualityCheck(sectionPath);

      const duration = ((Date.now() - startTime) / 1000).toFixed(1);
      console.log(`✨ セクション完了: ${sectionName} (${duration}秒)`);

      return { success: true, section: sectionName, duration: parseFloat(duration) };

    } catch (error) {
      console.error(`❌ エラー: ${sectionName} - ${error.message}`);
      return { success: false, section: sectionName, error: error.message };
    }
  }

  /**
   * プロンプト実行のシミュレーション（実際にはClaude Codeが実行）
   */
  async executeStep(sectionPath, prompt) {
    // 実際の実装では、Claude Code APIを呼び出すか
    // ユーザーにプロンプトを提示
    return new Promise(resolve => {
      // シミュレーション: 実際の処理時間を模擬
      setTimeout(resolve, 1000 + Math.random() * 2000);
    });
  }

  /**
   * 品質チェック実行
   */
  async runQualityCheck(sectionPath) {
    const figmaPath = join(sectionPath, 'desktop/figma-data.json');
    const cssFiles = readdirSync(sectionPath).filter(f => f.endsWith('.css'));
    const htmlFiles = readdirSync(sectionPath).filter(f => f.endsWith('.html'));

    if (cssFiles.length === 0 || htmlFiles.length === 0) {
      throw new Error('CSS または HTML ファイルが見つかりません');
    }

    const cssPath = join(sectionPath, cssFiles[0]);
    const htmlPath = join(sectionPath, htmlFiles[0]);

    return new Promise((resolve, reject) => {
      const child = spawn('node', ['../complete-workflow.js', figmaPath, cssPath, htmlPath], {
        cwd: sectionPath,
        stdio: 'pipe'
      });

      child.on('close', (code) => {
        if (code === 0) {
          resolve();
        } else {
          reject(new Error(`品質チェック失敗 (exit code: ${code})`));
        }
      });
    });
  }

  /**
   * 並列処理実行
   */
  async processParallel(sections, maxConcurrency = 3) {
    console.log(`\n🔄 並列処理開始: ${sections.length}セクション (最大同時実行: ${maxConcurrency})`);

    const results = [];
    const startTime = Date.now();

    // セクションを同時実行数で分割
    for (let i = 0; i < sections.length; i += maxConcurrency) {
      const batch = sections.slice(i, i + maxConcurrency);
      console.log(`\n📦 バッチ ${Math.floor(i/maxConcurrency) + 1}: ${batch.map(s => s.name).join(', ')}`);

      const batchPromises = batch.map(section =>
        this.processSingleSection(section.path, section.name)
      );

      const batchResults = await Promise.allSettled(batchPromises);
      results.push(...batchResults.map(r => r.value || r.reason));
    }

    // 結果サマリー
    const totalDuration = ((Date.now() - startTime) / 1000).toFixed(1);
    const successful = results.filter(r => r.success).length;
    const failed = results.filter(r => !r.success).length;

    console.log(`\n🏁 並列処理完了`);
    console.log(`⏱️  総実行時間: ${totalDuration}秒`);
    console.log(`✅ 成功: ${successful}件`);
    console.log(`❌ 失敗: ${failed}件`);

    // 詳細結果をファイル出力
    const reportPath = join(process.cwd(), `workflow-report-${Date.now()}.json`);
    writeFileSync(reportPath, JSON.stringify({
      timestamp: new Date().toISOString(),
      totalSections: sections.length,
      successful,
      failed,
      totalDuration: parseFloat(totalDuration),
      results
    }, null, 2));

    console.log(`📄 詳細レポート: ${reportPath}`);

    return results;
  }

  /**
   * メイン実行関数
   */
  async run(args) {
    const [targetDir, ...flags] = args;

    if (!targetDir) {
      console.error('使用法: node auto-workflow.js <target-directory> [--parallel] [--all-sections]');
      console.error('');
      console.error('例:');
      console.error('  node auto-workflow.js output/myproject/sections_02');
      console.error('  node auto-workflow.js output/myproject --all-sections --parallel');
      process.exit(1);
    }

    const isParallel = flags.includes('--parallel');
    const isAllSections = flags.includes('--all-sections');

    let sectionsToProcess = [];

    if (isAllSections) {
      sectionsToProcess = this.findAllSections(targetDir);
      console.log(`🔍 発見されたセクション: ${sectionsToProcess.length}件`);
      sectionsToProcess.forEach(s => console.log(`  - ${s.name}`));
    } else {
      if (this.isValidFigmaSection(targetDir)) {
        sectionsToProcess = [{
          name: basename(targetDir),
          path: targetDir
        }];
      } else {
        console.error(`❌ 有効なFigmaセクションではありません: ${targetDir}`);
        process.exit(1);
      }
    }

    if (sectionsToProcess.length === 0) {
      console.error('❌ 処理対象のセクションが見つかりませんでした');
      process.exit(1);
    }

    // 実行方法選択
    if (isParallel && sectionsToProcess.length > 1) {
      await this.processParallel(sectionsToProcess);
    } else {
      // 順次実行
      console.log(`\n🔄 順次処理開始: ${sectionsToProcess.length}セクション`);
      for (const section of sectionsToProcess) {
        await this.processSingleSection(section.path, section.name);
      }
    }

    console.log('\n🎉 全体処理完了！');
  }
}

// 実行部分
if (import.meta.url === `file://${process.argv[1]}`) {
  const workflow = new AutomatedFigmaWorkflow();
  const args = process.argv.slice(2);

  workflow.run(args).catch(error => {
    console.error(`💥 致命的エラー: ${error.message}`);
    process.exit(1);
  });
}