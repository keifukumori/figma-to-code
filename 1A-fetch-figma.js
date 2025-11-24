require('dotenv').config();
const https = require('https');
const fs = require('fs');
const path = require('path');

// 設定
const FIGMA_TOKEN = process.env.FIGMA_TOKEN || 'YOUR_FIGMA_TOKEN';
const OUTPUT_BASE = process.env.OUTPUT_DIR || './output';

function extractFileKeyAndNodeId(input) {
  const urlMatch = input.match(/figma\.com\/(?:file|design)\/([a-zA-Z0-9]+).*node-id=([0-9-]+)/);
  if (urlMatch) {
    return {
      fileKey: urlMatch[1],
      nodeId: urlMatch[2].replace('-', ':')
    };
  }
  
  const directMatch = input.match(/^([a-zA-Z0-9]+):([0-9:-]+)$/);
  if (directMatch) {
    return {
      fileKey: directMatch[1],
      nodeId: directMatch[2].replace('-', ':')
    };
  }
  
  console.error('Invalid input. Use Figma URL or FILE_KEY:NODE_ID format');
  process.exit(1);
}

function toDirectoryName(name) {
  return name
    .toLowerCase()
    .replace(/[\s_]+/g, '-')
    .replace(/[^\w\-]/g, '')
    .replace(/--+/g, '-')
    .replace(/^-|-$/g, '');
}

function fetchFigmaNode(fileKey, nodeId) {
  return new Promise((resolve, reject) => {
    const url = `/v1/files/${fileKey}/nodes?ids=${encodeURIComponent(nodeId)}`;
    const options = {
      hostname: 'api.figma.com',
      path: url,
      headers: { 'X-Figma-Token': FIGMA_TOKEN }
    };

    https.get(options, (res) => {
      let data = '';
      res.on('data', chunk => data += chunk);
      res.on('end', () => {
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
        resolve(JSON.parse(data));
      });
    }).on('error', reject);
  });
}

function fetchFigmaFile(fileKey) {
  return new Promise((resolve, reject) => {
    const url = `/v1/files/${fileKey}`;
    const options = {
      hostname: 'api.figma.com',
      path: url,
      headers: { 'X-Figma-Token': FIGMA_TOKEN }
    };
    
    https.get(options, (res) => {
      let data = '';
      res.on('data', chunk => data += chunk);
      res.on('end', () => {
        if (res.statusCode !== 200) {
          reject(new Error(`API Error: ${res.statusCode} - ${data}`));
          return;
        }
        resolve(JSON.parse(data));
      });
    }).on('error', reject);
  });
}

function fetchFigmaImage(fileKey, nodeId) {
  return new Promise((resolve, reject) => {
    const url = `/v1/images/${fileKey}?ids=${encodeURIComponent(nodeId)}&format=png&scale=2`;
    const options = {
      hostname: 'api.figma.com',
      path: url,
      headers: { 'X-Figma-Token': FIGMA_TOKEN }
    };
    
    https.get(options, (res) => {
      let data = '';
      res.on('data', chunk => data += chunk);
      res.on('end', () => {
        if (res.statusCode !== 200) {
          reject(new Error(`Image API Error: ${res.statusCode}`));
          return;
        }
        resolve(JSON.parse(data));
      });
    }).on('error', reject);
  });
}

function downloadImage(url, filepath) {
  return new Promise((resolve, reject) => {
    https.get(url, (res) => {
      if (res.statusCode === 302 || res.statusCode === 301) {
        downloadImage(res.headers.location, filepath).then(resolve).catch(reject);
        return;
      }
      const file = fs.createWriteStream(filepath);
      res.pipe(file);
      file.on('finish', () => {
        file.close();
        resolve(filepath);
      });
    }).on('error', reject);
  });
}

function findPageName(fileData, nodeId) {
  for (const page of fileData.document.children) {
    if (findNodeInTree(page, nodeId)) {
      return page.name;
    }
  }
  return 'unknown-page';
}

