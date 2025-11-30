const fs = require('fs');
const path = require('path');

// セクション対応マッピング（順序とパターンベース）
const SECTION_MAPPING = [
  {
    name: 'hero',
    displayName: 'ヒーロー（社長写真＋メッセージ）',
    desktop: { pattern: 'set', index: 0 },
    mobile: { pattern: 'set', index: 0 }
  },
  {
    name: 'three-images',
    displayName: '3つの画像グリッド',
    desktop: { pattern: 'set', index: 1 },
    mobile: { pattern: 'set', index: 1 }
  },
  {
    name: 'materiality-intro',
    displayName: 'マテリアリティ説明（左右レイアウト）',
    desktop: { pattern: 'set', index: 2 },
    mobile: { pattern: 'set', index: 2 }
  },
  {
    name: 'materiality-list',
    displayName: 'マテリアリティ項目リスト',
    desktop: { pattern: 'set', index: 3 },
    mobile: { pattern: 'set', index: 3 }
  },
  {
    name: 'activity-images',
    displayName: '活動画像（3つ）',
    desktop: { pattern: 'contents-card-framed-h', index: 0 },
    mobile: { pattern: 'contents-card-framed-h', index: 0 }
  },
  {
    name: 'team-intro',
    displayName: 'チーム紹介（左右レイアウト）',
    desktop: { pattern: 'set', index: 4 },
    mobile: { pattern: 'set', index: 4 }
  },
  {
    name: 'wellbeing-section',
    displayName: 'Well-being FIRSTセクション',
    desktop: { pattern: 'Section - Well-Being Story', index: 0 },
    mobile: { pattern: 'Section - Well-Being Story', index: 0 }
  },
  {
    name: 'bottom-images',
    displayName: '最下部画像',
    desktop: { pattern: 'set', index: 5 },
    mobile: { pattern: 'set 3連', index: 0 }
  }
];

function findSectionByPattern(sections, pattern, index) {
  const matches = sections.filter(section => {
    if (pattern.includes('set') && pattern !== 'set') {
      return section.name.startsWith(pattern);
    } else if (pattern === 'set') {
      return section.name === 'set';
    } else {
      return section.name.includes(pattern);
    }
  });

  return matches[index] || null;
}

function extractSectionData(fullJson, sectionNode, deviceType) {
  // セクション専用のJSONデータを作成
  const sectionData = {
    document: {
      id: sectionNode.id,
      name: sectionNode.name,
      type: sectionNode.type,
      absoluteBoundingBox: sectionNode.absoluteBoundingBox,
      children: sectionNode.children || [],
      // 元のメタデータを保持
      fills: sectionNode.fills,
      effects: sectionNode.effects,
      layoutMode: sectionNode.layoutMode,
      primaryAxisSizingMode: sectionNode.primaryAxisSizingMode,
      counterAxisSizingMode: sectionNode.counterAxisSizingMode,
      primaryAxisAlignItems: sectionNode.primaryAxisAlignItems,
      counterAxisAlignItems: sectionNode.counterAxisAlignItems,
      paddingLeft: sectionNode.paddingLeft,
      paddingRight: sectionNode.paddingRight,
      paddingTop: sectionNode.paddingTop,
      paddingBottom: sectionNode.paddingBottom,
      itemSpacing: sectionNode.itemSpacing
    },
    device: deviceType,
    extractedAt: new Date().toISOString()
  };

  // 深い階層の要素も含めて収集する関数
  function collectAllNodes(node, collected = {}) {
    collected[node.id] = node;

    if (node.children) {
      node.children.forEach(child => {
        collectAllNodes(child, collected);
      });
    }

    return collected;
  }

  // セクション内の全ノードを収集
  const allNodes = collectAllNodes(sectionNode);

  return {
    nodes: {
      [sectionNode.id]: {
        document: sectionData.document
      }
    },
    allNodes: allNodes,
    meta: {
      device: deviceType,
      sectionName: sectionNode.name,
      extractedAt: sectionData.extractedAt
    }
  };
}

