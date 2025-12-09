#!/usr/bin/env python3
"""
Figma JSON Extractor
====================
大きなFigma JSONファイルからCSS生成に必要な情報を抽出し、
軽量なMarkdownファイルとして出力するスクリプト。

使用方法:
  python extract_figma.py <figma-data.json> [output.md]

出力:
  - extracted.md (デフォルト) または指定したファイル名
"""

import json
import sys
import os
from pathlib import Path


def rgb_to_css(r, g, b, a=1):
    """Figmaの0-1形式をCSS rgb()形式に変換"""
    r_int = round(r * 255)
    g_int = round(g * 255)
    b_int = round(b * 255)
    if a < 1:
        return f"rgba({r_int}, {g_int}, {b_int}, {a:.2f})"
    return f"rgb({r_int}, {g_int}, {b_int})"


def extract_color(fills):
    """fills配列から色を抽出"""
    if not fills:
        return None
    for fill in fills:
        if fill.get("visible", True) and fill.get("type") == "SOLID":
            color = fill.get("color", {})
            r = color.get("r", 0)
            g = color.get("g", 0)
            b = color.get("b", 0)
            a = fill.get("opacity", 1)
            return rgb_to_css(r, g, b, a)
        elif fill.get("visible", True) and "GRADIENT" in fill.get("type", ""):
            stops = fill.get("gradientStops", [])
            if stops:
                colors = []
                for stop in stops:
                    c = stop.get("color", {})
                    colors.append(rgb_to_css(c.get("r", 0), c.get("g", 0), c.get("b", 0)))
                return f"gradient({' → '.join(colors)})"
    return None


def extract_stroke_color(strokes):
    """strokes配列から色を抽出"""
    if not strokes:
        return None
    for stroke in strokes:
        if stroke.get("visible", True) and stroke.get("type") == "SOLID":
            color = stroke.get("color", {})
            r = color.get("r", 0)
            g = color.get("g", 0)
            b = color.get("b", 0)
            return rgb_to_css(r, g, b)
    return None


def extract_effects(effects):
    """effects配列からCSS用の効果を抽出"""
    if not effects:
        return None
    result = []
    for effect in effects:
        if not effect.get("visible", True):
            continue
        effect_type = effect.get("type", "")
        if effect_type == "DROP_SHADOW":
            color = effect.get("color", {})
            r = color.get("r", 0)
            g = color.get("g", 0)
            b = color.get("b", 0)
            a = color.get("a", 1)
            offset = effect.get("offset", {})
            x = offset.get("x", 0)
            y = offset.get("y", 0)
            radius = effect.get("radius", 0)
            spread = effect.get("spread", 0)
            result.append(f"drop-shadow({x}px {y}px {radius}px {spread}px {rgb_to_css(r, g, b, a)})")
        elif effect_type == "INNER_SHADOW":
            color = effect.get("color", {})
            r = color.get("r", 0)
            g = color.get("g", 0)
            b = color.get("b", 0)
            a = color.get("a", 1)
            offset = effect.get("offset", {})
            x = offset.get("x", 0)
            y = offset.get("y", 0)
            radius = effect.get("radius", 0)
            result.append(f"inner-shadow({x}px {y}px {radius}px {rgb_to_css(r, g, b, a)})")
        elif effect_type == "LAYER_BLUR":
            radius = effect.get("radius", 0)
            result.append(f"blur({radius}px)")
        elif effect_type == "BACKGROUND_BLUR":
            radius = effect.get("radius", 0)
            result.append(f"backdrop-blur({radius}px)")
    return ", ".join(result) if result else None


def get_font_style(node):
    """rangeAllFontNamesからフォントスタイルを抽出"""
    range_fonts = node.get("rangeAllFontNames", [])
    if range_fonts and len(range_fonts) > 0:
        first_range = range_fonts[0]
        if first_range and len(first_range) > 0:
            font_info = first_range[0]
            family = font_info.get("family", "")
            style = font_info.get("style", "")
            return family, style
    return None, None


def style_to_weight(style):
    """フォントスタイルをfontWeight数値に変換"""
    if not style:
        return None
    style_lower = style.lower()
    weight_map = {
        "thin": 100,
        "extralight": 200,
        "light": 300,
        "regular": 400,
        "medium": 500,
        "semibold": 600,
        "bold": 700,
        "extrabold": 800,
        "black": 900,
    }
    for key, value in weight_map.items():
        if key in style_lower:
            return value
    return 400  # デフォルト


def get_dimensions(node):
    """ノードのサイズと位置を取得（absoluteBoundingBoxまたは直接プロパティ）"""
    bbox = node.get("absoluteBoundingBox", {})
    return {
        "width": bbox.get("width") or node.get("width"),
        "height": bbox.get("height") or node.get("height"),
        "x": bbox.get("x") or node.get("x"),
        "y": bbox.get("y") or node.get("y"),
    }


