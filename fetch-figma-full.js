require('dotenv').config();
const https = require('https');
const fs = require('fs');
const path = require('path');

// 設定
const FIGMA_TOKEN = process.env.FIGMA_TOKEN || 'YOUR_FIGMA_TOKEN';
const OUTPUT_BASE = process.env.OUTPUT_DIR || './output';
const CACHE_DIR = path.join(OUTPUT_BASE, 'cache');

function extractFileKeyFromUrl(url) {
  const urlMatch = url.match(/figma\.com\/(?:file|design)\/([a-zA-Z0-9]+)/);
  if (urlMatch) {
    return urlMatch[1];
  }

  console.error('Invalid Figma URL. Expected format: https://figma.com/design/FILE_KEY...');
  process.exit(1);
}

function fetchFigmaFile(fileKey) {
  return new Promise((resolve, reject) => {
    const url = `/v1/files/${fileKey}`;
    const options = {
      hostname: 'api.figma.com',
      path: url,
      headers: { 'X-Figma-Token': FIGMA_TOKEN }
    };

    console.log(`Fetching full Figma file: ${fileKey}`);
    console.log(`⚠️ This may take 30-60 seconds for large files...`);

    https.get(options, (res) => {
      let data = '';
      res.on('data', chunk => {
        data += chunk;
        // プログレス表示（簡易版）
        if (data.length % (1024 * 1024) === 0) {
          process.stdout.write('.');
        }
      });

      res.on('end', () => {
        console.log(); // 改行

        if (res.statusCode === 429) {
          const retryAfter = res.headers['retry-after'] || '60';
          const upgradeLink = res.headers['x-figma-upgrade-link'];
          console.error(`\n⚠️ API制限に達しました (429)`);
          console.error(`   待機時間: ${retryAfter}秒`);
          console.error(`   時刻: ${new Date().toLocaleTimeString()}`);
          if (upgradeLink) {
            console.error(`   アップグレード: ${upgradeLink}`);
          }
          console.error(`   ヒント: 無料プランの場合、1日の制限に達している可能性があります`);
          reject(new Error(`API Error: ${res.statusCode} - ${data}`));
          return;
        }

        if (res.statusCode !== 200) {
          reject(new Error(`API Error: ${res.statusCode} - ${data}`));
          return;
        }

        try {
          const jsonData = JSON.parse(data);
          console.log(`✅ ファイル取得完了: ${Math.round(data.length / 1024 / 1024)}MB`);
          resolve(jsonData);
        } catch (error) {
          reject(new Error(`JSON Parse Error: ${error.message}`));
        }
      });
    }).on('error', reject);
  });
}

function mkdirSyncRecursive(dirPath) {
  if (!fs.existsSync(dirPath)) {
    fs.mkdirSync(dirPath, { recursive: true });
  }
}

function saveFullData(fileKey, data, deviceType = '') {
  const timestamp = new Date().toISOString().replace(/[:.]/g, '-');
  const suffix = deviceType ? `-${deviceType}` : '';
  const filename = `${fileKey}${suffix}-full-${timestamp}.json`;
  const filepath = path.join(CACHE_DIR, filename);

  mkdirSyncRecursive(CACHE_DIR);

  fs.writeFileSync(filepath, JSON.stringify(data, null, 2));
  console.log(`💾 保存完了: ${filepath}`);

  // 最新データへのシンボリックリンク作成
  const latestFilename = `${fileKey}${suffix}-full-latest.json`;
  const latestPath = path.join(CACHE_DIR, latestFilename);

  // 既存のシンボリックリンクを削除
  if (fs.existsSync(latestPath)) {
    fs.unlinkSync(latestPath);
  }

  // 新しいシンボリックリンクを作成
  try {
    fs.symlinkSync(path.basename(filepath), latestPath);
    console.log(`🔗 最新データリンク: ${latestPath}`);
  } catch (error) {
    // Windows等でシンボリックリンクが作成できない場合はコピー
    fs.copyFileSync(filepath, latestPath);
    console.log(`📁 最新データコピー: ${latestPath}`);
  }

  return { filepath, latestPath };
}