function findNodeInTree(node, targetId) {
  if (node.id === targetId) return true;
  if (node.children) {
    return node.children.some(child => findNodeInTree(child, targetId));
  }
  return false;
}

function mkdirSyncRecursive(dirPath) {
  if (!fs.existsSync(dirPath)) {
    fs.mkdirSync(dirPath, { recursive: true });
  }
}

// セクション管理ファイルの読み書き
function loadSectionsConfig(pageDir) {
  const configPath = path.join(pageDir, 'sections.json');
  if (fs.existsSync(configPath)) {
    return JSON.parse(fs.readFileSync(configPath, 'utf8'));
  }
  return { sections: [] };
}

function saveSectionsConfig(pageDir, config) {
  const configPath = path.join(pageDir, 'sections.json');
  fs.writeFileSync(configPath, JSON.stringify(config, null, 2));
}

async function main() {
  // コマンドライン引数または環境変数からURLを取得
  const input = process.argv[2] || process.env.FIGMA_URL;
  const pageName = process.argv[3];
  const deviceType = process.argv[4]; // desktop/mobile

  // レスポンシブ対応: DESKTOP/MOBILEが両方設定されている場合
  const desktopUrl = process.env.FIGMA_URL_DESKTOP;
  const mobileUrl = process.env.FIGMA_URL_MOBILE;

  if (desktopUrl && mobileUrl && !input) {
    console.log('🔄 レスポンシブ対応モード: デスクトップ・モバイル両方を処理します\n');

    // ページ名はオプション（未指定の場合は自動取得）
    if (!pageName) {
      console.log('ℹ️ ページ名が未指定のため、Figmaから自動取得します...\n');
    }

    // デスクトップ版処理
    console.log('📱 1/2: デスクトップ版を処理...');
    await processVersion(desktopUrl, pageName, 'desktop');

    // モバイル版処理
    console.log('\n📱 2/2: モバイル版を処理...');
    await processVersion(mobileUrl, pageName, 'mobile');

    console.log('\n✅ レスポンシブ対応完了！');
    console.log('🚀 Next: Claude Code でレスポンシブHTML/CSS生成');
    console.log(`   cd output/${toDirectoryName(pageName)}`);
    console.log(`   claude → PROMPT-COMPLETE.md の内容を実行`);
    return;
  }

  // 従来の単一URL処理
  if (!input) {
    console.log('Usage: node fetch-figma.js [FIGMA_URL] [PAGE_NAME] [DEVICE_TYPE]');
    console.log('');
    console.log('URLは以下の方法で指定できます:');
    console.log('  1. 単一URL: node fetch-figma.js "URL" page_name');
    console.log('  2. .envファイル: FIGMA_URL="URL" を設定');
    console.log('  3. レスポンシブ: .envにFIGMA_URL_DESKTOP, FIGMA_URL_MOBILEを設定');
    console.log('');
    console.log('Examples:');
    console.log('  node fetch-figma.js "https://figma.com/...?node-id=1-100" templates');
    console.log('  node fetch-figma.js "URL" templates desktop  # desktop/に保存');
    console.log('  node fetch-figma.js "URL" templates mobile   # mobile/に保存');
    process.exit(1);
  }

  // 単一版処理
  await processVersion(input, pageName, deviceType);
}