def traverse_nodes(node, path="", results=None, warnings=None):
    """ノードを再帰的に走査して情報を抽出"""
    if results is None:
        results = {
            "texts": [],
            "frames": [],
            "rectangles": [],
            "vectors": [],
            "ellipses": [],
        }
    if warnings is None:
        warnings = []

    node_type = node.get("type", "")
    node_name = node.get("name", "Unknown")
    visible = node.get("visible", True)
    current_path = f"{path}/{node_name}" if path else node_name

    # 非表示要素はスキップ
    if not visible:
        return results, warnings

    # テキスト要素
    if node_type == "TEXT":
        font_family, font_style = get_font_style(node)
        font_weight = style_to_weight(font_style)
        dims = get_dimensions(node)

        text_info = {
            "name": node_name,
            "path": current_path,
            "characters": node.get("characters", ""),
            "fontSize": node.get("fontSize"),
            "fontWeight": font_weight,
            "fontFamily": font_family,
            "lineHeight": node.get("lineHeightPx") or dims.get("height"),
            "letterSpacing": node.get("letterSpacing"),
            "textAlign": node.get("textAlignHorizontal"),
            "color": extract_color(node.get("fills", [])),
            "opacity": node.get("opacity", 1),
            "width": dims.get("width"),
            "height": dims.get("height"),
        }

        # 警告チェック
        if text_info["fontSize"] is None:
            warnings.append(f"⚠️ fontSize未取得: {node_name} (path: {current_path})")

        results["texts"].append(text_info)

    # フレーム/コンポーネント
    elif node_type in ["FRAME", "COMPONENT", "INSTANCE", "GROUP"]:
        dims = get_dimensions(node)
        frame_info = {
            "name": node_name,
            "path": current_path,
            "type": node_type,
            "width": dims.get("width"),
            "height": dims.get("height"),
            "x": dims.get("x"),
            "y": dims.get("y"),
            "paddingTop": node.get("paddingTop"),
            "paddingRight": node.get("paddingRight"),
            "paddingBottom": node.get("paddingBottom"),
            "paddingLeft": node.get("paddingLeft"),
            "itemSpacing": node.get("itemSpacing"),
            "cornerRadius": node.get("cornerRadius"),
            "backgroundColor": extract_color(node.get("fills", [])),
            "borderColor": extract_stroke_color(node.get("strokes", [])),
            "strokeWeight": node.get("strokeWeight"),
            "layoutMode": node.get("layoutMode"),
            "opacity": node.get("opacity", 1),
            "effects": extract_effects(node.get("effects", [])),
        }
        results["frames"].append(frame_info)

    # 矩形
    elif node_type == "RECTANGLE":
        dims = get_dimensions(node)
        rect_info = {
            "name": node_name,
            "path": current_path,
            "width": dims.get("width"),
            "height": dims.get("height"),
            "cornerRadius": node.get("cornerRadius"),
            "fill": extract_color(node.get("fills", [])),
            "stroke": extract_stroke_color(node.get("strokes", [])),
            "strokeWeight": node.get("strokeWeight"),
        }
        results["rectangles"].append(rect_info)

    # ベクター/アイコン
    elif node_type == "VECTOR":
        dims = get_dimensions(node)
        vector_info = {
            "name": node_name,
            "path": current_path,
            "width": dims.get("width"),
            "height": dims.get("height"),
            "fill": extract_color(node.get("fills", [])),
            "stroke": extract_stroke_color(node.get("strokes", [])),
        }
        results["vectors"].append(vector_info)

    # 楕円/円
    elif node_type == "ELLIPSE":
        dims = get_dimensions(node)
        ellipse_info = {
            "name": node_name,
            "path": current_path,
            "width": dims.get("width"),
            "height": dims.get("height"),
            "fill": extract_color(node.get("fills", [])),
        }
        results["ellipses"].append(ellipse_info)

    # 子要素を再帰処理
    children = node.get("children", [])
    for child in children:
        traverse_nodes(child, current_path, results, warnings)

    return results, warnings