function getFileInfo(data) {
  const totalNodes = countNodes(data.document);
  const pages = data.document.children.map(page => ({
    name: page.name,
    id: page.id,
    children: page.children ? page.children.length : 0
  }));

  return { totalNodes, pages };
}

function countNodes(node) {
  let count = 1; // 自分自身
  if (node.children) {
    for (const child of node.children) {
      count += countNodes(child);
    }
  }
  return count;
}

async function main() {
  // コマンドライン引数または環境変数からURLを取得
  const desktopUrl = process.argv[2] || process.env.FIGMA_URL_DESKTOP;
  const mobileUrl = process.argv[3] || process.env.FIGMA_URL_MOBILE;

  if (!desktopUrl) {
    console.log('Usage: node fetch-figma-full.js <DESKTOP_URL> [MOBILE_URL]');
    console.log('');
    console.log('URLは以下の方法で指定できます:');
    console.log('  1. 引数: node fetch-figma-full.js "https://figma.com/design/..."');
    console.log('  2. 環境変数: .envにFIGMA_URL_DESKTOPを設定');
    console.log('');
    console.log('Examples:');
    console.log('  node fetch-figma-full.js "https://figma.com/design/ABC123..."');
    console.log('  node fetch-figma-full.js "desktop-url" "mobile-url"');
    process.exit(1);
  }

  console.log('🚀 Figma Full File Fetcher');
  console.log('================================');

  try {
    // デスクトップファイル取得
    console.log('\n📱 1. デスクトップ版ファイル取得...');
    const desktopFileKey = extractFileKeyFromUrl(desktopUrl);
    const desktopData = await fetchFigmaFile(desktopFileKey);
    const desktopInfo = getFileInfo(desktopData);
    const desktopFiles = saveFullData(desktopFileKey, desktopData, 'desktop');

    console.log(`   📊 総ノード数: ${desktopInfo.totalNodes.toLocaleString()}`);
    console.log(`   📄 ページ数: ${desktopInfo.pages.length}`);
    desktopInfo.pages.forEach((page, i) => {
      console.log(`     ${i + 1}. ${page.name} (${page.children} children)`);
    });

    // モバイルファイル取得（オプション）
    let mobileFiles = null;
    if (mobileUrl) {
      console.log('\n📱 2. モバイル版ファイル取得...');
      const mobileFileKey = extractFileKeyFromUrl(mobileUrl);

      // 同じファイルの場合は重複取得を避ける
      if (mobileFileKey === desktopFileKey) {
        console.log('   ℹ️ デスクトップと同じファイルです。データを共有します。');
        mobileFiles = saveFullData(mobileFileKey, desktopData, 'mobile');
      } else {
        const mobileData = await fetchFigmaFile(mobileFileKey);
        const mobileInfo = getFileInfo(mobileData);
        mobileFiles = saveFullData(mobileFileKey, mobileData, 'mobile');

        console.log(`   📊 総ノード数: ${mobileInfo.totalNodes.toLocaleString()}`);
        console.log(`   📄 ページ数: ${mobileInfo.pages.length}`);
      }
    }

    // 完了報告
    console.log('\n✅ ファイル全体の取得完了！');
    console.log('================================');
    console.log('📁 保存されたファイル:');
    console.log(`   Desktop: ${desktopFiles.latestPath}`);
    if (mobileFiles) {
      console.log(`   Mobile:  ${mobileFiles.latestPath}`);
    }

    console.log('\n🚀 Next: セクション抽出');
    console.log('   node extract-section.js --desktop-url="..." --section-name="..."');
    if (mobileFiles) {
      console.log('   または: node extract-section.js --desktop-url="..." --mobile-url="..." --section-name="..."');
    }

  } catch (error) {
    console.error('\n❌ エラーが発生しました:');
    console.error(`   ${error.message}`);

    if (error.message.includes('429')) {
      console.log('\n💡 解決策:');
      console.log('   - 翌日まで待機');
      console.log('   - Figma有料プランへのアップグレード');
      console.log('   - 別のFigmaアカウントの使用');
    }

    process.exit(1);
  }
}

main().catch(console.error);