function splitFigmaSections() {
  console.log('🔄 Figma JSONファイルをセクション別に分割中...');

  // 入力ファイルパス
  const desktopJsonPath = './output/f/sections/section/desktop/figma-data.json';
  const mobileJsonPath = './output/f/sections/section/mobile/figma-data.json';

  // 出力ディレクトリ
  const outputDir = './output/f/sections/section/sections-split';

  // ディレクトリ作成
  if (!fs.existsSync(outputDir)) {
    fs.mkdirSync(outputDir, { recursive: true });
  }

  // JSONファイル読み込み
  const desktopJson = JSON.parse(fs.readFileSync(desktopJsonPath, 'utf8'));
  const mobileJson = JSON.parse(fs.readFileSync(mobileJsonPath, 'utf8'));

  // ルート要素取得
  const desktopContents = Object.values(desktopJson.nodes)[0].document.children[0];
  const mobileContents = Object.values(mobileJson.nodes)[0].document.children[0];

  const desktopSections = desktopContents.children;
  const mobileSections = mobileContents.children;

  console.log(`📱 Desktop: ${desktopSections.length}セクション`);
  console.log(`📱 Mobile: ${mobileSections.length}セクション`);

  // マッピング情報を保存
  const mappingInfo = [];

  // 各セクションを処理
  SECTION_MAPPING.forEach((mapping, index) => {
    console.log(`\\n${index + 1}. ${mapping.displayName} を処理中...`);

    // デスクトップ版セクションを検索
    const desktopSection = findSectionByPattern(desktopSections, mapping.desktop.pattern, mapping.desktop.index);
    // モバイル版セクションを検索
    const mobileSection = findSectionByPattern(mobileSections, mapping.mobile.pattern, mapping.mobile.index);

    if (desktopSection && mobileSection) {
      console.log(`  ✅ Desktop: "${desktopSection.name}" (ID: ${desktopSection.id})`);
      console.log(`  ✅ Mobile: "${mobileSection.name}" (ID: ${mobileSection.id})`);

      // セクション専用JSONデータを抽出
      const desktopData = extractSectionData(desktopJson, desktopSection, 'desktop');
      const mobileData = extractSectionData(mobileJson, mobileSection, 'mobile');

      // ファイル保存
      const sectionDir = path.join(outputDir, mapping.name);
      if (!fs.existsSync(sectionDir)) {
        fs.mkdirSync(sectionDir, { recursive: true });
      }

      const desktopPath = path.join(sectionDir, 'desktop.json');
      const mobilePath = path.join(sectionDir, 'mobile.json');

      fs.writeFileSync(desktopPath, JSON.stringify(desktopData, null, 2));
      fs.writeFileSync(mobilePath, JSON.stringify(mobileData, null, 2));

      console.log(`  💾 保存: ${desktopPath}`);
      console.log(`  💾 保存: ${mobilePath}`);

      // マッピング情報記録
      mappingInfo.push({
        section: mapping.name,
        displayName: mapping.displayName,
        desktop: {
          id: desktopSection.id,
          name: desktopSection.name,
          position: desktopSection.absoluteBoundingBox,
          file: path.relative(outputDir, desktopPath)
        },
        mobile: {
          id: mobileSection.id,
          name: mobileSection.name,
          position: mobileSection.absoluteBoundingBox,
          file: path.relative(outputDir, mobilePath)
        }
      });

    } else {
      console.log(`  ❌ セクションが見つかりません:`);
      if (!desktopSection) {
        console.log(`     Desktop: パターン "${mapping.desktop.pattern}" のインデックス ${mapping.desktop.index}`);
      }
      if (!mobileSection) {
        console.log(`     Mobile: パターン "${mapping.mobile.pattern}" のインデックス ${mapping.mobile.index}`);
      }
    }
  });

  // マッピング情報を保存
  const mappingPath = path.join(outputDir, 'section-mapping.json');
  fs.writeFileSync(mappingPath, JSON.stringify({
    generatedAt: new Date().toISOString(),
    sections: mappingInfo,
    totalSections: mappingInfo.length
  }, null, 2));

  console.log(`\\n✨ 分割完了！`);
  console.log(`📂 出力ディレクトリ: ${outputDir}`);
  console.log(`📋 マッピング情報: ${mappingPath}`);
  console.log(`📊 処理済みセクション数: ${mappingInfo.length}/${SECTION_MAPPING.length}`);

  return mappingInfo;
}

// 実行
if (require.main === module) {
  try {
    splitFigmaSections();
  } catch (error) {
    console.error('❌ エラー:', error.message);
    console.error(error.stack);
  }
}

module.exports = { splitFigmaSections, SECTION_MAPPING };