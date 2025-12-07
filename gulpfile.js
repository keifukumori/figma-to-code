const gulp = require('gulp');
const sass = require('gulp-sass')(require('sass'));
const cleanCSS = require('gulp-clean-css');
const fileInclude = require('gulp-file-include');
const rename = require('gulp-rename');
const browserSync = require('browser-sync').create();
const fs = require('fs');
const path = require('path');

// プロジェクト一覧を取得
function getProjects() {
  const srcDir = 'src';
  if (!fs.existsSync(srcDir)) {
    return [];
  }
  return fs.readdirSync(srcDir)
    .filter(name => {
      const fullPath = path.join(srcDir, name);
      return fs.statSync(fullPath).isDirectory() && !name.startsWith('_');
    });
}

// HTMLインクルード処理（全プロジェクト）
function html() {
  const projects = getProjects();
  if (projects.length === 0) {
    console.log('No projects found in src/');
    return Promise.resolve();
  }

  const tasks = projects.map(project => {
    return gulp.src(`src/${project}/*.html`)
      .pipe(fileInclude({
        prefix: '@@',
        basepath: '@file'
      }))
      .pipe(gulp.dest(`dist/${project}`));
  });

  return Promise.all(tasks);
}

// Sass → CSS コンパイル（全プロジェクト）
function styles() {
  const projects = getProjects();
  if (projects.length === 0) {
    console.log('No projects found in src/');
    return Promise.resolve();
  }

  const tasks = projects.map(project => {
    const stylePath = `src/${project}/scss/style.scss`;
    if (!fs.existsSync(stylePath)) {
      console.log(`Skipping ${project}: style.scss not found`);
      return Promise.resolve();
    }

    return new Promise((resolve, reject) => {
      gulp.src(stylePath)
        .pipe(sass().on('error', sass.logError))
        .pipe(gulp.dest(`dist/${project}/css`))
        .pipe(cleanCSS())
        .pipe(rename({ suffix: '.min' }))
        .pipe(gulp.dest(`dist/${project}/css`))
        .on('end', resolve)
        .on('error', reject);
    });
  });

  return Promise.all(tasks);
}

// デバッグ用HTML処理（各セクションを単体HTMLとしてビルド）
// ※新構造ではpreview.htmlを直接使用するため、この関数は後方互換用
function debugHtml() {
  const projects = getProjects();
  if (projects.length === 0) {
    return Promise.resolve();
  }

  const tasks = [];

  projects.forEach(project => {
    const includesDir = `src/${project}/_includes`;
    if (!fs.existsSync(includesDir)) {
      return;
    }

    // _includes配下のセクションディレクトリを取得
    const sections = fs.readdirSync(includesDir)
      .filter(name => {
        const fullPath = path.join(includesDir, name);
        return fs.statSync(fullPath).isDirectory();
      });

    sections.forEach(section => {
      const sectionHtml = `src/${project}/_includes/${section}/index.html`;
      if (!fs.existsSync(sectionHtml)) {
        return;
      }

      // 新構造: preview.htmlが既に存在する場合はスキップ
      const previewHtml = `src/${project}/_includes/${section}/preview.html`;
      if (fs.existsSync(previewHtml)) {
        console.log(`  Skipping ${section}: preview.html already exists (use new workflow)`);
        return;
      }

      // デバッグ用の完全なHTMLを生成（後方互換）
      const task = new Promise((resolve, reject) => {
        // セクションHTMLの内容を読み込んでラップ
        let htmlContent = fs.readFileSync(sectionHtml, 'utf8');
        // アイコンパスをdebug/からの相対パスに修正
        htmlContent = htmlContent.replace(/src="icons\//g, 'src="../icons/');
        const debugHtmlContent = `<!DOCTYPE html>
<html lang="ja">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Debug: ${section}</title>
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=Noto+Sans+JP:wght@400;700&display=swap" rel="stylesheet">
  <link rel="stylesheet" href="css/${section}.css">
</head>
<body>
${htmlContent}
</body>
</html>`;

        // debugディレクトリに出力
        const debugDir = `dist/${project}/debug`;
        if (!fs.existsSync(debugDir)) {
          fs.mkdirSync(debugDir, { recursive: true });
        }

        fs.writeFileSync(`${debugDir}/${section}.html`, debugHtmlContent);
        resolve();
      });

      tasks.push(task);
    });
  });

  return Promise.all(tasks);
}

// セクション別CSS生成（プレビュー用）
// scss/_*.scss から _includes/*/style.css を自動生成
function previewStyles(done) {
  const dartSass = require('sass');
  const projects = getProjects();

  projects.forEach(project => {
    const scssDir = `src/${project}/scss`;
    const includesDir = `src/${project}/_includes`;
    if (!fs.existsSync(scssDir) || !fs.existsSync(includesDir)) {
      return;
    }

    // _で始まるパーシャルファイルを取得（_base.scss以外）
    const partials = fs.readdirSync(scssDir)
      .filter(name => name.startsWith('_') && name.endsWith('.scss') && name !== '_base.scss');

    partials.forEach(partial => {
      const sectionName = partial.replace(/^_/, '').replace(/\.scss$/, '');
      const sectionDir = `${includesDir}/${sectionName}`;

      // セクションディレクトリが存在しない場合はスキップ
      if (!fs.existsSync(sectionDir)) {
        return;
      }

      // SCSSコンテンツを直接コンパイル
      const scssContent = `@import 'base';\n@import '${sectionName}';\n`;

      try {
        const result = dartSass.compileString(scssContent, {
          loadPaths: [scssDir]
        });

        const outputPath = path.join(sectionDir, 'style.css');
        fs.writeFileSync(outputPath, result.css);
        console.log(`  Generated: ${outputPath}`);
      } catch (err) {
        console.error(`  Error compiling ${sectionName}:`, err.message);
      }
    });
  });

  done();
}

// SVGアイコンコピー（全プロジェクト）
function icons() {
  const projects = getProjects();
  if (projects.length === 0) {
    return Promise.resolve();
  }

  const tasks = projects.map(project => {
    const iconsPath = `src/${project}/icons`;
    if (!fs.existsSync(iconsPath)) {
      return Promise.resolve();
    }

    return new Promise((resolve, reject) => {
      gulp.src(`${iconsPath}/**/*.svg`, { base: iconsPath })
        .pipe(gulp.dest(`dist/${project}/icons`))
        .on('end', resolve)
        .on('error', reject);
    });
  });

  return Promise.all(tasks);
}

// 開発サーバー
function serve() {
  const projects = getProjects();
  const baseDir = projects.length > 0 ? `dist/${projects[0]}` : 'dist';

  browserSync.init({
    server: {
      baseDir: 'dist'
    },
    open: true,
    notify: false
  });

  // 全プロジェクトを監視
  gulp.watch('src/*/*.html', html);
  gulp.watch('src/*/_includes/**/*.html', html);
  gulp.watch('src/*/scss/**/*.scss', gulp.parallel(styles, previewStyles));
  gulp.watch('src/*/icons/**/*.svg', icons);

  gulp.watch('dist/**/*').on('change', browserSync.reload);
}

// ビルドタスク
const build = gulp.series(
  gulp.parallel(html, styles, icons, debugHtml, previewStyles)
);

// デフォルトタスク（開発用）
const dev = gulp.series(
  build,
  serve
);

// エクスポート
exports.html = html;
exports.styles = styles;
exports.icons = icons;
exports.debugHtml = debugHtml;
exports.previewStyles = previewStyles;
exports.build = build;
exports.default = dev;
