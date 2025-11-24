require('dotenv').config();
const fs = require('fs');
const path = require('path');

// 既存のfetch-figma.js機能をインポート
const { processVersion, toDirectoryName, mkdirSyncRecursive, loadSectionsConfig, saveSectionsConfig } = require('./fetch-figma-core');

/**
 * CSVファイルを読み込んでURLペアのリストを返す
 * CSV形式: page_name,desktop_url,mobile_url
 */
function parseCSV(csvPath) {
  if (!fs.existsSync(csvPath)) {
    throw new Error(`CSV file not found: ${csvPath}`);
  }

  const csvContent = fs.readFileSync(csvPath, 'utf8');
  const lines = csvContent.trim().split('\n');

  // ヘッダー行をスキップ
  const header = lines[0].split(',');
  const urlPairs = [];

  for (let i = 1; i < lines.length; i++) {
    const columns = lines[i].split(',');

    if (columns.length >= 3) {
      urlPairs.push({
        pageName: columns[0].trim(),
        desktopUrl: columns[1].trim(),
        mobileUrl: columns[2].trim()
      });
    }
  }

  return urlPairs;
}

/**
 * 1つのURLペアを処理（デスクトップ + モバイル）
 */
async function processPair(pair, index, total) {
  console.log(`\n🔄 [${index + 1}/${total}] Processing: ${pair.pageName}`);
  console.log(`   Desktop: ${pair.desktopUrl}`);
  console.log(`   Mobile:  ${pair.mobileUrl}`);

  try {
    // デスクトップ版処理
    console.log(`\n📱 [${index + 1}/${total}] 1/2: デスクトップ版処理...`);
    await processVersionFromModule(pair.desktopUrl, pair.pageName, 'desktop');

    // 少し待機（API制限対策）
    await sleep(2000);

    // モバイル版処理
    console.log(`\n📱 [${index + 1}/${total}] 2/2: モバイル版処理...`);
    await processVersionFromModule(pair.mobileUrl, pair.pageName, 'mobile');

    console.log(`✅ [${index + 1}/${total}] 完了: ${pair.pageName}`);

    // ペア間の待機（API制限対策）
    if (index < total - 1) {
      console.log('⏳ API制限対策で3秒待機...');
      await sleep(3000);
    }

  } catch (error) {
    console.error(`❌ [${index + 1}/${total}] エラー: ${pair.pageName}`);
    console.error(`   ${error.message}`);

    if (error.message.includes('429') || error.message.includes('Rate limit')) {
      console.log('⚠️ API制限に達しました。60秒待機してから再試行...');
      await sleep(60000);

      // 再試行
      console.log(`🔄 [${index + 1}/${total}] 再試行: ${pair.pageName}`);
      await processPair(pair, index, total);
    } else {
      throw error; // 他のエラーは再スロー
    }
  }
}

/**
 * sleep関数
 */
function sleep(ms) {
  return new Promise(resolve => setTimeout(resolve, ms));
}

/**
 * processVersion関数のラッパー（モジュール化対応）
 */
async function processVersionFromModule(url, pageName, deviceType) {
  // 既存のprocessVersion関数を呼び出し
  // ここでは簡略化のため、直接実装

  // TODO: fetch-figma.jsのprocessVersion関数を分離してインポート
  // 現在は fetch-figma.js を直接実行する方式で代替

  const { exec } = require('child_process');
  const util = require('util');
  const execPromise = util.promisify(exec);

  try {
    const command = `node fetch-figma.js "${url}" "${pageName}" "${deviceType}"`;
    const { stdout, stderr } = await execPromise(command);

    if (stderr) {
      console.error('Warning:', stderr);
    }

    console.log(stdout);
  } catch (error) {
    throw new Error(error.message);
  }
}

/**
 * メイン処理
 */
async function main() {
  const csvPath = process.argv[2] || './urls.csv';

  console.log('🚀 Figma Batch Processor');
  console.log(`📄 CSV file: ${csvPath}\n`);

  try {
    // CSVパース
    const urlPairs = parseCSV(csvPath);

    if (urlPairs.length === 0) {
      console.log('❌ CSVファイルにデータが見つかりません');
      process.exit(1);
    }

    console.log(`📊 処理対象: ${urlPairs.length} ペア`);
    urlPairs.forEach((pair, i) => {
      console.log(`   ${i + 1}. ${pair.pageName}`);
    });

    console.log('\n⏳ 処理開始...');

    // 順次処理
    for (let i = 0; i < urlPairs.length; i++) {
      await processPair(urlPairs[i], i, urlPairs.length);
    }

    console.log('\n🎉 全ての処理が完了しました！');

    // 結果サマリー
    console.log('\n📁 生成されたページ:');
    urlPairs.forEach((pair, i) => {
      const pageDir = toDirectoryName(pair.pageName);
      console.log(`   ${i + 1}. output/${pageDir}/`);
      console.log(`      → PROMPT-COMPLETE.md でHTML/CSS生成可能`);
    });

  } catch (error) {
    console.error('❌ バッチ処理エラー:', error.message);
    process.exit(1);
  }
}

// 実行
if (require.main === module) {
  main().catch(console.error);
}

module.exports = { parseCSV, processPair };