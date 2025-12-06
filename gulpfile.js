const gulp = require('gulp');
const sass = require('gulp-sass')(require('sass'));
const cleanCSS = require('gulp-clean-css');
const fileInclude = require('gulp-file-include');
const rename = require('gulp-rename');
const browserSync = require('browser-sync').create();

// パス設定
const paths = {
  src: {
    html: 'src/*.html',
    includes: 'src/_includes/**/*.html',
    scss: 'src/scss/**/*.scss',
    icons: 'src/icons/**/*.svg'
  },
  dist: {
    root: 'dist',
    css: 'dist/css',
    icons: 'dist/icons'
  }
};

// HTMLインクルード処理
function html() {
  return gulp.src(paths.src.html)
    .pipe(fileInclude({
      prefix: '@@',
      basepath: '@file'
    }))
    .pipe(gulp.dest(paths.dist.root))
    .pipe(browserSync.stream());
}

// Sass → CSS コンパイル
function styles() {
  return gulp.src('src/scss/main.scss')
    .pipe(sass().on('error', sass.logError))
    .pipe(gulp.dest(paths.dist.css))
    .pipe(cleanCSS())
    .pipe(rename({ suffix: '.min' }))
    .pipe(gulp.dest(paths.dist.css))
    .pipe(browserSync.stream());
}

// SVGアイコンコピー
function icons() {
  return gulp.src(paths.src.icons)
    .pipe(gulp.dest(paths.dist.icons))
    .pipe(browserSync.stream());
}

// 開発サーバー
function serve() {
  browserSync.init({
    server: {
      baseDir: paths.dist.root
    },
    open: true,
    notify: false
  });

  gulp.watch(paths.src.html, html);
  gulp.watch(paths.src.includes, html);
  gulp.watch(paths.src.scss, styles);
  gulp.watch(paths.src.icons, icons);
}

// ビルドタスク
const build = gulp.series(
  gulp.parallel(html, styles, icons)
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
exports.build = build;
exports.default = dev;