def generate_markdown(results, warnings, input_file):
    """抽出結果をMarkdown形式で出力"""
    lines = []

    # ヘッダー
    lines.append(f"# Figma Data Extract")
    lines.append(f"")
    lines.append(f"Source: `{input_file}`")
    lines.append(f"")

    # 警告セクション
    if warnings:
        lines.append("## ⚠️ Warnings")
        lines.append("")
        for w in warnings:
            lines.append(f"- {w}")
        lines.append("")

    # サマリー
    lines.append("## Summary")
    lines.append("")
    lines.append(f"| Type | Count |")
    lines.append(f"|------|-------|")
    lines.append(f"| Texts | {len(results['texts'])} |")
    lines.append(f"| Frames/Components | {len(results['frames'])} |")
    lines.append(f"| Rectangles | {len(results['rectangles'])} |")
    lines.append(f"| Vectors | {len(results['vectors'])} |")
    lines.append(f"| Ellipses | {len(results['ellipses'])} |")
    lines.append("")

    # テキスト要素
    if results["texts"]:
        lines.append("## Texts")
        lines.append("")
        lines.append("| Name | Characters | fontSize | fontWeight | lineHeight | letterSpacing | textAlign | opacity | color |")
        lines.append("|------|------------|----------|------------|------------|---------------|-----------|---------|-------|")
        for t in results["texts"]:
            chars = t["characters"][:30] + "..." if len(t["characters"]) > 30 else t["characters"]
            chars = chars.replace("|", "\\|").replace("\n", " ")
            letter_spacing = t.get('letterSpacing', '-')
            text_align = t.get('textAlign', '-')
            opacity = t.get('opacity', 1)
            opacity_str = str(opacity) if opacity != 1 else "-"
            lines.append(f"| {t['name']} | {chars} | {t['fontSize']} | {t['fontWeight']} | {t['lineHeight']} | {letter_spacing} | {text_align} | {opacity_str} | {t['color']} |")
        lines.append("")

    # フレーム/コンポーネント
    if results["frames"]:
        lines.append("## Frames & Components")
        lines.append("")
        lines.append("| Name | Type | Width | Height | Padding (T/R/B/L) | Gap | Corner | BG Color | Opacity | Effects |")
        lines.append("|------|------|-------|--------|-------------------|-----|--------|----------|---------|---------|")
        for f in results["frames"]:
            padding = f"{f['paddingTop']}/{f['paddingRight']}/{f['paddingBottom']}/{f['paddingLeft']}"
            if padding == "None/None/None/None":
                padding = "-"
            opacity = f.get('opacity', 1)
            opacity_str = str(opacity) if opacity != 1 else "-"
            effects = f.get('effects', '-') or "-"
            lines.append(f"| {f['name']} | {f['type']} | {f['width']} | {f['height']} | {padding} | {f['itemSpacing']} | {f['cornerRadius']} | {f['backgroundColor']} | {opacity_str} | {effects} |")
        lines.append("")

    # 矩形
    if results["rectangles"]:
        lines.append("## Rectangles")
        lines.append("")
        lines.append("| Name | Width | Height | Corner | Fill | Stroke |")
        lines.append("|------|-------|--------|--------|------|--------|")
        for r in results["rectangles"]:
            lines.append(f"| {r['name']} | {r['width']} | {r['height']} | {r['cornerRadius']} | {r['fill']} | {r['stroke']} |")
        lines.append("")

    # ベクター
    if results["vectors"]:
        lines.append("## Vectors (Icons)")
        lines.append("")
        lines.append("| Name | Width | Height | Fill | Stroke |")
        lines.append("|------|-------|--------|------|--------|")
        for v in results["vectors"]:
            lines.append(f"| {v['name']} | {v['width']} | {v['height']} | {v['fill']} | {v['stroke']} |")
        lines.append("")

    # 楕円
    if results["ellipses"]:
        lines.append("## Ellipses")
        lines.append("")
        lines.append("| Name | Width | Height | Fill |")
        lines.append("|------|-------|--------|------|")
        for e in results["ellipses"]:
            lines.append(f"| {e['name']} | {e['width']} | {e['height']} | {e['fill']} |")
        lines.append("")

    return "\n".join(lines)


def main():
    if len(sys.argv) < 2:
        print("Usage: python extract_figma.py <figma-data.json> [output.md]")
        sys.exit(1)

    input_file = sys.argv[1]
    output_file = sys.argv[2] if len(sys.argv) > 2 else None

    # デフォルト出力先は入力ファイルと同じディレクトリ
    if output_file is None:
        input_path = Path(input_file)
        output_file = input_path.parent / "extracted.md"

    # JSON読み込み
    print(f"Reading: {input_file}")
    with open(input_file, "r", encoding="utf-8") as f:
        data = json.load(f)

    # ルートノードを探す
    root = data
    if "document" in data:
        root = data["document"]
    elif "nodes" in data:
        # Figma API形式: nodes > {nodeId} > document
        for node_id, node_data in data["nodes"].items():
            if "document" in node_data:
                root = node_data["document"]
                break
    elif "children" in data:
        pass  # rootはそのまま

    # 抽出実行
    print("Extracting...")
    results, warnings = traverse_nodes(root)

    # Markdown生成
    markdown = generate_markdown(results, warnings, input_file)

    # 出力
    with open(output_file, "w", encoding="utf-8") as f:
        f.write(markdown)

    # 統計表示
    print(f"\n✅ Output: {output_file}")
    print(f"   Texts: {len(results['texts'])}")
    print(f"   Frames: {len(results['frames'])}")
    print(f"   Rectangles: {len(results['rectangles'])}")
    print(f"   Vectors: {len(results['vectors'])}")
    print(f"   Ellipses: {len(results['ellipses'])}")

    if warnings:
        print(f"\n⚠️ Warnings: {len(warnings)}")
        for w in warnings:
            print(f"   {w}")
    else:
        print(f"\n✅ No warnings")


if __name__ == "__main__":
    main()
