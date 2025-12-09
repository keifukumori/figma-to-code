#!/usr/bin/env node

const { chromium } = require('playwright');
const fs = require('fs');
const path = require('path');
const { PNG } = require('pngjs');

/**
 * Figmaキャプチャと生成HTMLのレイアウト比較ツール
 * 差分が大きい場合は再生成を促す
 */

class LayoutComparator {
  constructor(options = {}) {
    this.threshold = options.threshold || 0.1; // ピクセル差分の許容閾値
    this.mismatchThreshold = options.mismatchThreshold || 5; // 不一致率の許容値（%）
  }

  /**
   * 画像を読み込んでPNGオブジェクトに変換
   */
  async loadImage(imagePath) {
    const data = fs.readFileSync(imagePath);
    const png = PNG.sync.read(data);
    return png;
  }

  /**
   * PlaywrightでHTMLをスクリーンショット
   * @param {number} deviceScaleFactor - Retina対応（2 = 2x解像度）
   */
  async captureHtml(htmlPath, outputPath, viewport = { width: 375, height: 812 }, deviceScaleFactor = 2) {
    const browser = await chromium.launch();
    const context = await browser.newContext({
      viewport: viewport,
      deviceScaleFactor: deviceScaleFactor  // Retina対応
    });
    const page = await context.newPage();

    // ローカルHTMLファイルを開く
    const absolutePath = path.resolve(htmlPath);
    await page.goto(`file://${absolutePath}`);

    // レンダリング待機
    await page.waitForLoadState('networkidle');
    await page.waitForTimeout(500); // フォント読み込み待ち

    // スクリーンショット（ビューポートサイズ固定、fullPageではない）
    await page.screenshot({
      path: outputPath,
      fullPage: false  // ビューポートサイズだけキャプチャ
    });

    await browser.close();

    console.log(`📸 スクリーンショット保存: ${outputPath} (${viewport.width}x${viewport.height} @${deviceScaleFactor}x)`);
    return outputPath;
  }

  /**
   * 画像をリサイズ（シンプルなnearest neighbor）
   */
  resizeImage(srcPng, targetWidth, targetHeight) {
    const dst = new PNG({ width: targetWidth, height: targetHeight });

    const xRatio = srcPng.width / targetWidth;
    const yRatio = srcPng.height / targetHeight;

    for (let y = 0; y < targetHeight; y++) {
      for (let x = 0; x < targetWidth; x++) {
        const srcX = Math.floor(x * xRatio);
        const srcY = Math.floor(y * yRatio);

        const srcIdx = (srcY * srcPng.width + srcX) * 4;
        const dstIdx = (y * targetWidth + x) * 4;

        dst.data[dstIdx] = srcPng.data[srcIdx];         // R
        dst.data[dstIdx + 1] = srcPng.data[srcIdx + 1]; // G
        dst.data[dstIdx + 2] = srcPng.data[srcIdx + 2]; // B
        dst.data[dstIdx + 3] = srcPng.data[srcIdx + 3]; // A
      }
    }

    return dst;
  }

  /**
   * 2つの画像を比較（pixelmatchをdynamic importで読み込み）
   */
  async compareImages(image1Path, image2Path, diffOutputPath) {
    // ESM モジュールを動的にインポート
    const pixelmatch = (await import('pixelmatch')).default;

    let img1 = await this.loadImage(image1Path);
    let img2 = await this.loadImage(image2Path);

    // サイズが異なる場合はリサイズ
    const sizesDiffer = img1.width !== img2.width || img1.height !== img2.height;

    if (sizesDiffer) {
      console.log(`⚠️  画像サイズが異なります:`);
      console.log(`   Figmaキャプチャ: ${img1.width}x${img1.height}`);
      console.log(`   生成HTML: ${img2.width}x${img2.height}`);

      // Figmaキャプチャのサイズを基準にHTMLスクリーンショットをリサイズ
      // （Figmaが2xの場合でも、HTMLを2xに拡大して比較）
      const targetWidth = img1.width;
      const targetHeight = img1.height;

      console.log(`   → HTMLスクリーンショットを ${targetWidth}x${targetHeight} にリサイズ`);
      img2 = this.resizeImage(img2, targetWidth, targetHeight);
    }

    const width = img1.width;
    const height = img1.height;

    const diff = new PNG({ width, height });

    // ピクセル比較
    const mismatchedPixels = pixelmatch(
      img1.data,
      img2.data,
      diff.data,
      width,
      height,
      { threshold: this.threshold }
    );

    // 差分画像を保存
    fs.writeFileSync(diffOutputPath, PNG.sync.write(diff));

    const totalPixels = width * height;
    const mismatchPercent = (mismatchedPixels / totalPixels) * 100;

    return {
      width,
      height,
      totalPixels,
      mismatchedPixels,
      mismatchPercent: mismatchPercent.toFixed(2),
      passed: mismatchPercent <= this.mismatchThreshold
    };
  }