async function processVersion(input, pageName, deviceType) {
  const { fileKey, nodeId } = extractFileKeyAndNodeId(input);
  console.log(`Fetching: fileKey=${fileKey}, nodeId=${nodeId}, device=${deviceType || 'default'}`);

  // ノードデータ取得
  const nodeData = await fetchFigmaNode(fileKey, nodeId);
  const node = nodeData.nodes[nodeId].document;
  const sectionName = node.name;

  // ページ名取得
  let resolvedPageName = pageName;
  if (!resolvedPageName) {
    console.log('Fetching file structure for page name...');
    const fileData = await fetchFigmaFile(fileKey);
    resolvedPageName = findPageName(fileData, nodeId);
  }

  // ディレクトリ構造
  const pageDirName = toDirectoryName(resolvedPageName);
  const sectionDirName = toDirectoryName(sectionName);
  const pageDir = path.join(OUTPUT_BASE, pageDirName);

  // デバイス種別に応じたディレクトリ構造
  let sectionDir;
  if (deviceType === 'desktop' || deviceType === 'mobile') {
    sectionDir = path.join(pageDir, 'sections', sectionDirName, deviceType);
  } else {
    sectionDir = path.join(pageDir, 'sections', sectionDirName);
  }

  mkdirSyncRecursive(pageDir);
  mkdirSyncRecursive(sectionDir);

  console.log(`Page: ${resolvedPageName} -> ${pageDirName}`);
  console.log(`Section: ${sectionName} -> ${sectionDirName}${deviceType ? '/' + deviceType : ''}`);

  // JSON保存
  const jsonPath = path.join(sectionDir, 'figma-data.json');
  fs.writeFileSync(jsonPath, JSON.stringify(nodeData, null, 2));
  console.log(`Saved: ${jsonPath}`);

  // 画像取得
  const imageData = await fetchFigmaImage(fileKey, nodeId);
  const imageUrl = imageData.images[nodeId];
  if (imageUrl) {
    const imagePath = path.join(sectionDir, 'figma-capture.png');
    await downloadImage(imageUrl, imagePath);
    console.log(`Saved: ${imagePath}`);
  }

  // セクション管理に追加（レスポンシブ対応）
  const config = loadSectionsConfig(pageDir);
  const existingIndex = config.sections.findIndex(s => s.name === sectionDirName);

  const sectionInfo = {
    name: sectionDirName,
    originalName: sectionName,
    nodeId: nodeId,
    path: `sections/${sectionDirName}`,
    addedAt: new Date().toISOString()
  };

  // レスポンシブ対応の場合、devices情報を追加
  if (deviceType === 'desktop' || deviceType === 'mobile') {
    if (existingIndex >= 0) {
      // 既存セクションにデバイス情報を追加
      if (!config.sections[existingIndex].devices) {
        config.sections[existingIndex].devices = {};
      }
      config.sections[existingIndex].devices[deviceType] = {
        nodeId: nodeId,
        dataFile: `${deviceType}/figma-data.json`,
        captureFile: `${deviceType}/figma-capture.png`
      };
    } else {
      // 新規セクションとして追加
      sectionInfo.devices = {
        [deviceType]: {
          nodeId: nodeId,
          dataFile: `${deviceType}/figma-data.json`,
          captureFile: `${deviceType}/figma-capture.png`
        }
      };
      config.sections.push(sectionInfo);
    }
  } else {
    // 従来の単一デバイス処理
    if (existingIndex >= 0) {
      config.sections[existingIndex] = sectionInfo;
      console.log(`⚡ Updated existing section: ${sectionDirName}`);
    } else {
      config.sections.push(sectionInfo);
      console.log(`✅ Added new section: ${sectionDirName}`);
    }
  }

  saveSectionsConfig(pageDir, config);

  // 状態表示（レスポンシブ対応時は簡略化）
  if (!deviceType || (!process.env.FIGMA_URL_DESKTOP && !process.env.FIGMA_URL_MOBILE)) {
    console.log(`\n📁 Page: ${pageDir}`);
    console.log(`   Sections (${config.sections.length}):`);
    config.sections.forEach((s, i) => {
      console.log(`     ${i + 1}. ${s.originalName}`);
    });

    console.log(`\n🚀 Next: Run Claude Code to generate/update HTML`);
    console.log(`   cd ${pageDir}`);
    console.log(`   claude`);
    console.log(`   → PROMPT.md の内容を実行`);
  }
}

main().catch(console.error);
