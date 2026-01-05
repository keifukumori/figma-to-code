#!/usr/bin/env python3
"""
Figma Structured Extractor
===========================
extracted.md を解析して、関係性を保持したまま構造化されたマークダウンファイルを生成

機能:
1. デザインシステム抽出（共通パターン検出）
2. セクション分割（Y座標ベース + 意味的グルーピング）
3. 階層構造保持
4. 関係性保持出力フォーマット

使用方法:
    python3 extract_figma_structured.py <extracted.md>
"""

import re
import sys
import os
from pathlib import Path
from datetime import datetime
from collections import defaultdict, Counter
from typing import Dict, List, Tuple, Any, Optional
import json


class ExtractedMarkdownParser:
    """extracted.mdファイルを解析するクラス"""

    def __init__(self, file_path: str):
        self.file_path = file_path
        self.sections = {}
        self.texts = []
        self.frames = []
        self.rectangles = []
        self.vectors = []
        self.lines = []
        self.ellipses = []
        self.layout_overlaps = []
        self.svg_hashes = []
        self.hierarchy = {}

    def parse(self):
        """ファイルを解析して各セクションのデータを抽出"""
        with open(self.file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # 各セクションを抽出
        self._extract_texts(content)
        self._extract_frames(content)
        self._extract_rectangles(content)
        self._extract_vectors(content)
        self._extract_lines(content)
        self._extract_ellipses(content)
        self._extract_layout_overlaps(content)
        self._extract_svg_hashes(content)
        self._extract_hierarchy(content)

    def _extract_texts(self, content: str):
        """テキスト要素を抽出"""
        # ## Texts (基本) セクションを探す
        pattern = r'## Texts \(基本\)(.*?)(?=##|$)'
        match = re.search(pattern, content, re.DOTALL)
        if not match:
            return

        section_content = match.group(1)
        lines = section_content.strip().split('\n')

        # テーブルの解析
        header_found = False
        for line in lines:
            if '|' not in line:
                continue
            if 'Characters' in line and 'Name' in line:
                header_found = True
                continue
            if not header_found or '---' in line:
                continue

            # データ行の解析
            cols = [col.strip() for col in line.split('|')[1:-1]]
            if len(cols) >= 9:
                text_data = {
                    'characters': cols[0],
                    'name': cols[1],
                    'fontSize': self._safe_float(cols[2]),
                    'fontWeight': self._safe_int(cols[3]),
                    'absoluteX': self._safe_float(cols[4]),
                    'absoluteY': self._safe_float(cols[5]),
                    'color': cols[6],
                    'lineHeight': self._safe_float(cols[7]),
                    'textAlign': cols[8],
                    'opacity': cols[9] if len(cols) > 9 else '-'
                }
                self.texts.append(text_data)

    def _extract_frames(self, content: str):
        """フレーム要素を抽出"""
        pattern = r'## Frames & Components \(基本\)(.*?)(?=##|$)'
        match = re.search(pattern, content, re.DOTALL)
        if not match:
            return

        section_content = match.group(1)
        lines = section_content.strip().split('\n')

        header_found = False
        for line in lines:
            if '|' not in line:
                continue
            if 'Name' in line and 'Type' in line:
                header_found = True
                continue
            if not header_found or '---' in line:
                continue

            cols = [col.strip() for col in line.split('|')[1:-1]]
            if len(cols) >= 8:  # 最低限のカラム数に調整
                frame_data = {
                    'name': cols[0],
                    'type': cols[1],
                    'width': self._safe_float(cols[2]),
                    'height': self._safe_float(cols[3]),
                    'absoluteX': self._safe_float(cols[4]),
                    'absoluteY': self._safe_float(cols[5]),
                    'layoutMode': cols[6] if len(cols) > 6 else None,
                    'itemSpacing': cols[7] if len(cols) > 7 else None,
                    'backgroundColor': cols[8] if len(cols) > 8 and cols[8] != 'None' else None,
                    'cornerRadius': self._safe_float(cols[9]) if len(cols) > 9 else None
                }
                self.frames.append(frame_data)

    def _extract_rectangles(self, content: str):
        """矩形要素を抽出"""
        pattern = r'## Rectangles\n\n(.*?)(?=\n## |\n\Z)'
        match = re.search(pattern, content, re.DOTALL)
        if not match:
            return

        section_content = match.group(1)
        lines = section_content.strip().split('\n')

        header_found = False
        for line in lines:
            if '|' not in line:
                continue
            if 'name' in line and 'depth' in line:
                header_found = True
                continue
            if not header_found or '---' in line:
                continue

            cols = [col.strip() for col in line.split('|')[1:-1]]
            if len(cols) >= 20:  # 最低限必要なカラム数に調整
                rect_data = {
                    'name': cols[0],
                    'depth': self._safe_int(cols[1]),
                    'parent_id': cols[2],
                    'absoluteX': self._safe_float(cols[3]),
                    'absoluteY': self._safe_float(cols[4]),
                    'width': self._safe_float(cols[5]),
                    'height': self._safe_float(cols[6]),
                    'fill': cols[7],
                    'stroke': cols[8],
                    'strokeWeight': self._safe_float(cols[9]),
                    'cornerRadius': self._safe_float(cols[10]) if len(cols) > 10 else None,  # cornerRadius追加
                    'layoutPositioning': cols[11] if len(cols) > 11 else None,
                    'scrollBehavior': cols[12] if len(cols) > 12 else None,
                    'blendMode': cols[13] if len(cols) > 13 else None,
                    'strokeAlign': cols[14] if len(cols) > 14 else None,
                    'styles': cols[15] if len(cols) > 15 else None,
                    'constraints': cols[16] if len(cols) > 16 else None,
                    'effects': cols[17] if len(cols) > 17 else None,
                    'interactions': cols[18] if len(cols) > 18 else None,
                    'parent_name': cols[19] if len(cols) > 19 else None,
                    'cornerSmoothing': cols[20] if len(cols) > 20 else None  # cornerSmoothing追加
                }

                # 画像要素（RECTANGLEでnameがimage*）の特別処理
                if rect_data.get('name', '').startswith('image '):
                    rect_data['is_image'] = True
                    rect_data['image_id'] = rect_data.get('name', '').replace('image ', '')
                else:
                    rect_data['is_image'] = False

                self.rectangles.append(rect_data)

    def _extract_vectors(self, content: str):
        """ベクター要素を抽出"""
        pattern = r'## Vectors \(Icons/Lines\)\n\n(.*?)(?=\n## |\n\Z)'
        match = re.search(pattern, content, re.DOTALL)
        if not match:
            return

        section_content = match.group(1)
        lines = section_content.strip().split('\n')

        header_found = False
        for line in lines:
            if '|' not in line:
                continue
            if 'name' in line and 'depth' in line:
                header_found = True
                continue
            if not header_found or '---' in line:
                continue

            cols = [col.strip() for col in line.split('|')[1:-1]]
            if len(cols) >= 25:  # 実際のカラム数に合わせて調整
                vector_data = {
                    'name': cols[0],
                    'depth': self._safe_int(cols[1]),
                    'parent_id': cols[2],
                    'absoluteX': self._safe_float(cols[3]),
                    'absoluteY': self._safe_float(cols[4]),
                    'width': self._safe_float(cols[5]),
                    'height': self._safe_float(cols[6]),
                    'fill': cols[7],
                    'stroke': cols[8],
                    'strokeWeight': self._safe_float(cols[9]),
                    'strokeCap': cols[10] if len(cols) > 10 else None,
                    'strokeJoin': cols[11] if len(cols) > 11 else None,
                    'layoutPositioning': cols[12] if len(cols) > 12 else None,
                    'scrollBehavior': cols[13] if len(cols) > 13 else None,
                    'blendMode': cols[14] if len(cols) > 14 else None,
                    'strokeAlign': cols[15] if len(cols) > 15 else None,
                    'styles': cols[16] if len(cols) > 16 else None,
                    'constraints': cols[17] if len(cols) > 17 else None,
                    'effects': cols[18] if len(cols) > 18 else None,
                    'isMask': cols[19] if len(cols) > 19 else None,
                    'maskType': cols[20] if len(cols) > 20 else None,
                    'interactions': cols[21] if len(cols) > 21 else None,
                    'parent_name': cols[22] if len(cols) > 22 else None,
                    'rotation': self._safe_float(cols[23]) if len(cols) > 23 else None,
                    'booleanOperation': cols[24] if len(cols) > 24 else None,
                    'fillOverrideTable': cols[25] if len(cols) > 25 else None
                }
                self.vectors.append(vector_data)

    def _extract_lines(self, content: str):
        """線要素を抽出"""
        pattern = r'## Lines\n\n(.*?)(?=\n## |\n\Z)'
        match = re.search(pattern, content, re.DOTALL)
        if not match:
            return

        section_content = match.group(1)
        lines = section_content.strip().split('\n')

        header_found = False
        for line in lines:
            if '|' not in line:
                continue
            if 'name' in line and 'depth' in line:
                header_found = True
                continue
            if not header_found or '---' in line:
                continue

            cols = [col.strip() for col in line.split('|')[1:-1]]
            if len(cols) >= 27:
                line_data = {
                    'name': cols[0],
                    'depth': self._safe_int(cols[1]),
                    'parent_id': cols[2],
                    'absoluteX': self._safe_float(cols[3]),
                    'absoluteY': self._safe_float(cols[4]),
                    'width': self._safe_float(cols[5]),
                    'height': self._safe_float(cols[6]),
                    'fill': cols[7],
                    'stroke': cols[8],
                    'strokeWeight': self._safe_float(cols[9]),
                    'layoutPositioning': cols[10],
                    'scrollBehavior': cols[11],
                    'rotation': self._safe_float(cols[12]),
                    'blendMode': cols[13],
                    'fillGeometry': cols[14],
                    'strokeAlign': cols[15],
                    'strokeGeometry': cols[16],
                    'constraints': cols[17],
                    'relativeTransform': cols[18],
                    'size': cols[19],
                    'layoutAlign': cols[20],
                    'layoutGrow': cols[21],
                    'layoutSizingHorizontal': cols[22],
                    'layoutSizingVertical': cols[23],
                    'effects': cols[24],
                    'interactions': cols[25],
                    'parent_name': cols[26]
                }
                self.lines.append(line_data)

    def _extract_ellipses(self, content: str):
        """楕円要素を抽出"""
        pattern = r'## Ellipses\n\n(.*?)(?=\n## |\n\Z)'
        match = re.search(pattern, content, re.DOTALL)
        if not match:
            return

        section_content = match.group(1)
        lines = section_content.strip().split('\n')

        header_found = False
        for line in lines:
            if '|' not in line:
                continue
            if 'name' in line and 'depth' in line:
                header_found = True
                continue
            if not header_found or '---' in line:
                continue

            cols = [col.strip() for col in line.split('|')[1:-1]]
            if len(cols) >= 23:
                ellipse_data = {
                    'name': cols[0],
                    'depth': self._safe_int(cols[1]),
                    'parent_id': cols[2],
                    'absoluteX': self._safe_float(cols[3]),
                    'absoluteY': self._safe_float(cols[4]),
                    'width': self._safe_float(cols[5]),
                    'height': self._safe_float(cols[6]),
                    'fill': cols[7],
                    'stroke': cols[8],
                    'strokeWeight': self._safe_float(cols[9]),
                    'layoutPositioning': cols[10],
                    'scrollBehavior': cols[11],
                    'blendMode': cols[12],
                    'fillGeometry': cols[13],
                    'strokeAlign': cols[14],
                    'strokeGeometry': cols[15],
                    'constraints': cols[16],
                    'relativeTransform': cols[17],
                    'size': cols[18],
                    'effects': cols[19],
                    'arcData': cols[20],
                    'interactions': cols[21],
                    'parent_name': cols[22]
                }
                self.ellipses.append(ellipse_data)

    def _extract_layout_overlaps(self, content: str):
        """Layout Overlaps セクション抽出"""
        pattern = r'## Layout Overlaps \(要素の重なり検出と推奨CSS提案\)\n\n(.*?)(?=\n## |\n\Z)'
        match = re.search(pattern, content, re.DOTALL)
        if not match:
            return

        section_content = match.group(1)
        lines = section_content.strip().split('\n')

        header_found = False
        for line in lines:
            if '|' not in line:
                continue
            if 'Parent' in line and 'Child' in line:
                header_found = True
                continue
            if not header_found or '---' in line:
                continue

            cols = [col.strip() for col in line.split('|')[1:-1]]
            if len(cols) >= 6:
                overlap_data = {
                    'parent': cols[0],
                    'parent_id': cols[1],
                    'child': cols[2],
                    'child_id': cols[3],
                    'overlap_y': self._safe_float(cols[4]),
                    'overlap_height': self._safe_float(cols[5]),
                    'css_suggestion': cols[6] if len(cols) > 6 else ''
                }
                self.layout_overlaps.append(overlap_data)

    def _extract_svg_hashes(self, content: str):
        """SVG hashes セクション抽出"""
        pattern = r'## SVG hashes \(アイコン識別用\)\n\n(.*?)(?=\n## |\n\Z)'
        match = re.search(pattern, content, re.DOTALL)
        if not match:
            return

        section_content = match.group(1)
        lines = section_content.strip().split('\n')

        header_found = False
        for line in lines:
            if '|' not in line:
                continue
            if 'Hash' in line and 'Usage Count' in line:
                header_found = True
                continue
            if not header_found or '---' in line:
                continue

            cols = [col.strip() for col in line.split('|')[1:-1]]
            if len(cols) >= 3:
                svg_data = {
                    'hash': cols[0],
                    'usage_count': self._safe_int(cols[1]),
                    'example_names': cols[2]
                }
                self.svg_hashes.append(svg_data)

    def _extract_hierarchy(self, content: str):
        """階層構造を抽出"""
        pattern = r'## 📐 階層構造（Layout Tree）\n\n(.*?)(?=\n## |\n\Z)'
        match = re.search(pattern, content, re.DOTALL)
        if not match:
            return

        section_content = match.group(1)
        lines = section_content.strip().split('\n')

        current_path = []
        for line in lines:
            if not line.strip():
                continue

            # インデントレベルを計算
            indent_level = (len(line) - len(line.lstrip())) // 2

            # 要素名を抽出 ("- element_name (TYPE)" 形式)
            element_match = re.search(r'- (.+?) \(([^)]+)\)', line)
            if element_match:
                name = element_match.group(1)
                element_type = element_match.group(2)

                # パスを調整
                current_path = current_path[:indent_level]
                current_path.append(name)

                self.hierarchy['/'.join(current_path)] = {
                    'name': name,
                    'type': element_type,
                    'level': indent_level,
                    'parent': '/'.join(current_path[:-1]) if len(current_path) > 1 else None,
                    'raw_line': line.strip()
                }

    def _safe_float(self, value: str) -> Optional[float]:
        """文字列を安全にfloatに変換"""
        try:
            if value and value != '-':
                return float(value)
        except:
            pass
        return None

    def _safe_int(self, value: str) -> Optional[int]:
        """文字列を安全にintに変換"""
        try:
            if value and value != '-':
                return int(value)
        except:
            pass
        return None


class DesignSystemExtractor:
    """デザインシステムを抽出するクラス"""

    def __init__(self, parser: ExtractedMarkdownParser):
        self.parser = parser

    def extract_typography_system(self) -> Dict:
        """タイポグラフィシステムを抽出"""
        font_combinations = defaultdict(list)

        for text in self.parser.texts:
            # フォント組み合わせのパターンを検出
            key = f"{text.get('fontSize', '')}px-{text.get('fontWeight', '')}-{text.get('textAlign', '')}"
            font_combinations[key].append(text.get('characters', ''))

        # 3回以上使用されているパターンをシステム化
        typography_system = {}
        for pattern, examples in font_combinations.items():
            if len(examples) >= 3:
                typography_system[pattern] = {
                    'usage_count': len(examples),
                    'examples': examples[:5],  # 最初の5例
                    'pattern_type': self._classify_text_pattern(examples)
                }

        return typography_system

    def extract_layout_system(self) -> Dict:
        """レイアウトシステムを抽出"""
        layout_patterns = defaultdict(list)

        for frame in self.parser.frames:
            if frame.get('layoutMode'):
                key = f"{frame.get('layoutMode', '')}-gap{frame.get('itemSpacing', '')}"
                layout_patterns[key].append(frame.get('name', ''))

        layout_system = {}
        for pattern, names in layout_patterns.items():
            if len(names) >= 2:
                layout_system[pattern] = {
                    'usage_count': len(names),
                    'examples': names[:5]
                }

        return layout_system

    def extract_color_system(self) -> Dict:
        """カラーシステムを抽出"""
        colors = defaultdict(int)

        for text in self.parser.texts:
            if text.get('color'):
                colors[text['color']] += 1

        for frame in self.parser.frames:
            if frame.get('backgroundColor') and frame['backgroundColor'] != 'None':
                colors[frame['backgroundColor']] += 1

        # 使用回数順でソート
        color_system = {}
        for color, count in sorted(colors.items(), key=lambda x: x[1], reverse=True):
            if count >= 2:  # 2回以上使用
                color_system[color] = {
                    'usage_count': count,
                    'color_type': self._classify_color(color)
                }

        return color_system

    def _classify_text_pattern(self, examples: List[str]) -> str:
        """テキストパターンを分類"""
        # 見出し、ボタン、価格などのパターンを推定
        text_samples = [ex.lower() for ex in examples[:3]]

        if any('$' in text for text in text_samples):
            return 'price'
        elif any(len(text) < 20 and text.isupper() for text in text_samples):
            return 'heading'
        elif any('/' in text for text in text_samples):
            return 'rating'
        elif any(text in ['shop now', 'view all', 'subscribe'] for text in text_samples):
            return 'button'
        else:
            return 'body'

    def _classify_color(self, color: str) -> str:
        """色を分類"""
        if 'rgb(0, 0, 0)' in color:
            return 'text-primary'
        elif 'rgb(255, 255, 255)' in color:
            return 'background-primary'
        elif '0.40' in color or '0.60' in color:
            return 'text-secondary'
        elif 'rgb(255, 51, 51)' in color:
            return 'accent-red'
        elif 'rgb(0, 111, 253)' in color:
            return 'primary-blue'
        else:
            return 'custom'


class SectionDetector:
    """セクション検出クラス"""

    def __init__(self, parser: ExtractedMarkdownParser):
        self.parser = parser

    def detect_sections_by_coordinates(self) -> List[Dict]:
        """Y座標ベースでセクションを検出"""
        # 全要素をY座標でソート
        all_elements = []

        for text in self.parser.texts:
            if text.get('absoluteY') is not None:
                all_elements.append({
                    'type': 'text',
                    'data': text,
                    'y': text['absoluteY'],
                    'content': text.get('characters', ''),
                    'size': text.get('fontSize', 16)
                })

        for frame in self.parser.frames:
            if frame.get('absoluteY') is not None:
                all_elements.append({
                    'type': 'frame',
                    'data': frame,
                    'y': frame['absoluteY'],
                    'content': frame.get('name', ''),
                    'size': frame.get('height', 0)
                })

        all_elements.sort(key=lambda x: x['y'])

        # セクション境界を検出
        sections = []
        current_section = {
            'name': 'header',
            'start_y': 0,
            'elements': [],
            'section_type': 'header'
        }

        last_y = 0
        gap_threshold = 100  # Y座標の大きなギャップでセクション区切り

        for element in all_elements:
            y = element['y']

            # 大きなギャップがあればセクション区切り
            if y - last_y > gap_threshold and current_section['elements']:
                current_section['end_y'] = last_y
                sections.append(current_section)

                # 新しいセクション開始
                current_section = {
                    'name': self._detect_section_name(element),
                    'start_y': y,
                    'elements': [],
                    'section_type': self._detect_section_type(element)
                }

            current_section['elements'].append(element)
            last_y = y

        # 最後のセクションを追加
        if current_section['elements']:
            current_section['end_y'] = last_y
            sections.append(current_section)

        return sections

    def _detect_section_name(self, element: Dict) -> str:
        """要素からセクション名を推定"""
        content = element.get('content', '').lower()

        if 'new arrivals' in content:
            return 'new_arrivals'
        elif 'top selling' in content or 'selling' in content:
            return 'top_selling'
        elif 'customers' in content:
            return 'testimonials'
        elif 'browse' in content or 'style' in content:
            return 'browse_styles'
        elif 'shop.co' in content and element.get('y', 0) > 3000:
            return 'footer'
        elif element.get('y', 0) < 200:
            return 'header'
        else:
            return f'section_{int(element.get("y", 0) // 1000)}'

    def _detect_section_type(self, element: Dict) -> str:
        """セクションタイプを推定"""
        content = element.get('content', '').lower()
        y = element.get('y', 0)

        if y < 200:
            return 'navigation'
        elif 'find clothes' in content or y < 600:
            return 'hero'
        elif 'new arrivals' in content or 'selling' in content:
            return 'product_grid'
        elif 'customers' in content:
            return 'testimonials'
        elif 'browse' in content:
            return 'category_grid'
        elif y > 3500:
            return 'footer'
        else:
            return 'content'


class StructuredOutputGenerator:
    """構造化出力生成クラス"""

    def __init__(self, parser: ExtractedMarkdownParser, design_system: Dict, sections: List[Dict]):
        self.parser = parser
        self.design_system = design_system
        self.sections = sections

    def generate_design_system_file(self) -> str:
        """デザインシステムファイルを生成"""
        lines = []
        lines.append("# Design System")
        lines.append(f"> 自動抽出されたデザインシステム")
        lines.append(f"> 生成日時: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        lines.append("")

        # タイポグラフィシステム
        lines.append("## Typography System")
        lines.append("")
        typography = self.design_system.get('typography', {})

        for pattern, data in typography.items():
            pattern_type = data.get('pattern_type', 'unknown')
            usage_count = data.get('usage_count', 0)
            examples = data.get('examples', [])

            lines.append(f"### {pattern} ({pattern_type})")
            lines.append(f"- 使用回数: {usage_count}")
            lines.append(f"- 例: {', '.join(examples[:3])}")
            lines.append("")

        # カラーシステム
        lines.append("## Color System")
        lines.append("")
        colors = self.design_system.get('colors', {})

        for color, data in colors.items():
            color_type = data.get('color_type', 'unknown')
            usage_count = data.get('usage_count', 0)

            lines.append(f"### {color}")
            lines.append(f"- タイプ: {color_type}")
            lines.append(f"- 使用回数: {usage_count}")
            lines.append("")

        # レイアウトシステム
        lines.append("## Layout System")
        lines.append("")
        layouts = self.design_system.get('layouts', {})

        for pattern, data in layouts.items():
            usage_count = data.get('usage_count', 0)
            examples = data.get('examples', [])

            lines.append(f"### {pattern}")
            lines.append(f"- 使用回数: {usage_count}")
            lines.append(f"- 使用箇所: {', '.join(examples[:3])}")
            lines.append("")

        return "\n".join(lines)

    def generate_sections_file(self) -> str:
        """セクション別ファイルを生成"""
        lines = []
        lines.append("# Structured Sections")
        lines.append(f"> 関係性を保持したセクション分割")
        lines.append(f"> 生成日時: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        lines.append(f"> 検出セクション数: {len(self.sections)}")
        lines.append("")

        for i, section in enumerate(self.sections):
            lines.append(f"## セクション{i+1}: {section['name']}")
            lines.append(f"### メタ情報")
            lines.append(f"- セクションタイプ: {section.get('section_type', 'unknown')}")
            lines.append(f"- Y座標範囲: {section.get('start_y', 0)} - {section.get('end_y', 0)}")
            lines.append(f"- 要素数: {len(section.get('elements', []))}")
            lines.append("")

            # 要素一覧
            lines.append("### 構成要素")
            elements = section.get('elements', [])

            # テキスト要素
            text_elements = [e for e in elements if e['type'] == 'text']
            if text_elements:
                lines.append("#### テキスト要素")
                lines.append("| 内容 | fontSize | fontWeight | 座標(X,Y) | 色 |")
                lines.append("|------|----------|------------|-----------|-----|")

                for elem in text_elements[:10]:  # 最初の10要素
                    data = elem['data']
                    content = str(data.get('characters', '')).replace('|', '\\|')
                    if len(content) > 30:
                        content = content[:27] + "..."

                    lines.append(f"| {content} | {data.get('fontSize', '')} | {data.get('fontWeight', '')} | ({data.get('absoluteX', '')}, {data.get('absoluteY', '')}) | {data.get('color', '')} |")

                if len(text_elements) > 10:
                    lines.append(f"> 残り{len(text_elements) - 10}要素は省略")
                lines.append("")

            # フレーム要素
            frame_elements = [e for e in elements if e['type'] == 'frame']
            if frame_elements:
                lines.append("#### レイアウトフレーム")
                lines.append("| 名前 | サイズ(W×H) | 座標(X,Y) | レイアウト | 背景色 |")
                lines.append("|------|-------------|-----------|-----------|--------|")

                for elem in frame_elements[:10]:
                    data = elem['data']
                    name = str(data.get('name', '')).replace('|', '\\|')
                    size = f"{data.get('width', '')}×{data.get('height', '')}"
                    coords = f"({data.get('absoluteX', '')}, {data.get('absoluteY', '')})"
                    layout = data.get('layoutMode', '')
                    bg = data.get('backgroundColor', '')

                    lines.append(f"| {name} | {size} | {coords} | {layout} | {bg} |")

                if len(frame_elements) > 10:
                    lines.append(f"> 残り{len(frame_elements) - 10}要素は省略")
                lines.append("")

            # セクション間の関係性
            if i > 0:
                prev_section = self.sections[i-1]
                gap = section.get('start_y', 0) - prev_section.get('end_y', 0)
                lines.append(f"### 前セクションとの関係")
                lines.append(f"- 間隔: {gap}px")
                lines.append("")

            lines.append("---")
            lines.append("")

        return "\n".join(lines)

    def generate_relationship_map(self) -> str:
        """関係性マップを生成"""
        lines = []
        lines.append("# Element Relationship Map")
        lines.append(f"> 要素間の関係性マップ")
        lines.append(f"> 生成日時: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        lines.append("")

        lines.append("## 階層構造")
        lines.append("```")
        for path, info in self.parser.hierarchy.items():
            indent = "  " * info['level']
            lines.append(f"{indent}- {info['name']} ({info['type']})")
        lines.append("```")
        lines.append("")

        # 近接要素マップ
        lines.append("## 要素近接マップ")
        lines.append("| 要素 | 座標 | 右隣要素 | 下隣要素 |")
        lines.append("|------|------|----------|----------|")

        # テキスト要素の近接関係を計算
        texts_by_y = defaultdict(list)
        for text in self.parser.texts:
            if text.get('absoluteY') is not None:
                y_group = int(text['absoluteY'] // 50) * 50  # 50px範囲でグルーピング
                texts_by_y[y_group].append(text)

        for y_group in sorted(texts_by_y.keys()):
            texts = sorted(texts_by_y[y_group], key=lambda t: t.get('absoluteX', 0))

            for i, text in enumerate(texts):
                name = str(text.get('characters', '')).replace('|', '\\|')[:20]
                coords = f"({text.get('absoluteX', '')}, {text.get('absoluteY', '')})"
                right_neighbor = texts[i+1].get('characters', '') if i+1 < len(texts) else ''

                # 下隣要素を探す
                next_y_group = y_group + 50
                down_neighbor = ''
                if next_y_group in texts_by_y:
                    # 最も近いX座標の要素を探す
                    current_x = text.get('absoluteX', 0)
                    closest_text = min(texts_by_y[next_y_group],
                                     key=lambda t: abs(t.get('absoluteX', 0) - current_x))
                    down_neighbor = closest_text.get('characters', '')[:15]

                lines.append(f"| {name} | {coords} | {right_neighbor[:15]} | {down_neighbor} |")

        lines.append("")
        return "\n".join(lines)


def main():
    """メイン実行関数"""
    if len(sys.argv) != 2:
        print("Usage: python3 extract_figma_structured.py <extracted.md>")
        sys.exit(1)

    input_file = sys.argv[1]
    if not os.path.exists(input_file):
        print(f"Error: File not found: {input_file}")
        sys.exit(1)

    print("🚀 Figma Structured Extractor 開始...")
    print(f"📄 Input: {input_file}")

    try:
        # 1. extracted.md を解析
        print("🔄 extracted.md 解析中...")
        parser = ExtractedMarkdownParser(input_file)
        parser.parse()

        print(f"✅ 解析完了")
        print(f"   テキスト: {len(parser.texts)}")
        print(f"   フレーム: {len(parser.frames)}")
        print(f"   階層要素: {len(parser.hierarchy)}")

        # 2. デザインシステム抽出
        print("🎨 デザインシステム抽出中...")
        design_extractor = DesignSystemExtractor(parser)
        design_system = {
            'typography': design_extractor.extract_typography_system(),
            'layouts': design_extractor.extract_layout_system(),
            'colors': design_extractor.extract_color_system()
        }

        # 3. セクション検出
        print("📊 セクション検出中...")
        section_detector = SectionDetector(parser)
        sections = section_detector.detect_sections_by_coordinates()

        # 4. 出力ディレクトリ作成
        input_path = Path(input_file)
        output_dir = input_path.parent / "structured_output"
        output_dir.mkdir(exist_ok=True)

        print(f"📁 出力先: {output_dir}")

        # 5. 構造化ファイル生成
        print("📝 構造化ファイル生成中...")
        generator = StructuredOutputGenerator(parser, design_system, sections)

        # デザインシステムファイル
        design_system_content = generator.generate_design_system_file()
        (output_dir / "design_system.md").write_text(design_system_content, encoding="utf-8")
        print("✅ design_system.md")

        # セクション別ファイル
        sections_content = generator.generate_sections_file()
        (output_dir / "structured_sections.md").write_text(sections_content, encoding="utf-8")
        print("✅ structured_sections.md")

        # 関係性マップ
        relationship_content = generator.generate_relationship_map()
        (output_dir / "relationship_map.md").write_text(relationship_content, encoding="utf-8")
        print("✅ relationship_map.md")

        print("\n🎉 Structured Extraction 完了!")
        print(f"   検出セクション数: {len(sections)}")
        print(f"   デザインパターン: {len(design_system['typography']) + len(design_system['layouts'])}")
        print(f"   階層要素数: {len(parser.hierarchy)}")

        # ファイルサイズ表示
        for filename in ["design_system.md", "structured_sections.md", "relationship_map.md"]:
            filepath = output_dir / filename
            if filepath.exists():
                size = filepath.stat().st_size
                print(f"     {filename}: {size:,} bytes")

    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()