  /**
   * レポートを生成
   */
  generateReport(result, figmaCapturePath, htmlScreenshotPath, diffPath) {
    const status = result.passed ? '✅ PASS' : '❌ FAIL';

    console.log(`\n${'='.repeat(50)}`);
    console.log(`🎨 レイアウト比較結果: ${status}`);
    console.log(`${'='.repeat(50)}`);
    console.log(`📊 統計:`);
    console.log(`   比較サイズ: ${result.width}x${result.height}`);
    console.log(`   総ピクセル数: ${result.totalPixels.toLocaleString()}`);
    console.log(`   不一致ピクセル: ${result.mismatchedPixels.toLocaleString()}`);
    console.log(`   不一致率: ${result.mismatchPercent}%`);
    console.log(`   許容閾値: ${this.mismatchThreshold}%`);
    console.log(`\n📁 ファイル:`);
    console.log(`   Figmaキャプチャ: ${figmaCapturePath}`);
    console.log(`   生成HTML: ${htmlScreenshotPath}`);
    console.log(`   差分画像: ${diffPath}`);

    if (!result.passed) {
      console.log(`\n🔧 アクション必要:`);
      console.log(`   レイアウトの差分が大きいです。`);
      console.log(`   差分画像を確認し、HTML/CSSを修正してください。`);
      console.log(`   特に以下を確認:`);
      console.log(`   - グリッド/フレックスのカラム数`);
      console.log(`   - 要素の幅（%指定）`);
      console.log(`   - 要素の数`);
    }

    return result;
  }
}

/**
 * メイン実行関数
 */
async function compareLayout(figmaCapturePath, htmlPath, options = {}) {
  const comparator = new LayoutComparator(options);

  // 出力ディレクトリ
  const outputDir = options.outputDir || path.dirname(htmlPath);
  const htmlScreenshotPath = path.join(outputDir, 'generated-screenshot.png');
  const diffPath = path.join(outputDir, 'layout-diff.png');

  console.log(`\n🔍 レイアウト比較を開始...`);
  console.log(`   Figmaキャプチャ: ${figmaCapturePath}`);
  console.log(`   HTMLファイル: ${htmlPath}`);

  // 1. HTMLをスクリーンショット
  console.log(`\n📸 HTMLをレンダリング中...`);

  // Figmaキャプチャのサイズを取得
  const figmaImg = await comparator.loadImage(figmaCapturePath);
  console.log(`   Figmaキャプチャサイズ: ${figmaImg.width}x${figmaImg.height}`);

  // Figmaは通常2xで出力されるので、ビューポートは半分のサイズ
  // deviceScaleFactor=2 で2x解像度のスクリーンショットを撮る
  const deviceScaleFactor = 2;
  const viewport = {
    width: Math.round(figmaImg.width / deviceScaleFactor),
    height: Math.round(figmaImg.height / deviceScaleFactor)
  };
  console.log(`   HTMLビューポート: ${viewport.width}x${viewport.height} (@${deviceScaleFactor}x)`);

  await comparator.captureHtml(htmlPath, htmlScreenshotPath, viewport, deviceScaleFactor);

  // 2. 画像比較
  console.log(`\n🔬 画像を比較中...`);
  const result = await comparator.compareImages(
    figmaCapturePath,
    htmlScreenshotPath,
    diffPath
  );

  // 3. レポート生成
  comparator.generateReport(result, figmaCapturePath, htmlScreenshotPath, diffPath);

  // 4. 終了コード
  if (!result.passed) {
    console.log(`\n💡 ヒント: 不一致率が ${comparator.mismatchThreshold}% を超えています。`);
    console.log(`   --threshold オプションで許容値を調整できます。`);
  }

  return result;
}

// CLI実行
if (require.main === module) {
  const args = process.argv.slice(2);

  if (args.length < 2) {
    console.log(`
📐 レイアウト比較ツール - Figmaキャプチャ vs 生成HTML

使用方法:
  node compare-layout.js <figma-capture.png> <index.html> [options]

例:
  node compare-layout.js ./output/cart/figma-capture.png ./output/cart/index.html
  node compare-layout.js ./figma-capture.png ./index.html --threshold 10

オプション:
  --threshold <数値>  不一致率の許容値（%）デフォルト: 5
  --output <dir>      出力ディレクトリ

出力:
  - generated-screenshot.png  生成HTMLのスクリーンショット
  - layout-diff.png           差分画像（赤=不一致箇所）

終了コード:
  0 = 差分が許容範囲内
  1 = 差分が大きい（要修正）
    `);
    process.exit(1);
  }

  const figmaCapturePath = args[0];
  const htmlPath = args[1];

  // オプション解析
  const options = {};
  for (let i = 2; i < args.length; i++) {
    if (args[i] === '--threshold' && args[i + 1]) {
      options.mismatchThreshold = parseFloat(args[i + 1]);
      i++;
    } else if (args[i] === '--output' && args[i + 1]) {
      options.outputDir = args[i + 1];
      i++;
    }
  }

  compareLayout(figmaCapturePath, htmlPath, options)
    .then(result => {
      process.exit(result.passed ? 0 : 1);
    })
    .catch(err => {
      console.error('❌ エラー:', err.message);
      process.exit(1);
    });
}

module.exports = { compareLayout, LayoutComparator };
